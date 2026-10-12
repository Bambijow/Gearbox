#!/usr/bin/env python3
"""Read-only run diagnostics. Never reconcile, unlock, approve or dispatch work."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from redact import redact_obj
from usage_ledger import totals


def inspect_run(run: Path, repo_root: Path | None = None) -> dict:
    run = run.resolve()
    repo_root = (repo_root or Path.cwd()).resolve()
    warnings = []

    def read(path: Path, required: bool = False) -> dict:
        try:
            resolved = path.resolve()
            if not (resolved.is_relative_to(run) or resolved.is_relative_to(repo_root)):
                raise ValueError("reference outside run/repository")
            if not resolved.exists() and not required:
                return {}
            value = json.loads(resolved.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            return value
        except (OSError, ValueError, RuntimeError) as exc:
            if required:
                raise ValueError(f"cannot inspect {path.name}: {exc}") from exc
            warnings.append(f"{path.name}: {exc}")
            return {}

    def reference(value) -> dict:
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value:
            path = Path(value)
            if not path.is_absolute():
                local = run / path
                path = local if local.exists() else repo_root / path
            return read(path, required=True)
        return {}

    state = read(run / "state.json", required=True)
    approval = state.get("plan_approval") or {}
    problem = None
    if approval.get("required") and approval.get("status") != "APPROVED":
        problem = "Exact persisted plan needs human approval."
    elif approval.get("status") in {"APPROVED", "AUTO_APPROVED"}:
        raw = approval.get("plan_resolved") or approval.get("plan_path")
        try:
            if not raw:
                raise ValueError("approved plan path missing")
            path = (repo_root / raw).resolve()
            if not (path.is_relative_to(repo_root) or path.is_relative_to(run)):
                raise ValueError("approved plan outside run/repository")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != approval.get("approved_sha256"):
                problem = "Approved plan changed; re-present it before dispatch."
        except (OSError, ValueError, RuntimeError) as exc:
            problem = str(exc)

    runtime = state.get("runtime_plans") or {}
    try:
        scheduler = reference(runtime.get("scheduler"))
    except ValueError as exc:
        warnings.append(str(exc)); scheduler = {}
    quality = state.get("quality") or {}
    quality_result = None
    if quality.get("plan_path"):
        try:
            from gate_result import aggregate
            plan = reference(quality["plan_path"])
            results = [reference(value) for value in (quality.get("gate_results") or {}).values()]
            quality_result = aggregate(plan, results, artifact_root=run)
        except (ValueError, TypeError, AttributeError) as exc:
            quality_result = {"status": "BLOCKED", "error": str(exc)}
    children_data = read(run / "children.json")
    children = children_data.get("children", {})
    if not isinstance(children, dict):
        warnings.append("children.json: children must be an object"); children = {}
    child_counts = Counter(str(child.get("status", "UNKNOWN")) for child in children.values() if isinstance(child, dict))
    usage = read(run / "usage.json")
    usage_items = usage.get("items", [])
    if not isinstance(usage_items, list) or not all(isinstance(item, dict) for item in usage_items):
        warnings.append("usage.json: invalid items"); usage = {}
    actions = []
    if state.get("blocker"):
        actions.append("Resolve the recorded blocker before resuming.")
    if problem:
        actions.append(problem)
    if quality_result and quality_result.get("status") != "PASS":
        actions.append("Repair or recollect the blocked/missing quality evidence; do not ship.")
    if (run / ".lock").exists():
        actions.append("A lock is present. Resume must check its owner; inspection does not break locks.")
    if not actions:
        actions.append("Use resume to reconcile Git, children and remaining gates before continuing.")
    return redact_obj({
        "schema_version": 1, "read_only": True,
        "run_id": state.get("run_id", run.name), "status": state.get("status", "UNKNOWN"),
        "phase": state.get("phase", "UNKNOWN"), "cycle": state.get("cycle"),
        "blocker": state.get("blocker"), "pending": state.get("pending", []),
        "approval": {"status": approval.get("status", "UNSET"), "required": approval.get("required"), "problem": problem},
        "quality": quality_result,
        "scheduler": {key: scheduler.get(key) for key in ("available_slots", "dispatch_units", "blocked", "waiting")},
        "recorded_child_statuses": dict(sorted(child_counts.items())),
        "usage": totals(usage), "budgets": state.get("budgets", {}),
        "cache": state.get("cache", {}), "lock_present": (run / ".lock").exists(),
        "warnings": warnings, "next_actions": actions,
        "limitations": "Recorded child statuses are not liveness checks. Git, remote CI and tool capabilities are not probed.",
    })


def render(report: dict) -> str:
    lines = [f"Run {report['run_id']}: {report['status']} / {report['phase']}",
             f"Plan approval: {report['approval']['status']}"]
    if report["blocker"]:
        lines.append("Blocker: " + json.dumps(report["blocker"], ensure_ascii=False))
    if report["quality"]:
        lines.append("Quality: " + report["quality"]["status"])
        for key in ("missing_required", "blocked", "repair", "plan_errors", "invalid_results"):
            if report["quality"].get(key):
                lines.append(f"  {key}: " + json.dumps(report["quality"][key], ensure_ascii=False))
    lines.append("Recorded children: " + json.dumps(report["recorded_child_statuses"]))
    lines.append("Recorded usage: " + json.dumps(report["usage"]))
    if report["scheduler"].get("waiting"):
        lines.append("Scheduler waiting: " + json.dumps(report["scheduler"]["waiting"]))
    lines.extend("Next: " + action for action in report["next_actions"])
    lines.extend("Warning: " + warning for warning in report["warnings"])
    lines.append(report["limitations"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = inspect_run(args.run_dir, args.repo_root)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(json.dumps({"read_only": True, "error": str(exc)}))
        return 6
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else render(report), end="\n" if args.json else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
