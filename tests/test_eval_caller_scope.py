"""Regression checks for caller-shaped scope evaluation."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "eval_contract.py"


class CallerScopeEvalTests(unittest.TestCase):
    def check(self, changed, forbidden, include_manifest=True):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "state.json").write_text(json.dumps({"status": "PASS"}))
            if include_manifest:
                (root / "changed_paths.json").write_text(json.dumps({"changed_paths": changed}))
            scenario = root / "scenario.json"
            scenario.write_text(json.dumps({
                "name": "scope",
                "allowed_final_statuses": ["PASS"],
                "forbidden_changed_paths": forbidden,
            }))
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(scenario), str(root)],
                text=True, capture_output=True, check=False,
            )

    def test_unrelated_edit_fails_even_with_pass_status(self):
        result = self.check(["src/unrelated/fix.py"], ["src/unrelated/**"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("out-of-scope change", result.stdout)

    def test_protected_test_change_fails(self):
        result = self.check(["tests/protected/proof.py"], ["tests/protected/**"])
        self.assertEqual(result.returncode, 1)

    def test_expected_scope_passes(self):
        result = self.check(["src/feature/fix.py"], ["src/unrelated/**"])
        self.assertEqual(result.returncode, 0)

    def test_missing_manifest_fails_closed(self):
        result = self.check([], ["src/unrelated/**"], include_manifest=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing changed-path manifest", result.stdout)


if __name__ == "__main__":
    unittest.main()
