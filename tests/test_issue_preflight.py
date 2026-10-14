from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import issue_preflight as gate


class IssuePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "stories").mkdir()
        (self.root / "stories" / "US-203-qualification.md").write_text("# Test\n", encoding="utf-8")
        (self.root / "stories" / "00-conventions.md").write_text("# Normative\n", encoding="utf-8")
        self.body = (
            "- **Dépendances** : US-202, US-005\n"
            "- **Document de conventions** : \x60stories/00-conventions.md\x60\n\n"
            "---\nFichier source : [\x60stories/US-203-qualification.md\x60]"
            "(../blob/main/stories/US-203-qualification.md)\n"
        )

    def test_parse_dependencies_only_from_declared_metadata(self) -> None:
        body = "US-999 in narrative\n**Dépendances** : US-202, #12, US-202, —\n"
        self.assertEqual(gate.parse_dependencies(body), ["US-202", "#12"])

    def test_parse_existing_growth_engine_document_format(self) -> None:
        self.assertEqual(gate.parse_documents(self.body), {
            "source_spec": "stories/US-203-qualification.md",
            "conventions": "stories/00-conventions.md",
        })

    def test_spec_outside_repository_is_blocked(self) -> None:
        with self.assertRaises(gate.PreflightError):
            gate.safe_document(self.root, "../outside.md", "org/repo")

    def test_external_spec_url_is_blocked(self) -> None:
        with self.assertRaises(gate.PreflightError):
            gate.safe_document(
                self.root, "https://github.com/other/repo/blob/main/stories/a.md",
                "org/repo",
            )

    def test_resolve_linked_spec(self) -> None:
        self.assertEqual(
            gate.safe_document(self.root, "../blob/main/stories/US-203-qualification.md", "org/repo"),
            "stories/US-203-qualification.md",
        )

    def test_missing_normative_doc_is_blocker(self) -> None:
        (self.root / "stories" / "00-conventions.md").unlink()
        with patch.object(gate, "resolve_dependency", return_value={"status": "PASS"}):
            report = gate.verify_issue({"number": 12, "body": self.body}, "org/repo", self.root)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("Markdown spec missing", report["errors"][0])

    def test_verified_dependencies_and_spec(self) -> None:
        with patch.object(
            gate, "resolve_dependency",
            side_effect=lambda ref, repo, num: {"reference": ref, "status": "PASS"},
        ):
            report = gate.verify_issue({"number": 12, "body": self.body}, "org/repo", self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["dependencies"]), 2)
        self.assertEqual(report["conventions"], "stories/00-conventions.md")
        self.assertEqual(report["source_spec"], "stories/US-203-qualification.md")

    def test_open_dependency_fails_closed(self) -> None:
        def fake(*args: str):
            if args[:2] == ("issue", "list"):
                return [{"number": 11, "title": "US-202 : Title"}]
            if args[:2] == ("issue", "view"):
                return {"number": 11, "state": "OPEN"}
            self.fail(str(args))
        with patch.object(gate, "run_gh", side_effect=fake):
            with self.assertRaisesRegex(gate.PreflightError, "not closed"):
                gate.resolve_dependency("US-202", "org/repo", 12)

    def test_manually_closed_dependency_is_not_merge_evidence(self) -> None:
        with patch.object(gate, "run_gh", return_value={
            "state": "CLOSED", "closedByPullRequestsReferences": [],
        }):
            with self.assertRaisesRegex(gate.PreflightError, "no linked closing PR"):
                gate.resolve_dependency("#11", "org/repo", 12)

    def test_merged_pr_must_be_in_default_branch(self) -> None:
        def fake(*args: str):
            if args[:2] == ("issue", "view"):
                return {"state": "CLOSED", "closedByPullRequestsReferences": [{"number": 54}]}
            if args[:2] == ("repo", "view"):
                return {"defaultBranchRef": {"name": "main"}}
            if args[:2] == ("pr", "view"):
                return {
                    "mergedAt": "2026-10-14T00:00:00Z",
                    "mergeCommit": {"oid": "abc123"}, "url": "https://github.com/org/repo/pull/54",
                }
            if args[0] == "api":
                return {"status": "diverged"}
            self.fail(str(args))
        with patch.object(gate, "run_gh", side_effect=fake):
            with self.assertRaisesRegex(gate.PreflightError, "not.*verified"):
                gate.resolve_dependency("#11", "org/repo", 12)

    def test_merged_pr_in_default_branch_passes(self) -> None:
        def fake(*args: str):
            if args[:2] == ("issue", "view"):
                return {"state": "CLOSED", "closedByPullRequestsReferences": [{"number": 54}]}
            if args[:2] == ("repo", "view"):
                return {"defaultBranchRef": {"name": "main"}}
            if args[:2] == ("pr", "view"):
                return {
                    "mergedAt": "2026-10-14T00:00:00Z",
                    "mergeCommit": {"oid": "abc123"}, "url": "https://github.com/org/repo/pull/54",
                }
            if args[0] == "api":
                return {"status": "ahead"}
            self.fail(str(args))
        with patch.object(gate, "run_gh", side_effect=fake):
            result = gate.resolve_dependency("#11", "org/repo", 12)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["merge_sha"], "abc123")

    def test_never_accept_self_dependency(self) -> None:
        with self.assertRaisesRegex(gate.PreflightError, "itself"):
            gate.resolve_dependency("#12", "org/repo", 12)

    def test_issue_url_cannot_switch_repositories(self) -> None:
        with self.assertRaises(gate.PreflightError):
            gate.parse_issue_reference("https://github.com/other/repo/issues/12", "org/repo")


if __name__ == "__main__":
    unittest.main()
