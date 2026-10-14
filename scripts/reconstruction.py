#!/usr/bin/env python3
"""Inspect a portable reconstruction contract without executing or modifying a target."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from gate_result import SHA256, verify_proofs

KINDS = {"source", "behavior", "interface", "binary"}
AVAILABILITY = {"runnable", "artifact-only", "recordings-only"}
DISPOSITIONS = {"preserve", "adapt", "discard", "defer"}
EVIDENCE_KINDS = {"source", "static-analysis", "runtime", "recording", "trace", "test"}


def text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def strings(value) -> bool:
    return isinstance(value, list) and all(text(item) for item in value)


def records(data, key, errors) -> dict:
    result = {}
    items = data.get(key)
    if not isinstance(items, list):
        errors.append(f"{key} must be an explicit list")
        return result
    for item in items:
        if not isinstance(item, dict) or not text(item.get("id")):
            errors.append(f"{key} entries require a string id")
        elif item["id"] in result:
            errors.append(f"duplicate {key} id: {item['id']}")
        else:
            result[item["id"]] = item
    return result


def inspect_contract(data: dict, artifact_root: Path) -> dict:
    """Check referential integrity and stated readiness, not truth of model conclusions."""
    errors, gaps = [], []
    if not isinstance(data, dict):
        data = {}
        errors.append("contract must be an object")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        errors.append("reconstruction schema_version must be 1")
    for key in ("question", "scope"):
        if not text(data.get(key)):
            errors.append(f"{key} is required")
    source = data.get("source")
    if not isinstance(source, dict):
        source = {}
        errors.append("source must identify the authority being reconstructed")
    for key in ("id", "version", "fingerprint"):
        if not text(source.get(key)):
            errors.append(f"source.{key} is required")
    if not isinstance(source.get("kind"), str) or source["kind"] not in KINDS:
        errors.append("invalid source.kind")
    if not isinstance(source.get("availability"), str) or source["availability"] not in AVAILABILITY:
        errors.append("invalid source.availability")
    if not strings(data.get("limitations")):
        errors.append("limitations must be an explicit string list")
    target = data.get("target")
    if target is not None and (not isinstance(target, dict) or not all(text(target.get(k)) for k in ("project", "revision"))):
        errors.append("target requires project and revision")

    evidence = records(data, "evidence", errors)
    claims = records(data, "claims", errors)
    scenarios = records(data, "scenarios", errors)
    decisions = records(data, "decisions", errors)
    unknowns = records(data, "unknowns", errors)
    verified = set()
    for eid, item in evidence.items():
        why = []
        if not isinstance(item.get("kind"), str) or item["kind"] not in EVIDENCE_KINDS:
            why.append("invalid evidence kind")
        if not text(item.get("source_fingerprint")) or item["source_fingerprint"] != source.get("fingerprint"):
            why.append("source fingerprint mismatch")
        if not text(item.get("path")) or Path(item["path"]).is_absolute() or not isinstance(item.get("sha256"), str) or not SHA256.fullmatch(item["sha256"]):
            why.append("evidence requires a relative path and full SHA-256 digest")
        if not strings(item.get("limitations")):
            why.append("evidence limitations must be explicit")
        if not isinstance(item.get("coverage"), str) or item["coverage"] not in {"bounded", "partial", "unknown"}:
            why.append("evidence coverage must be bounded, partial or unknown")
        if not why:
            why.extend(verify_proofs({"evidence": [item]}, {"required_evidence_kinds": [item["kind"]]}, artifact_root))
        if why:
            errors.extend(f"{eid}: {reason}" for reason in why)
        else:
            verified.add(eid)

    for cid, claim in claims.items():
        if not text(claim.get("statement")) or type(claim.get("material")) is not bool:
            errors.append(f"{cid}: statement and explicit material boolean are required")
        status = claim.get("status")
        if not isinstance(status, str) or status not in {"observed", "inferred", "unknown"}:
            errors.append(f"{cid}: invalid claim status")
        refs = claim.get("evidence_ids")
        if not strings(refs):
            errors.append(f"{cid}: evidence_ids must be a string list")
            refs = []
        if any(eid not in evidence for eid in refs):
            errors.append(f"{cid}: dangling evidence reference")
        if isinstance(status, str) and status in {"observed", "inferred"} and (not refs or not all(eid in verified for eid in refs)):
            errors.append(f"{cid}: {status} claim requires verified evidence files")
        if not strings(claim.get("limitations")):
            errors.append(f"{cid}: limitations must be explicit")
        if claim.get("material") and any(evidence.get(eid, {}).get("coverage") != "bounded" for eid in refs):
            gaps.append(f"{cid}: material claim depends on partial or unknown coverage")
        if claim.get("material") and status != "observed":
            gaps.append(f"{cid}: material behavior remains {status}")

    for sid, scenario in scenarios.items():
        for key in ("setup", "actions", "expected", "oracle"):
            if not text(scenario.get(key)):
                errors.append(f"{sid}: {key} must describe a replayable scenario")
        refs = scenario.get("claim_ids")
        if not strings(refs) or not refs or any(cid not in claims for cid in refs):
            errors.append(f"{sid}: claim_ids must reference existing claims")
        refs = scenario.get("reference_evidence_ids")
        if not strings(refs) or not refs or any(eid not in verified for eid in refs):
            errors.append(f"{sid}: reference evidence is missing or unverifiable")
        if not strings(scenario.get("normalizations")):
            errors.append(f"{sid}: normalizations must be explicit (including [])")
        if not text(scenario.get("comparison")):
            errors.append(f"{sid}: comparison must state preserved semantics and justified tolerances")

    by_claim = {}
    for did, decision in decisions.items():
        cid = decision.get("claim_id")
        if not text(cid) or cid not in claims:
            errors.append(f"{did}: unknown claim_id")
            continue
        if cid in by_claim:
            errors.append(f"{did}: duplicate decision for {cid}")
        by_claim[cid] = decision
        disposition = decision.get("disposition")
        if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
            errors.append(f"{did}: invalid disposition")
        if not text(decision.get("reason")):
            errors.append(f"{did}: reason is required")
        refs = decision.get("scenario_ids")
        if not strings(refs) or any(sid not in scenarios for sid in refs):
            errors.append(f"{did}: invalid scenario_ids")
            refs = []
        if isinstance(disposition, str) and disposition in {"preserve", "adapt"}:
            if not text(decision.get("target_behavior")):
                errors.append(f"{did}: target_behavior must be explicit")
            if not refs or any(not strings(scenarios[sid].get("claim_ids")) or cid not in scenarios[sid]["claim_ids"] for sid in refs):
                errors.append(f"{did}: each scenario must exercise the selected claim")
        if disposition == "defer" and claims[cid].get("material"):
            gaps.append(f"{cid}: material transfer decision deferred")
    if not claims:
        gaps.append("no behavior has been reconstructed")
    if target is not None:
        for cid, claim in claims.items():
            if claim.get("material") and cid not in by_claim:
                gaps.append(f"{cid}: target transfer decision missing")

    for uid, unknown in unknowns.items():
        if not text(unknown.get("question")) or type(unknown.get("blocking")) is not bool:
            errors.append(f"{uid}: question and explicit blocking boolean are required")
        refs = unknown.get("claim_ids")
        if not strings(refs) or any(cid not in claims for cid in refs):
            errors.append(f"{uid}: invalid claim_ids")
        if unknown.get("blocking"):
            gaps.append(f"{uid}: {unknown.get('question', 'unresolved question')}")
    if source.get("availability") == "recordings-only":
        gaps.append("recordings cannot establish unobserved interactions or runtime equivalence")
    return {"schema_version": 1,
            "status": "BLOCKED" if errors else ("PARTIAL" if gaps else "READY_FOR_SHAPING"),
            "source_fingerprint": source.get("fingerprint"),
            "verified_evidence_ids": sorted(verified), "errors": errors, "gaps": gaps,
            "implementation_authorized": False, "runtime_equivalence_proven": False,
            "note": "Readiness checks integrity and explicit decisions only; inspect evidence semantics and obtain normal spec/plan approval."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--artifact-root", type=Path)
    args = ap.parse_args()
    try:
        raw = args.input.read_bytes()
        data = json.loads(raw)
        result = inspect_contract(data, args.artifact_root or args.input.parent)
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    result["contract_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "READY_FOR_SHAPING" else 6


if __name__ == "__main__":
    raise SystemExit(main())
