"""Deterministic integration/regression tests; no models, network or product writes."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import evidence
import evidence_deps
import frontier_scheduler as scheduler
import gate_result
import precompute
import quality_plan


def task(name, path, **kwargs):
    return {"id": name, "status": "READY", "owned_paths": [path], "risk": "low", **kwargs}


def selected(plan):
    return [member for unit in plan["dispatch_units"]
            for member in (unit.get("members") or [unit["id"]])]


class PrecomputeTests(unittest.TestCase):
    def test_rejects_path_traversal_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            for name in ("../../app", "/tmp/app", ".", ".."):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    precompute.precompute({"context_descriptors": [{"id": name, "data": {}}]}, Path(td))
            self.assertEqual(list(Path(td).iterdir()), [])


class SchedulerTests(unittest.TestCase):
    def test_same_wave_reserves_ownership(self):
        tasks = [task("A", "src/shared"), task("B", "src/shared/x.ts"), task("C", "src/free.ts")]
        result = scheduler.plan({"max_parallel_workers": 3, "tasks": tasks})
        self.assertEqual(selected(result), ["A", "C"])
        self.assertTrue(any(item["id"] == "B" for item in result["waiting"]))

    def test_batch_does_not_stop_remaining_dispatch(self):
        tasks = [task("A", "a", batch_key="rename"), task("B", "b", batch_key="rename"), task("C", "c")]
        result = scheduler.plan({"max_parallel_workers": 2, "tasks": tasks})
        self.assertEqual(len(result["dispatch_units"]), 2)
        self.assertEqual(selected(result), ["A", "B", "C"])

    def test_batch_respects_previous_unit_and_reserves_all_members(self):
        tasks = [task("A", "shared"), task("B", "shared/b", batch_key="rename"),
                 task("C", "c", batch_key="rename"), task("D", "d", batch_key="rename"), task("E", "c/e")]
        result = scheduler.plan({"max_parallel_workers": 4, "tasks": tasks})
        self.assertEqual(selected(result), ["A", "C", "D"])

    def test_paths_and_repository_root(self):
        for a, b in ((".", "src/a"), ("src/../src/a", "src/a"), ("src/**", "src/a"),
                     ("src\\a", "src/a")):
            with self.subTest(a=a, b=b):
                self.assertTrue(scheduler.conflicts([a], [b]))
        self.assertFalse(scheduler.conflicts(["src/a"], ["src/ab"]))

    def test_selection_is_input_order_independent_and_never_overlaps(self):
        tasks = [task("A", "a", batch_key="x"), task("B", "a/b", batch_key="x"),
                 task("C", "c", batch_key="x"), task("D", "d")]
        expected = None
        for ordering in itertools.permutations(tasks):
            result = scheduler.plan({"max_parallel_workers": 3, "tasks": list(ordering)})
            ids = selected(result)
            if expected is None:
                expected = ids
            self.assertEqual(ids, expected)
            self.assertEqual(len(ids), len(set(ids)))
            paths = {t["id"]: t["owned_paths"] for t in tasks}
            for x, y in itertools.combinations(ids, 2):
                self.assertFalse(scheduler.conflicts(paths[x], paths[y]))


class EvidenceTests(unittest.TestCase):
    def test_status_and_process_exit_must_agree(self):
        for item in ({"status": "FAIL", "exit_code": 0}, {"status": "BLOCKED", "exit_code": 0},
                     {"status": "PASS", "exit_code": 1}, {"status": "PASS", "exit_code": False},
                     {"status": "UNKNOWN", "exit_code": 0}, {}, {"status": "", "exit_code": 0}):
            with self.subTest(item=item):
                self.assertFalse(evidence.passing(item))
        for item in ({"status": "PASS", "exit_code": 0}, {"status": "PASS"},
                     {"status": "success"}, {"exit_code": 0}):
            with self.subTest(item=item):
                self.assertTrue(evidence.passing(item))

    def test_failed_evidence_is_not_reused(self):
        ledger = {"items": [{"kind": "test", "sha": "abc", "status": "FAIL", "exit_code": 0}]}
        self.assertFalse(evidence.reuse(ledger, "test", "abc", None, None, None)["reusable"])

    def test_missing_identity_cannot_match_missing_identity(self):
        ledger = {"items": [{"kind": "test", "status": "PASS"}]}
        self.assertFalse(evidence.reuse(ledger, "test", None, None, None, None)["reusable"])

    def test_empty_scope_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(SystemExit):
                evidence.scope_fingerprint(Path(td), [], {})

    def test_scoped_hash_cannot_follow_directory_symlink_outside_repo(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            root.mkdir()
            (root / "src").mkdir()
            outside = Path(td) / "outside.txt"
            outside.write_text("not a repo dependency")
            (root / "src" / "link.txt").symlink_to(outside)
            with self.assertRaises(SystemExit):
                evidence.scope_fingerprint(root, ["src"], {})


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def closure(self, entry="src/Page.tsx", depth=8, extras=None):
        return evidence_deps.dependency_closure(self.root, [entry], extras or [], depth)

    def test_unresolved_alias_forces_exact_sha(self):
        self.write("src/Page.tsx", 'import {x} from "@/tokens";')
        self.write("src/tokens.ts", "export const x=1;")
        report = self.closure()
        self.assertFalse(report["complete"])
        self.assertTrue(report["unresolved_imports"])
        self.assertEqual(report["reuse_basis"], "exact_sha")

    def test_relative_closure_is_complete(self):
        self.write("src/Page.tsx", 'import {x} from "./tokens";')
        self.write("src/tokens.ts", "export const x=1;")
        report = self.closure()
        self.assertTrue(report["complete"])
        self.assertEqual(set(report["dependencies"]), {"src/Page.tsx", "src/tokens.ts"})

    def test_depth_limit_is_explicit(self):
        self.write("src/Page.tsx", 'import "./a";')
        self.write("src/a.ts", 'import "./b";')
        self.write("src/b.ts", "export const b=1;")
        report = self.closure(depth=1)
        self.assertFalse(report["complete"])
        self.assertTrue(report["depth_limit_hit"])

    def test_missing_relative_dynamic_and_unsupported_inputs_are_not_complete(self):
        for source in ('import "./missing";', 'const x = import(name);', 'require(name);'):
            self.write("src/Page.tsx", source)
            with self.subTest(source=source):
                self.assertFalse(self.closure()["complete"])
        self.write("scene.gd", 'extends Node\n')
        self.assertFalse(self.closure(entry="scene.gd")["complete"])

    def test_missing_extra_is_not_silently_dropped(self):
        self.write("src/Page.tsx", "export const x=1;")
        self.assertFalse(self.closure(extras=["tokens.json"])["complete"])

    def test_python_from_package_import_submodule(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/util.py", "X=1")
        self.write("pkg/main.py", "from . import util")
        report = self.closure(entry="pkg/main.py")
        self.assertIn("pkg/util.py", report["dependencies"])
        self.assertIn("pkg/__init__.py", report["dependencies"])

    def test_cli_fingerprint_refuses_scope_reuse_when_discovery_is_incomplete(self):
        self.write("src/Page.tsx", 'import "@/tokens";')
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/evidence.py"), "fingerprint",
                               "--repo-root", str(self.root), "--entry", "src/Page.tsx"],
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertIsNone(result["scope_fingerprint"])
        self.assertEqual(result["reuse_basis"], "exact_sha")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plan = quality_plan.compile_plan("a11y-audit", "standard", [], [], [], {},
                                             run_id="r1", scope="checkout", input_fingerprint="sha:abc")
        self.results = []
        for gate in self.plan["gates"]:
            if gate["status"] != "REQUIRED":
                continue
            proof = []
            for kind in gate["required_evidence_kinds"] or ["other"]:
                path = self.root / f'{gate["gate"]}-{kind}.json'
                path.write_text('{"checked":true}')
                proof.append({"kind": kind, "path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            self.results.append({"schema_version": 2, "gate": gate["gate"], "status": "PASS", "run_id": "r1",
                                 "quality_plan_id": self.plan["quality_plan_id"], "scope": "checkout",
                                 "input_fingerprint": "sha:abc", "findings": [], "evidence": proof})

    def aggregate(self, results=None):
        return gate_result.aggregate(self.plan, self.results if results is None else results, artifact_root=self.root)

    def test_compiled_plan_accepts_current_verified_proof(self):
        self.assertEqual(self.aggregate()["status"], "PASS")

    def test_binding_mismatches_are_blocked(self):
        for key in ("run_id", "scope", "input_fingerprint", "quality_plan_id"):
            changed = copy.deepcopy(self.results)
            changed[0][key] = "stale"
            with self.subTest(key=key):
                self.assertEqual(self.aggregate(changed)["status"], "BLOCKED")

    def test_duplicate_results_never_last_write_win(self):
        for order in (self.results + self.results, list(reversed(self.results + self.results))):
            self.assertEqual(self.aggregate(order)["status"], "BLOCKED")

    def test_empty_or_wrong_proof_kind_is_blocked(self):
        for proof in ([], [{**self.results[0]["evidence"][0], "kind": "other"}]):
            changed = copy.deepcopy(self.results)
            changed[0]["evidence"] = proof
            self.assertEqual(self.aggregate(changed)["status"], "BLOCKED")

    def test_mutated_or_missing_artifact_is_blocked(self):
        path = self.root / self.results[0]["evidence"][0]["path"]
        path.write_text("changed after review")
        self.assertEqual(self.aggregate()["status"], "BLOCKED")
        path.unlink()
        self.assertEqual(self.aggregate()["status"], "BLOCKED")

    def test_proof_path_cannot_escape_run(self):
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / "proof.json"
            path.write_text('{"checked":true}')
            changed = copy.deepcopy(self.results)
            changed[0]["evidence"][0]["path"] = str(path)
            self.assertEqual(self.aggregate(changed)["status"], "BLOCKED")

    def test_legacy_and_provisional_results_fail_closed(self):
        legacy = {"schema_version": 1, "gate": "A11Y_GATE", "status": "PASS", "scope": "unrelated",
                  "input_fingerprint": "stale", "findings": [], "evidence": []}
        self.assertEqual(self.aggregate([legacy])["status"], "BLOCKED")
        self.plan = quality_plan.compile_plan("a11y-audit", "standard", [], [], [], {})
        self.assertEqual(self.aggregate()["status"], "BLOCKED")

    def test_invalid_types_are_reported_without_crashing(self):
        for malformed in (None, [], "PASS", {"status": []}, {"schema_version": True}):
            with self.subTest(value=malformed):
                self.assertTrue(gate_result.validate(malformed))
                self.assertEqual(self.aggregate([malformed])["status"], "BLOCKED")

    def test_cli_returns_nonzero_for_blocked(self):
        plan_path = self.root / "quality-plan.json"
        plan_path.write_text(json.dumps(self.plan))
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/gate_result.py"), "aggregate", "--plan", str(plan_path)],
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 6, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "BLOCKED")

    def test_required_gate_cannot_be_marked_not_applicable(self):
        changed = copy.deepcopy(self.results)
        changed[0]["status"] = "NOT_APPLICABLE"
        self.assertEqual(self.aggregate(changed)["status"], "BLOCKED")

    def test_changed_plan_cannot_keep_old_identity(self):
        self.plan["scope"] = "other-page"
        result = self.aggregate()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("quality_plan_id" in message for message in result["plan_errors"]))

    def test_cli_pass_roundtrip(self):
        plan_path = self.root / "quality-plan.json"
        plan_path.write_text(json.dumps(self.plan))
        command = [sys.executable, str(ROOT / "scripts/gate_result.py"), "aggregate", "--plan", str(plan_path)]
        for i, result in enumerate(self.results):
            path = self.root / f"result-{i}.json"
            path.write_text(json.dumps(result))
            command.extend(["--result", str(path)])
        proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "PASS")

    def test_precompute_preserves_binding_and_never_dispatches(self):
        result = precompute.precompute({"task_kind": "a11y-audit", "run_id": "r1", "scope": "checkout",
                                        "input_fingerprint": "sha:abc"}, self.root)
        self.assertEqual(result["quality_plan"]["run_id"], "r1")
        self.assertEqual(result["quality_plan"]["input_fingerprint"], "sha:abc")
        self.assertEqual(result["worker_dispatches"], 0)
        self.assertEqual(result["model_calls"], 0)


class InspectTests(unittest.TestCase):
    def test_read_only_inspection_preserves_run_and_lock(self):
        from inspect_run import inspect_run
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = {"run_id": "r", "status": "AWAITING_APPROVAL", "phase": "PLAN",
                     "plan_approval": {"required": True, "status": "PENDING"},
                     "blocker": {"code": "PLAN_APPROVAL_REQUIRED"}}
            (root / "state.json").write_text(json.dumps(state))
            (root / ".lock").write_text('{"pid":123}')
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()}
            report = inspect_run(root, root)
            after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()}
            self.assertEqual(before, after)
            self.assertTrue(report["read_only"])
            self.assertTrue(report["approval"]["problem"])
            self.assertIsNone(report["usage"]["reported_cost_usd"])

    def test_missing_run_is_not_created(self):
        from inspect_run import inspect_run
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing"
            with self.assertRaises(ValueError):
                inspect_run(missing, Path(td))
            self.assertFalse(missing.exists())

    def test_changed_approved_plan_is_explained(self):
        from inspect_run import inspect_run
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = root / "plan.md"
            plan.write_text("new content")
            (root / "state.json").write_text(json.dumps({"plan_approval": {"required": True, "status": "APPROVED",
                                                   "plan_resolved": str(plan), "approved_sha256": "old"}}))
            self.assertIn("changed", inspect_run(root, root)["approval"]["problem"])


if __name__ == "__main__":
    unittest.main()
