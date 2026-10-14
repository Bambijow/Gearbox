#!/usr/bin/env python3
"""Read-only, hash-verified decision dependency ledger and invalidation graph."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from gate_result import SHA256, verify_proofs


def valid_text(value):
    return isinstance(value, str) and bool(value.strip())


def index(items, label, errors):
    if not isinstance(items, list):
        errors.append(f"{label} must be a list")
        return {}
    result = {}
    for item in items:
        if not isinstance(item, dict) or not valid_text(item.get("id")):
            errors.append(f"{label} entry needs id")
        elif item["id"] in result:
            errors.append(f"duplicate {label} id {item['id']}")
        else:
            result[item["id"]] = item
    return result


def inspect_ledger(data, root: Path, changed_evidence=()):
    errors, stale = [], set()
    if not isinstance(data, dict):
        data = {}
        errors.append("ledger must be an object")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        errors.append("ledger schema_version must be 1")
    for field in ("run_id", "source_fingerprint"):
        if not valid_text(data.get(field)):
            errors.append(f"{field} must be set")
    evidence = index(data.get("evidence"), "evidence", errors)
    decisions = index(data.get("decisions"), "decisions", errors)
    if not decisions:
        errors.append("at least one decision is required")
    changed = set(changed_evidence)
    if changed - evidence.keys():
        errors.append("changed_evidence contains an unknown evidence id")
    verified = set()
    for eid, item in evidence.items():
        problems = []
        if not valid_text(item.get("path")) or Path(item.get("path", ".")).is_absolute():
            problems.append("relative path required")
        if not isinstance(item.get("sha256"), str) or not SHA256.fullmatch(item["sha256"]):
            problems.append("SHA-256 required")
        if item.get("source_fingerprint") != data.get("source_fingerprint"):
            problems.append("source fingerprint mismatch")
        if not problems:
            problems.extend(verify_proofs({"evidence": [{"kind": "decision", "path": item["path"],
                                                           "sha256": item["sha256"]}]},
                                          {"required_evidence_kinds": ["decision"]}, root))
        if problems:
            errors.extend(f"{eid}: {problem}" for problem in problems)
            stale.add(eid)
        else:
            verified.add(eid)
    parents = {}
    for did, item in decisions.items():
        for field in ("statement", "decision_reason", "falsifier"):
            if not valid_text(item.get(field)):
                errors.append(f"{did}: {field} required")
        if item.get("kind") not in {"observation", "hypothesis", "approved-target"}:
            errors.append(f"{did}: invalid kind")
        if item.get("kind") == "approved-target" and not valid_text(item.get("approval_pointer")):
            errors.append(f"{did}: user-approved decision needs approval_pointer")
        refs = item.get("evidence_ids")
        if not isinstance(refs, list) or not refs or not all(valid_text(x) for x in refs):
            errors.append(f"{did}: nonempty evidence_ids required")
            refs = []
        if any(x not in evidence for x in refs):
            errors.append(f"{did}: missing evidence reference")
        dependencies = item.get("depends_on", [])
        if not isinstance(dependencies, list) or not all(valid_text(x) for x in dependencies):
            errors.append(f"{did}: depends_on must be string ids")
            dependencies = []
        if did in dependencies or any(x not in decisions for x in dependencies):
            errors.append(f"{did}: unknown/self decision dependency")
        tasks = item.get("affected_tasks", [])
        if not isinstance(tasks, list) or not all(valid_text(x) for x in tasks):
            errors.append(f"{did}: affected_tasks must be string ids")
        parents[did] = dependencies
        if any(x not in verified or x in changed for x in refs):
            stale.add(did)
    # Propagate changed evidence to dependent decisions. Detect dependency cycles.
    states = {}
    def visit(did):
        if states.get(did) == 1:
            errors.append(f"cycle in decision dependencies at {did}")
            return False
        if states.get(did) == 2:
            return did in stale
        states[did] = 1
        if any(visit(other) for other in parents.get(did, ()) if other in decisions):
            stale.add(did)
        states[did] = 2
        return did in stale
    for did in decisions:
        visit(did)
    invalidated = []
    for did, decision in sorted(decisions.items()):
        if did in stale:
            invalidated.append({"decision_id": did,
                                "affected_tasks": sorted(set(decision.get("affected_tasks", [])))
                                if isinstance(decision.get("affected_tasks", []), list) else []})
    return {"schema_version": 1, "status": "BLOCKED" if errors else ("REVALIDATION_REQUIRED" if invalidated else "VERIFIED_LEDGER"),
            "errors": errors, "verified_evidence_ids": sorted(verified),
            "invalidated_decisions": invalidated, "changed_evidence_ids": sorted(changed),
            "note": "Integrity and dependency checks only; semantic truth and user approval require separate checks."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--changed-evidence", action="append", default=[])
    args = parser.parse_args()
    try:
        raw = args.input.read_bytes()
        result = inspect_ledger(json.loads(raw), args.input.parent, args.changed_evidence)
        result["ledger_sha256"] = hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "VERIFIED_LEDGER" else 6


if __name__ == "__main__":
    raise SystemExit(main())
