from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import autopilot as ap


def issue(n, state="OPEN", labels=("autopilot",), body=""):
    return {"number": n, "title": f"Issue {n}", "state": state, "labels": [{"name": l} for l in labels], "body": body}


def pr(n, closes=(), labels=()):
    return {"number": n, "labels": [{"name": l} for l in labels], "closingIssuesReferences": [{"number": c} for c in closes]}


class FakeGitHub:
    """Just enough of gh/git/claude for the autopilot loop; `claude` opens a PR closing the issue unless told not to."""

    def __init__(self, issues, prs=(), checks=("pass",), files=("src/a.ts",), child_opens_pr=True):
        self.issues, self.prs = list(issues), list(prs)
        self.checks, self.files, self.child_opens_pr = list(checks), list(files), child_opens_pr
        self.calls: list[list[str]] = []
        self.next_pr = 100

    def __call__(self, args, cwd, timeout=None):
        self.calls.append(list(args))
        if args[0] == "claude":
            n = int(args[2].split()[1]) if args[2].startswith("/gearbox:issue") else None
            if n and self.child_opens_pr:
                self.prs.append(pr(self.next_pr, closes=[n]))
                self.next_pr += 1
            return 0, "done", ""
        if args[:3] == ["gh", "issue", "list"]:
            return 0, json.dumps(self.issues), ""
        if args[:3] == ["gh", "pr", "list"]:
            return 0, json.dumps(self.prs), ""
        if args[:3] == ["gh", "pr", "view"]:
            return 0, json.dumps({"state": "OPEN", "isDraft": False, "headRefOid": "abc123",
                                  "files": [{"path": f} for f in self.files]}), ""
        if args[:3] == ["gh", "pr", "checks"]:
            bucket = self.checks.pop(0) if len(self.checks) > 1 else self.checks[0]
            return (0, "[]", "") if bucket is None else (0, json.dumps([{"name": "verify", "bucket": bucket}]), "")
        if args[:3] == ["gh", "pr", "merge"]:
            n = int(args[3])
            merged = next(p for p in self.prs if p["number"] == n)
            self.prs.remove(merged)
            for i in self.issues:
                if i["number"] in {c["number"] for c in merged["closingIssuesReferences"]}:
                    i["state"] = "CLOSED"
            return 0, "", ""
        if args[:2] == ["gh", "issue"] or args[:2] == ["gh", "pr"]:
            if args[2] == "edit":
                for i in self.issues if args[1] == "issue" else self.prs:
                    if i["number"] == int(args[3]):
                        i["labels"].append({"name": ap.NEEDS_HUMAN})
            return 0, "", ""
        return 0, "", ""  # git, sh

    def merges(self):
        return [c for c in self.calls if c[:3] == ["gh", "pr", "merge"]]


class ParsingTests(unittest.TestCase):
    def test_dependency_lines_in_french_and_english(self):
        body = "## Dépendances\nDépend de #2\nDepends on #3, #4\nBlocked by #5\nVoir aussi #9"
        self.assertEqual(ap.parse_deps(body), [2, 3, 4, 5])
        self.assertEqual(ap.parse_deps(None), [])

    def test_targets(self):
        for t in ("owner/name", "https://github.com/owner/name", "https://github.com/owner/name.git", "git@github.com:owner/name.git"):
            self.assertEqual(ap.parse_target(t), ("owner", "name"), t)
        self.assertIsNone(ap.parse_target("not a repo"))

    def test_config_overrides_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".gearbox").mkdir()
            (Path(d) / ".gearbox" / "config.md").write_text("```yaml\nautopilot_label: ready\nautopilot_deploy: npm run deploy\nother: x\n```\n")
            cfg = ap.load_config(Path(d))
        self.assertEqual(cfg["autopilot_label"], "ready")
        self.assertEqual(cfg["autopilot_deploy"], "npm run deploy")
        self.assertEqual(cfg["base_branch"], "main")
        self.assertNotIn("other", cfg)

    def test_guarded_paths_match_dirs_and_files(self):
        guarded = [".github/", ".gearbox/config.md"]
        self.assertEqual(ap.guarded_hits([".github/workflows/x.yml", ".gearbox/config.md", ".githubx", "src/a"], guarded),
                         [".github/workflows/x.yml", ".gearbox/config.md"])


class SelectionTests(unittest.TestCase):
    def test_next_ready_respects_dependencies_humans_and_open_prs(self):
        issues = [issue(1, state="CLOSED"), issue(2, body="Dépend de #1"), issue(3, body="Dépend de #4"),
                  issue(4), issue(5, labels=("autopilot", "needs-human")), issue(6, labels=())]
        self.assertEqual(ap.next_ready(issues, [], "autopilot")["number"], 2)
        self.assertEqual(ap.next_ready(issues, [pr(10, closes=[2])], "autopilot")["number"], 4)
        self.assertIsNone(ap.next_ready([issue(7, body="Dépend de #99")], [], "autopilot"), "unknown dependency is not closed")

    def test_pending_pr_skips_prs_flagged_for_a_human(self):
        issues = [issue(1), issue(2)]
        self.assertEqual(ap.pending_pr(issues, [pr(10, closes=[1], labels=("needs-human",)), pr(11, closes=[2])], "autopilot")[0]["number"], 11)
        self.assertIsNone(ap.pending_pr(issues, [pr(12, closes=[42])], "autopilot"))


class MergeGateTests(unittest.TestCase):
    repo = Path(".")

    def test_guarded_path_blocks_without_merging(self):
        gh = FakeGitHub([issue(1)], [pr(10, closes=[1])], files=(".github/workflows/verify.yml",))
        verdict = ap.merge_gate(self.repo, 10, [".github/"], 60, gh, lambda s: None)
        self.assertEqual(verdict["status"], "BLOCKED")
        self.assertEqual(gh.merges(), [])

    def test_failed_check_blocks(self):
        gh = FakeGitHub([issue(1)], [pr(10, closes=[1])], checks=("fail",))
        verdict = ap.merge_gate(self.repo, 10, [], 60, gh, lambda s: None)
        self.assertTrue(verdict["checks_failed"])
        self.assertEqual(gh.merges(), [])

    def test_waits_for_pending_then_merges_on_exact_head(self):
        gh = FakeGitHub([issue(1)], [pr(10, closes=[1])], checks=("pending", "pass"))
        verdict = ap.merge_gate(self.repo, 10, [], 60, gh, lambda s: None)
        self.assertEqual(verdict["status"], "MERGED")
        self.assertIn("--match-head-commit", gh.merges()[0])
        self.assertEqual(gh.merges()[0][-1], "abc123")

    def test_no_checks_is_never_green(self):
        gh = FakeGitHub([issue(1)], [pr(10, closes=[1])], checks=(None,))
        self.assertEqual(ap.merge_gate(self.repo, 10, [], 0, gh, lambda s: None)["status"], "BLOCKED")
        self.assertEqual(gh.merges(), [])


class DrainTests(unittest.TestCase):
    def pilot(self, gh):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return ap.Autopilot(Path(tmp.name), dict(ap.DEFAULTS), gh, lambda s: None, Path(tmp.name) / "logs")

    def test_drains_backlog_in_dependency_order_with_one_child_per_issue(self):
        gh = FakeGitHub([issue(1), issue(2, body="Dépend de #1"), issue(3, body="Dépend de #2")])
        stop = self.pilot(gh).drain(max_merges=10, max_hours=1)
        self.assertEqual(stop, "backlog empty")
        children = [c[2] for c in gh.calls if c[0] == "claude"]
        self.assertEqual(children, [f"/gearbox:issue {n} --auto --ship --follow-pr" for n in (1, 2, 3)])
        self.assertEqual(len(gh.merges()), 3)

    def test_issue_without_pr_is_flagged_and_dependents_wait(self):
        gh = FakeGitHub([issue(1), issue(2, body="Dépend de #1")], child_opens_pr=False)
        stop = self.pilot(gh).drain(max_merges=10, max_hours=1)
        self.assertTrue(stop.startswith("backlog blocked"), stop)
        self.assertIn(ap.NEEDS_HUMAN, ap.labels_of(gh.issues[0]))
        self.assertEqual(gh.merges(), [])

    def test_red_pr_gets_one_repair_then_a_human(self):
        gh = FakeGitHub([issue(1)], checks=("fail",))
        stop = self.pilot(gh).drain(max_merges=10, max_hours=1)
        self.assertTrue(any(c[0] == "claude" and c[2].startswith("/gearbox:continue-pr") for c in gh.calls))
        self.assertTrue(stop.startswith("backlog blocked"), stop)
        self.assertEqual(gh.merges(), [])

    def test_pause_issue_stops_before_any_work(self):
        gh = FakeGitHub([issue(1), issue(2, labels=(ap.PAUSE,))])
        self.assertEqual(self.pilot(gh).drain(max_merges=10, max_hours=1), "paused by an open autopilot-pause issue")
        self.assertFalse(any(c[0] == "claude" for c in gh.calls))

    def test_flag_failure_does_not_loop_on_the_same_pr(self):
        gh = FakeGitHub([issue(1)], checks=("fail",))
        real = gh.__call__
        gh_no_labels = lambda args, cwd, timeout=None: (1, "", "label not found") if args[2:3] == ["edit"] else real(args, cwd, timeout)
        stop = self.pilot(gh_no_labels).drain(max_merges=10, max_hours=1)
        repairs = [c for c in gh.calls if c[0] == "claude" and c[2].startswith("/gearbox:continue-pr")]
        self.assertEqual(len(repairs), 1)
        self.assertTrue(stop.startswith("backlog"), stop)

    def test_merge_budget(self):
        gh = FakeGitHub([issue(1), issue(2)])
        self.assertEqual(self.pilot(gh).drain(max_merges=1, max_hours=1), "merge budget reached")
        self.assertEqual(len(gh.merges()), 1)


if __name__ == "__main__":
    unittest.main()
