#!/usr/bin/env python3
"""Fail-closed GitHub issue prerequisites and local source-spec preflight.

Only reads GitHub and the local repository. The orchestrator records the
result into run_state.py before planning or dispatching implementation work.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEPENDENCY_LINE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?(?:Dépendances|Dependencies|Depends on|Blocked by)(?:\*\*)?\s*:\s*(.*)$"
)
DOCUMENT_LINE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?(Fichier source|Source spec|Document de conventions)(?:\*\*)?\s*:\s*(.*)$"
)
REFERENCE = re.compile(r"(?<![\w/])US-\d{3}\b|(?<![\w/])#\d+\b", re.I)
ISSUE_URL = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)(?:[/?#].*)?$")
SOURCE_CODE = re.compile(r"(?<!\w)\x60([^\x60]+\.md)\x60")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
ISSUE_ID = re.compile(r"^US-\d{3}\b", re.I)


class PreflightError(Exception):
    """An external dependency could not be verified."""


def run_gh(*args: str) -> Any:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=30, check=False)
    if proc.returncode:
        raise PreflightError(f"gh {' '.join(args[:3])} failed: {proc.stderr.strip()[:350]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise PreflightError("GitHub CLI did not return valid JSON") from exc


def parse_dependencies(body: str) -> list[str]:
    """Only parse explicitly declared dependency lines, never incidental references."""
    result: list[str] = []
    for match in DEPENDENCY_LINE.finditer(body):
        for ref in REFERENCE.findall(match.group(1)):
            key = ref.upper()
            if key not in result:
                result.append(key)
    return result


def parse_documents(body: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in DOCUMENT_LINE.finditer(body):
        key, value = match.group(1).lower(), match.group(2)
        path_match = SOURCE_CODE.search(value)
        if path_match:
            path = path_match.group(1)
        else:
            link = MARKDOWN_LINK.search(value)
            if link:
                url = link.group(1)
                # Accept browser links to the same repository once repo identity
                # is checked when resolving the path.
                path = url
            else:
                path = value.strip().split()[0] if value.strip() else ""
        if path:
            result["conventions" if key == "document de conventions" else "source_spec"] = path
    return result


def safe_document(repo_root: Path, source: str, repo: str) -> str:
    source = source.strip()
    if source.startswith("https://github.com/"):
        expected = f"https://github.com/{repo}/blob/"
        if not source.startswith(expected):
            raise PreflightError("Referenced spec belongs to a different repository")
        remainder = source[len(expected):]
        if "/" not in remainder:
            raise PreflightError("Source spec link has no repository path")
        # Links with branches containing slashes are intentionally unsupported:
        # a literal local path in the link label avoids ambiguity.
        source = remainder.split("/", 1)[1]
    elif source.startswith("../blob/"):
        remainder = source[len("../blob/"):]
        source = remainder.split("/", 1)[1] if "/" in remainder else ""
    path = Path(source)
    if not source.endswith(".md") or path.is_absolute() or not path.parts:
        raise PreflightError(f"Invalid local Markdown spec path: {source!r}")
    root = repo_root.resolve()
    absolute = (root / path).resolve()
    if not absolute.is_relative_to(root) or not absolute.is_file():
        raise PreflightError(f"Referenced Markdown spec missing or outside repository: {source}")
    return str(absolute.relative_to(root))


def resolve_dependency(ref: str, repo: str, current_number: int) -> dict[str, Any]:
    if ref.startswith("#"):
        number = int(ref[1:])
    else:
        matches = run_gh(
            "issue", "list", "--repo", repo, "--state", "all",
            "--search", f"{ref} in:title", "--limit", "100",
            "--json", "number,title,state,url",
        )
        exact = [item for item in matches if ISSUE_ID.match(item.get("title", "")) and
                 ISSUE_ID.match(item["title"]).group(0).upper() == ref]
        if len(exact) != 1:
            raise PreflightError(f"{ref}: expected exactly one issue with this title prefix; found {len(exact)}")
        number = int(exact[0]["number"])
    if number == current_number:
        raise PreflightError(f"{ref}: issue cannot depend on itself")
    dep = run_gh(
        "issue", "view", str(number), "--repo", repo,
        "--json", "number,title,state,url,closedByPullRequestsReferences",
    )
    if dep.get("state", "").upper() != "CLOSED":
        raise PreflightError(f"{ref} (#{number}): prerequisite issue is not closed")
    prs = dep.get("closedByPullRequestsReferences") or []
    if not prs:
        raise PreflightError(f"{ref} (#{number}): no linked closing PR; closure alone is not merge evidence")
    default = run_gh("repo", "view", repo, "--json", "defaultBranchRef")["defaultBranchRef"]["name"]
    for pr in prs:
        pr_number = pr.get("number")
        if not pr_number:
            continue
        detail = run_gh("pr", "view", str(pr_number), "--repo", repo,
                        "--json", "state,mergedAt,mergeCommit,url")
        sha = (detail.get("mergeCommit") or {}).get("oid")
        if not (detail.get("mergedAt") and sha):
            continue
        compare = run_gh("api", f"repos/{repo}/compare/{sha}...{default}")
        if compare.get("status") in ("ahead", "identical"):
            return {
                "reference": ref, "issue_number": number, "status": "PASS",
                "closing_pr": detail.get("url"), "merge_sha": sha,
                "default_branch": default,
            }
    raise PreflightError(f"{ref} (#{number}): no merged closing PR commit verified in {default}")


def verify_issue(issue: dict[str, Any], repo: str, root: Path) -> dict[str, Any]:
    number = int(issue["number"])
    body = issue.get("body") or ""
    documents = parse_documents(body)
    report: dict[str, Any] = {
        "status": "PASS", "issue": number, "repository": repo,
        "source_spec": None, "conventions": None, "dependencies": [], "errors": [],
    }
    for field in ("source_spec", "conventions"):
        if field in documents:
            try:
                report[field] = safe_document(root, documents[field], repo)
            except PreflightError as exc:
                report["errors"].append(str(exc))
    for ref in parse_dependencies(body):
        try:
            report["dependencies"].append(resolve_dependency(ref, repo, number))
        except PreflightError as exc:
            report["dependencies"].append({"reference": ref, "status": "BLOCKED", "reason": str(exc)})
            report["errors"].append(str(exc))
    if report["errors"]:
        report["status"] = "BLOCKED"
    return report


def parse_issue_reference(reference: str, repo: str) -> int:
    if reference.isdigit():
        return int(reference)
    match = ISSUE_URL.match(reference)
    if not match or f"{match.group(1)}/{match.group(2)}".lower() != repo.lower():
        raise PreflightError("Issue reference must be a number or a GitHub issue URL from the current repository")
    return int(match.group(3))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check issue prerequisites and local source specs")
    parser.add_argument("--issue", required=True, help="Issue number or same-repository URL")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--repo", help="owner/repository (default: discover using gh)")
    parser.add_argument("--output", help="Write JSON result, e.g. .gearbox/runs/issue-N/issue-preflight.json")
    args = parser.parse_args()
    report: dict[str, Any]
    try:
        root = Path(args.repo_root).resolve()
        if not root.is_dir():
            raise PreflightError("Repository root does not exist")
        repo = args.repo or run_gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
        number = parse_issue_reference(args.issue, repo)
        issue = run_gh("issue", "view", str(number), "--repo", repo,
                       "--json", "number,title,body,state,url")
        report = verify_issue(issue, repo, root)
    except (PreflightError, subprocess.TimeoutExpired, OSError, KeyError, ValueError) as exc:
        report = {"status": "BLOCKED", "issue": args.issue, "errors": [str(exc)],
                  "dependencies": [], "source_spec": None, "conventions": None}
    if args.output:
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 4


if __name__ == "__main__":
    sys.exit(main())
