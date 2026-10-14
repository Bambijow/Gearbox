"""Regressions for coverage, required context and absence of final-review evidence."""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import context_compiler
import coverage_matrix
import final_review_router
import precompute


class ContextTests(unittest.TestCase):
    def packet(self):
        return {"role": "worker", "outcome": "port feature", "spec_slice": "R1", "task": "implement R1",
                "required_capabilities": [], "ownership": ["src/feature"], "verify": ["test R1"],
                "output_contract": "diff and evidence"}

    def test_missing_essentials_are_rejected(self):
        for key in context_compiler.HARD_KEYS:
            data = self.packet()
            del data[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                context_compiler.compile_packet(data, 2048)
        with self.assertRaises(ValueError):
            context_compiler.compile_packet({}, 2048)

    def test_invalid_capabilities_and_budget_are_rejected(self):
        for value in (None, "[]", [False], [""]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                context_compiler.compile_packet({**self.packet(), "required_capabilities": value}, 2048)
        for value in (0, -1, True, "2000"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                context_compiler.compile_packet(self.packet(), value)

    def test_investigation_does_not_require_an_invented_spec(self):
        data = self.packet()
        data.pop("spec_slice")
        data["packet_kind"] = "investigation"
        _, manifest = context_compiler.compile_packet(data, 2048)
        self.assertNotIn("spec_slice", manifest["hard_keys"])

    def test_critical_context_survives_compression(self):
        data = self.packet()
        data["critical_pointers"] = ["contract.json#C1"]
        data["critical_dependencies"] = ["authority fingerprint must match"]
        data["pointers"] = [f"optional/{i}" for i in range(100)]
        packet, manifest = context_compiler.compile_packet(data, 1300)
        self.assertIn("contract.json#C1", packet)
        self.assertIn("authority fingerprint must match", packet)
        self.assertTrue(manifest["compression"]["compressed"])

    def test_precompute_validates_all_contexts_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                precompute.precompute({"context_descriptors": [{"id": "good", "data": self.packet()},
                                                                  {"id": "bad", "data": {}}]}, Path(td))
            self.assertEqual(list(Path(td).iterdir()), [])


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "proof.txt").write_text("test passed")
        binding = {"run_id": "r1", "scope": "feature", "input_fingerprint": "sha:current"}
        self.data = {"schema_version": 2, **binding,
                     "requirements": [{"id": "R1", "required_kinds": ["test"], "proof_ids": ["T1"]}],
                     "proofs": [{"id": "T1", "kind": "test", "status": "PASS", **binding,
                                 "pointer": "proof.txt", "sha256": hashlib.sha256((self.root / "proof.txt").read_bytes()).hexdigest()}]}

    def matrix(self):
        return coverage_matrix.compile_matrix(self.data, self.root)

    def test_valid_bound_proof_covers_requirement(self):
        self.assertEqual(self.matrix()["status"], "COMPLETE")

    def test_pending_proof_without_required_kinds_never_covers(self):
        self.data["proofs"][0]["status"] = "PENDING"
        self.data["requirements"][0].pop("required_kinds")
        self.assertEqual(self.matrix()["status"], "BLOCKED")

    def test_pending_proof_with_required_kinds_is_a_gap(self):
        self.data["proofs"][0]["status"] = "PENDING"
        self.assertEqual(self.matrix()["status"], "GAPS")

    def test_missing_pointer_target_is_blocked(self):
        self.data["proofs"][0]["pointer"] = "nonexistent"
        self.assertEqual(self.matrix()["status"], "BLOCKED")

    def test_content_change_is_blocked(self):
        (self.root / "proof.txt").write_text("changed")
        self.assertEqual(self.matrix()["status"], "BLOCKED")

    def test_stale_or_missing_identity_is_blocked(self):
        for key in coverage_matrix.BINDING:
            original = self.data["proofs"][0][key]
            self.data["proofs"][0][key] = "other"
            self.assertEqual(self.matrix()["status"], "BLOCKED")
            self.data["proofs"][0][key] = original
        self.data.pop("run_id")
        self.assertEqual(self.matrix()["status"], "BLOCKED")

    def test_failed_exit_or_unknown_status_never_passes(self):
        for value in (False, 1, "0"):
            self.data["proofs"][0]["exit_code"] = value
            self.assertEqual(self.matrix()["status"], "BLOCKED")
        self.data["proofs"][0].pop("exit_code")
        self.data["proofs"][0]["status"] = "looks good"
        self.assertEqual(self.matrix()["status"], "BLOCKED")

    def test_duplicate_ids_are_not_last_write_wins(self):
        self.data["proofs"].append(copy.deepcopy(self.data["proofs"][0]))
        self.assertEqual(self.matrix()["status"], "BLOCKED")

    def test_dangling_extra_proof_does_not_disappear(self):
        self.data["requirements"][0]["proof_ids"].append("missing")
        self.assertEqual(self.matrix()["status"], "GAPS")

    def test_failure_modes_are_part_of_completeness(self):
        self.data["failure_modes"] = ["repeated input"]
        self.assertEqual(self.matrix()["status"], "GAPS")
        self.data["proofs"][0]["covers_failure_mode"] = "repeated input"
        self.assertEqual(self.matrix()["status"], "COMPLETE")

    def test_empty_input_and_legacy_are_not_proof(self):
        self.assertEqual(coverage_matrix.compile_matrix({})["status"], "BLOCKED")
        self.data["schema_version"] = 1
        self.assertEqual(self.matrix()["status"], "BLOCKED")

    def test_explicit_non_applicability_is_supported(self):
        self.data["requirements"] = []
        self.data["proofs"] = []
        self.data["not_applicable_reason"] = "No product requirement changed in this metadata-only run"
        self.assertEqual(self.matrix()["status"], "COMPLETE")


class ReviewTests(unittest.TestCase):
    def route(self, extra):
        args = final_review_router.parser().parse_args([
            "--risk", "low", "--failure-visibility", "loud-local", "--task-review-gates", "passed", *extra])
        return final_review_router.route(args)

    def test_missing_evidence_cannot_select_lite(self):
        with self.assertRaises(ValueError):
            self.route([])

    def test_explicit_legacy_is_at_least_focused(self):
        self.assertEqual(self.route(["--legacy-incomplete-evidence"]).mode, "focused")

    def test_actual_complete_evidence_keeps_lite_route(self):
        self.assertEqual(self.route(["--coverage-status", "complete", "--quality-aggregate", "pass"]).mode, "lite")

    def test_non_applicability_needs_a_reason(self):
        flags = ["--coverage-status", "not-applicable", "--quality-aggregate", "not-applicable"]
        with self.assertRaises(ValueError):
            self.route(flags)
        self.assertEqual(self.route(flags + ["--evidence-not-applicable-reason", "metadata only"]).mode, "lite")


if __name__ == "__main__":
    unittest.main()
