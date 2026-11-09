#!/usr/bin/env python3
"""Drain a repository's labelled GitHub issue backlog without a human in the loop.

Each issue runs in its own `claude -p "/gearbox:issue N --auto --ship --follow-pr"` process, so every
issue starts from a fresh context. The only way a PR reaches the base branch is `merge_gate`: every
check green on the exact head commit and no guarded path touched. Anything else is labelled
`needs-human`, explained in a comment, and skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

NEEDS_HUMAN = "needs-human"
PAUSE = "autopilot-pause"
DEFAULTS = {
    "base_branch": "main",
    "autopilot_label": "autopilot",
    "autopilot_max_merges": "10",
    "autopilot_max_hours": "8",
    "autopilot_guarded_paths": ".github/,.claude/,.gearbox/config.md",
    "autopilot_deploy": "",
    "autopilot_permission_mode": "auto",
    "autopilot_check_timeout_min": "30",
}
MAX_CONSECUTIVE_FAILURES = 3
DEP_LINE = re.compile(r"(d[ée]pend|depends on|blocked by|requires)", re.I)
GITHUB_SLUG = re.compile(r"^(?:https://github\.com/|git@github\.com:)?([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")

# (args, cwd, timeout) -> (returncode, stdout, stderr); injectable for tests.
Runner = Callable[[list, Path, "float | None"], "tuple[int, str, str]"]


def default_runner(args: list, cwd: Path, timeout: float | None = None) -> tuple[int, str, str]:
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"


def parse_deps(body: str | None) -> list[int]:
    """Issue numbers named on a dependency line ("Dépend de #2", "Depends on #3, #4", "Blocked by #5")."""
    deps: set[int] = set()
    for line in (body or "").splitlines():
        if DEP_LINE.search(line):
            deps.update(int(n) for n in re.findall(r"#(\d+)", line))
    return sorted(deps)


def load_config(repo: Path) -> dict[str, str]:
    """Flat `key: value` lines from .gearbox/config.md over DEFAULTS (the file is YAML-ish markdown)."""
    cfg = dict(DEFAULTS)
    path = repo / ".gearbox" / "config.md"
    if path.exists():
        for line in path.read_text(errors="replace").splitlines():
            m = re.match(r"^([a-z_]+):\s*(.*?)\s*$", line)
            if m and m.group(1) in cfg:
                cfg[m.group(1)] = m.group(2).strip("'\"")
    return cfg


def parse_target(target: str) -> tuple[str, str] | None:
    m = GITHUB_SLUG.match(target.strip())
    return (m.group(1), m.group(2)) if m else None


def resolve_target(target: str, workspace: Path, run: Runner = default_runner) -> Path:
    """A local clone path for a directory, an owner/name slug, or a GitHub URL (cloned if missing)."""
    local = Path(target).expanduser()
    if local.is_dir():
        return local.resolve()
    slug = parse_target(target)
    if not slug:
        raise SystemExit(f"autopilot: not a directory nor a GitHub repository: {target}")
    dest = workspace.expanduser() / slug[0] / slug[1]
    if (dest / ".git").is_dir():
        run(["git", "fetch", "--quiet"], dest, 300)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        code, _, err = run(["gh", "repo", "clone", f"{slug[0]}/{slug[1]}", str(dest)], dest.parent, 600)
        if code:
            raise SystemExit(f"autopilot: clone failed: {err.strip()}")
    return dest


def labels_of(item: dict) -> set[str]:
    return {label["name"] for label in item.get("labels", [])}


def closing_numbers(pr: dict) -> set[int]:
    return {ref["number"] for ref in pr.get("closingIssuesReferences", [])}


def next_ready(issues: list[dict], open_prs: list[dict], label: str) -> dict | None:
    """Lowest-numbered open labelled issue with every dependency closed and no open PR already on it."""
    state = {i["number"]: i["state"] for i in issues}
    taken = set().union(*(closing_numbers(p) for p in open_prs)) if open_prs else set()
    for issue in sorted(issues, key=lambda i: i["number"]):
        tags = labels_of(issue)
        if issue["state"] != "OPEN" or label not in tags or NEEDS_HUMAN in tags or issue["number"] in taken:
            continue
        if all(state.get(dep) == "CLOSED" for dep in parse_deps(issue.get("body"))):
            return issue
    return None


def pending_pr(issues: list[dict], open_prs: list[dict], label: str) -> tuple[dict, int] | None:
    """An open PR (not flagged for a human) that closes an open labelled issue: finish it before new work."""
    ours = {i["number"] for i in issues if i["state"] == "OPEN" and label in labels_of(i)}
    for pr in sorted(open_prs, key=lambda p: p["number"]):
        hit = closing_numbers(pr) & ours
        if hit and NEEDS_HUMAN not in labels_of(pr):
            return pr, min(hit)
    return None


def guarded_hits(paths: list[str], guarded: list[str]) -> list[str]:
    return [p for p in paths if any(p == g or (g.endswith("/") and p.startswith(g)) for g in guarded)]


def merge_gate(repo: Path, pr: int, guarded: list[str], check_timeout: float,
               run: Runner = default_runner, sleep: Callable[[float], None] = time.sleep) -> dict:
    """Merge only when the PR is open, touches no guarded path, and every check passed on the exact head."""
    code, out, err = run(["gh", "pr", "view", str(pr), "--json", "state,isDraft,headRefOid,files"], repo, 60)
    if code:
        return {"status": "BLOCKED", "reason": f"cannot read PR: {err.strip()}"}
    view = json.loads(out)
    if view["state"] != "OPEN" or view["isDraft"]:
        return {"status": "BLOCKED", "reason": "PR is not open or is a draft"}
    hits = guarded_hits([f["path"] for f in view.get("files", [])], guarded)
    if hits:
        return {"status": "BLOCKED", "reason": f"guarded paths changed: {', '.join(hits)}"}
    head = view["headRefOid"]
    deadline = time.monotonic() + check_timeout
    while True:
        # `gh pr checks` exits non-zero while checks are pending or failed; the JSON is what matters.
        _, out, _ = run(["gh", "pr", "checks", str(pr), "--json", "name,bucket"], repo, 60)
        checks = json.loads(out) if out.strip().startswith("[") else []
        buckets = {c["bucket"] for c in checks}
        if checks and buckets & {"fail", "cancel"}:
            failed = [c["name"] for c in checks if c["bucket"] in {"fail", "cancel"}]
            return {"status": "BLOCKED", "reason": f"checks failed: {', '.join(failed)}", "checks_failed": True}
        if checks and buckets <= {"pass", "skipping"} and "pass" in buckets:
            break
        if time.monotonic() > deadline:
            return {"status": "BLOCKED", "reason": "no checks reported" if not checks else "checks still pending at timeout"}
        sleep(30)
    # --match-head-commit refuses the merge if anything was pushed after the checks ran.
    code, _, err = run(["gh", "pr", "merge", str(pr), "--squash", "--delete-branch", "--match-head-commit", head], repo, 120)
    if code:
        return {"status": "BLOCKED", "reason": f"merge refused: {err.strip()}"}
    return {"status": "MERGED", "head": head}


class Autopilot:
    def __init__(self, repo: Path, cfg: dict[str, str], run: Runner = default_runner,
                 sleep: Callable[[float], None] = time.sleep, log_dir: Path | None = None):
        self.repo, self.cfg, self.run, self.sleep = repo, cfg, run, sleep
        self.label = cfg["autopilot_label"]
        self.guarded = [g.strip() for g in cfg["autopilot_guarded_paths"].split(",") if g.strip()]
        self.log_dir = log_dir or repo / ".gearbox" / "runs" / f"autopilot-{time.strftime('%Y%m%d-%H%M%S')}"
        self.events: list[dict] = []
        self.given_up: set[int] = set()  # issues/PRs flagged this run, never retried even if labelling failed

    def gh_json(self, *args: str) -> list | dict:
        code, out, err = self.run(["gh", *args], self.repo, 120)
        if code:
            raise RuntimeError(f"gh {' '.join(args[:2])} failed: {err.strip()}")
        return json.loads(out)

    def note(self, **event) -> None:
        event["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.events.append(event)
        print(json.dumps(event, ensure_ascii=False), flush=True)

    def flag(self, number: int, kind: str, reason: str) -> None:
        self.given_up.add(number)
        self.run(["gh", kind, "edit", str(number), "--add-label", NEEDS_HUMAN], self.repo, 60)
        self.run(["gh", kind, "comment", str(number), "--body",
                  f"Autopilot stopped here and needs a human.\n\nReason: {reason}"], self.repo, 60)

    def child(self, prompt: str, name: str, timeout: float) -> int:
        """One fresh Claude Code process per unit of work; its transcript goes to the run log."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        code, out, err = self.run(["claude", "-p", prompt, "--permission-mode", self.cfg["autopilot_permission_mode"]],
                                  self.repo, timeout)
        (self.log_dir / f"{name}.log").write_text(out + ("\n--- stderr ---\n" + err if err else ""))
        return code

    def sync_base(self) -> None:
        base = self.cfg["base_branch"]
        self.run(["git", "switch", "--quiet", base], self.repo, 60)
        self.run(["git", "pull", "--quiet", "--ff-only"], self.repo, 300)

    def finish_pr(self, pr: int, issue: int, remaining: float) -> bool:
        timeout = float(self.cfg["autopilot_check_timeout_min"]) * 60
        verdict = merge_gate(self.repo, pr, self.guarded, timeout, self.run, self.sleep)
        if verdict.get("checks_failed"):
            self.note(event="repair", pr=pr, reason=verdict["reason"])
            self.child(f"/gearbox:continue-pr {pr} --auto", f"pr-{pr}-repair", remaining)
            verdict = merge_gate(self.repo, pr, self.guarded, timeout, self.run, self.sleep)
        if verdict["status"] != "MERGED":
            self.flag(pr, "pr", verdict["reason"])
            self.flag(issue, "issue", f"PR #{pr} blocked: {verdict['reason']}")
            self.note(event="blocked", issue=issue, pr=pr, reason=verdict["reason"])
            return False
        self.note(event="merged", issue=issue, pr=pr, head=verdict["head"])
        self.sync_base()
        deploy = self.cfg["autopilot_deploy"]
        if deploy:
            code, out, err = self.run(["sh", "-c", deploy], self.repo, 1800)
            self.note(event="deploy", ok=code == 0, output=(out or err).strip()[-500:])
        return True

    def drain(self, max_merges: int, max_hours: float) -> str:
        code, out, _ = self.run(["git", "status", "--porcelain", "--untracked-files=no"], self.repo, 60)
        if code or out.strip():
            return "dirty working tree: commit or stash local changes first"
        for name, color in ((NEEDS_HUMAN, "D93F0B"), (PAUSE, "FBCA04"), (self.label, "2347D8")):
            self.run(["gh", "label", "create", name, "--color", color], self.repo, 60)  # fails harmlessly if it exists
        self.sync_base()
        end = time.monotonic() + max_hours * 3600
        merged = failures = 0
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                return "time budget reached"
            if merged >= max_merges:
                return "merge budget reached"
            if failures >= MAX_CONSECUTIVE_FAILURES:
                return f"{failures} consecutive failures"
            issues = self.gh_json("issue", "list", "--state", "all", "--limit", "1000",
                                  "--json", "number,title,state,labels,body")
            if any(i["state"] == "OPEN" and PAUSE in labels_of(i) for i in issues):
                return "paused by an open autopilot-pause issue"
            prs = self.gh_json("pr", "list", "--state", "open", "--json", "number,labels,closingIssuesReferences")
            prs = [p for p in prs if p["number"] not in self.given_up]
            left = [i["number"] for i in issues if i["state"] == "OPEN" and self.label in labels_of(i)]
            issues = [i for i in issues if i["number"] not in self.given_up or i["state"] != "OPEN"]
            pending = pending_pr(issues, prs, self.label)
            if pending:
                ok = self.finish_pr(pending[0]["number"], pending[1], remaining)
                merged, failures = (merged + 1, 0) if ok else (merged, failures + 1)
                continue
            issue = next_ready(issues, prs, self.label)
            if not issue:
                return f"backlog blocked, waiting on a human: {left}" if left else "backlog empty"
            n = issue["number"]
            self.note(event="start", issue=n, title=issue["title"])
            self.child(f"/gearbox:issue {n} --auto --ship --follow-pr", f"issue-{n}", remaining)
            self.sync_base()
            prs = self.gh_json("pr", "list", "--state", "open", "--json", "number,labels,closingIssuesReferences")
            pr = next((p for p in prs if n in closing_numbers(p)), None)
            if not pr:
                self.flag(n, "issue", f"the Gearbox run produced no open PR closing #{n}; see {self.log_dir}/issue-{n}.log")
                self.note(event="blocked", issue=n, reason="no PR")
                failures += 1
                continue
            ok = self.finish_pr(pr["number"], n, end - time.monotonic())
            merged, failures = (merged + 1, 0) if ok else (merged, failures + 1)


def acquire_lock(repo: Path) -> Path | None:
    # Inside .git so the lock never shows up as a working-tree change.
    lock = repo / ".git" / "gearbox-autopilot.lock"
    if lock.exists():
        try:
            os.kill(int(lock.read_text().strip()), 0)
            return None  # a live autopilot already owns this repository
        except (ValueError, ProcessLookupError, PermissionError):
            pass  # stale lock from a dead process
    lock.write_text(str(os.getpid()))
    return lock


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("action", choices=["run", "queue"])
    p.add_argument("target", help="local clone, owner/name, or GitHub URL")
    p.add_argument("--workspace", default="~/gearbox-autopilot", help="where owner/name targets are cloned")
    p.add_argument("--max-merges", type=int)
    p.add_argument("--max-hours", type=float)
    a = p.parse_args(argv)
    if not shutil.which("claude") or default_runner(["gh", "auth", "status"], Path.cwd(), 30)[0]:
        print(json.dumps({"stop": "preflight failed: `claude` must be on PATH and `gh auth status` must succeed"}))
        return 1
    repo = resolve_target(a.target, Path(a.workspace))
    cfg = load_config(repo)
    pilot = Autopilot(repo, cfg)
    if a.action == "queue":
        issues = pilot.gh_json("issue", "list", "--state", "all", "--limit", "1000", "--json", "number,title,state,labels,body")
        prs = pilot.gh_json("pr", "list", "--state", "open", "--json", "number,labels,closingIssuesReferences")
        pending, nxt = pending_pr(issues, prs, pilot.label), next_ready(issues, prs, pilot.label)
        print(json.dumps({"repo": str(repo), "label": pilot.label,
                          "pending_pr": pending[0]["number"] if pending else None,
                          "next_issue": nxt["number"] if nxt else None,
                          "open_labelled": [i["number"] for i in issues if i["state"] == "OPEN" and pilot.label in labels_of(i)]}))
        return 0
    lock = acquire_lock(repo)
    if not lock:
        print(json.dumps({"stop": "another autopilot run holds the lock", "repo": str(repo)}))
        return 1
    try:
        stop = pilot.drain(a.max_merges or int(cfg["autopilot_max_merges"]), a.max_hours or float(cfg["autopilot_max_hours"]))
    finally:
        lock.unlink(missing_ok=True)
    pilot.log_dir.mkdir(parents=True, exist_ok=True)
    report = {"repo": str(repo), "stop": stop, "events": pilot.events}
    (pilot.log_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({"stop": stop, "report": str(pilot.log_dir / "report.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
