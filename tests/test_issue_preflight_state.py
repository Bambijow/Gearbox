from __future__ import annotations

import unittest

from scripts import run_state


class IssuePreflightStateTests(unittest.TestCase):
    def test_blocked_preflight_prevents_auto_plan(self) -> None:
        d = {"issue_preflight": {"status": "BLOCKED"}, "plan_approval": {"required": False}}
        self.assertIn("prerequisites", run_state.plan_gate_problem(d) or "")

    def test_passed_preflight_allows_existing_nonissue_plan_policy(self) -> None:
        d = {"issue_preflight": {"status": "PASS"}, "plan_approval": {"required": False}}
        self.assertIsNone(run_state.plan_gate_problem(d))

    def test_legacy_runs_without_preflight_keep_old_behavior(self) -> None:
        d = {"plan_approval": {"required": False}}
        self.assertIsNone(run_state.plan_gate_problem(d))


if __name__ == "__main__":
    unittest.main()
