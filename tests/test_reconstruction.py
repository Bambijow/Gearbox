"""No REA install, models, network or target execution: contract boundary tests."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import reconstruction
import orchestrator_guard


def fixture(root):
    path = root / "reference.json"
    path.write_text('{"input_ms":100,"height":2.5}', encoding="utf-8")
    return {
        "schema_version": 1, "question": "Recover buffered jump for a new engine", "scope": "buffered jump",
        "source": {"id": "old-game", "kind": "behavior", "version": "retained-build-1",
                   "fingerprint": "sha256:authority-and-config", "availability": "runnable"},
        "target": {"project": "new-game", "revision": "sha:destination"}, "limitations": ["one captured input class"],
        "evidence": [{"id": "E1", "kind": "runtime", "path": path.name,
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "source_fingerprint": "sha256:authority-and-config", "coverage": "bounded", "limitations": []}],
        "claims": [{"id": "C1", "statement": "100ms input buffer permits this recorded jump",
                    "material": True, "status": "observed", "evidence_ids": ["E1"], "limitations": ["captured case only"]}],
        "scenarios": [{"id": "S1", "claim_ids": ["C1"], "setup": "fixed timestep and reset character",
                       "actions": "press jump 100ms before landing", "expected": "jump reaches 2.5m",
                       "oracle": "retained reference capture, not candidate implementation",
                       "reference_evidence_ids": ["E1"], "normalizations": [],
                       "comparison": "height within independently selected measurement tolerance; time in milliseconds"}],
        "decisions": [{"id": "D1", "claim_id": "C1", "disposition": "adapt", "reason": "new engine units",
                       "target_behavior": "preserve input buffer duration and convert world units", "scenario_ids": ["S1"]}],
        "unknowns": []}


class ReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = fixture(self.root)

    def inspect(self):
        return reconstruction.inspect_contract(self.data, self.root)

    def test_ready_never_authorizes_implementation_or_equivalence(self):
        result = self.inspect()
        self.assertEqual(result["status"], "READY_FOR_SHAPING")
        self.assertFalse(result["implementation_authorized"])
        self.assertFalse(result["runtime_equivalence_proven"])

    def test_missing_source_is_supported_as_artifact_analysis(self):
        self.data["source"].update(kind="binary", availability="artifact-only")
        self.data["evidence"][0]["kind"] = "static-analysis"
        self.assertEqual(self.inspect()["status"], "READY_FOR_SHAPING")
        self.assertFalse(self.inspect()["runtime_equivalence_proven"])

    def test_recordings_cannot_establish_runtime_equivalence(self):
        self.data["source"]["availability"] = "recordings-only"
        self.assertEqual(self.inspect()["status"], "PARTIAL")

    def test_inference_does_not_become_observation_by_hashing_it(self):
        self.data["claims"][0]["status"] = "inferred"
        self.assertEqual(self.inspect()["status"], "PARTIAL")

    def test_missing_decision_for_target_is_partial(self):
        self.data["decisions"] = []
        self.assertEqual(self.inspect()["status"], "PARTIAL")

    def test_recovery_without_target_does_not_require_transfer_decisions(self):
        self.data.pop("target")
        self.data["decisions"] = []
        self.assertEqual(self.inspect()["status"], "READY_FOR_SHAPING")

    def test_deferred_material_decision_is_partial(self):
        self.data["decisions"][0]["disposition"] = "defer"
        self.assertEqual(self.inspect()["status"], "PARTIAL")

    def test_adaptation_requires_an_explicit_target_rule(self):
        self.data["decisions"][0].pop("target_behavior")
        self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_blocking_unknown_is_not_hidden_in_a_valid_bundle(self):
        self.data["unknowns"] = [{"id": "U1", "question": "What happens during pause?", "blocking": True, "claim_ids": ["C1"]}]
        self.assertEqual(self.inspect()["status"], "PARTIAL")

    def test_partial_coverage_does_not_become_complete(self):
        self.data["evidence"][0]["coverage"] = "partial"
        self.assertEqual(self.inspect()["status"], "PARTIAL")

    def test_changed_evidence_is_blocked(self):
        (self.root / "reference.json").write_text("different")
        self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_changed_source_identity_is_blocked(self):
        self.data["source"]["fingerprint"] = "new-reference"
        self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_missing_file_is_blocked(self):
        (self.root / "reference.json").unlink()
        self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_symlink_escape_and_absolute_paths_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            outside = Path(td) / "reference.json"
            outside.write_text("outside")
            (self.root / "link").symlink_to(outside)
            for path in ("link", str(self.root / "reference.json")):
                with self.subTest(path=path):
                    self.data["evidence"][0]["path"] = path
                    self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_duplicate_ids_are_blocked(self):
        for key in ("evidence", "claims", "scenarios", "decisions"):
            with self.subTest(key=key):
                self.data = fixture(self.root)
                self.data[key].append(copy.deepcopy(self.data[key][0]))
                self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_dangling_references_are_blocked(self):
        for key, field in (("claims", "evidence_ids"), ("scenarios", "claim_ids"), ("decisions", "scenario_ids")):
            with self.subTest(key=key):
                self.data = fixture(self.root)
                self.data[key][0][field] = ["missing"]
                self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_malformed_top_level_and_enums_fail_closed(self):
        for data in (None, [], {}, {"schema_version": True}):
            self.assertEqual(reconstruction.inspect_contract(data, self.root)["status"], "BLOCKED")
        for value in (None, [], {}, 2, False):
            for key in ("kind", "availability"):
                self.data = fixture(self.root)
                self.data["source"][key] = value
                self.assertEqual(self.inspect()["status"], "BLOCKED")
            for collection, key in (("claims", "status"), ("decisions", "disposition"), ("scenarios", "claim_ids")):
                self.data = fixture(self.root)
                self.data[collection][0][key] = value
                self.assertEqual(self.inspect()["status"], "BLOCKED")

    def test_cli_is_read_only_even_with_command_like_content(self):
        sentinel = self.root / "must-not-exist"
        self.data["scenarios"][0]["actions"] = f"touch {sentinel}"
        contract = self.root / "contract.json"
        contract.write_text(json.dumps(self.data))
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/reconstruction.py"), "--input", str(contract)],
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(sentinel.exists())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        self.assertEqual(json.loads(proc.stdout)["contract_sha256"], hashlib.sha256(contract.read_bytes()).hexdigest())

    def test_active_reverse_guard_denies_product_write(self):
        event = {"session_id": "reverse-regression", "cwd": str(self.root), "command_name": "gearbox:reverse"}
        command = [sys.executable, str(ROOT / "scripts/orchestrator_guard.py")]
        def invoke(action, payload):
            return subprocess.run(command + [action], input=json.dumps(payload), capture_output=True,
                                  text=True, timeout=10)
        try:
            self.assertEqual(invoke("activate", event).returncode, 0)
            result = invoke("check", {**event, "tool_name": "Write", "tool_input": {"file_path": "src/game.py"}})
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        finally:
            invoke("deactivate", event)

    def test_reverse_uses_guard_and_only_read_only_inspector_is_added(self):
        self.assertIn("reverse", orchestrator_guard.GUARDED_COMMANDS)
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text())
        groups = hooks["hooks"]["UserPromptExpansion"]
        for suffix in (" activate", " --hook"):
            self.assertTrue(any(re.fullmatch(group["matcher"], "gearbox:reverse") and
                any(hook["command"].endswith(suffix) for hook in group["hooks"]) for group in groups))
        self.assertTrue(orchestrator_guard._bash_allowed("python3 /plugin/scripts/reconstruction.py --input x")[0])
        self.assertFalse(orchestrator_guard._bash_allowed("rea capture-process scenario.json")[0])


if __name__ == "__main__":
    unittest.main()
