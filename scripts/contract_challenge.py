#!/usr/bin/env python3
"""Validate adversarial behavior-transfer reviews with bound, hash-checked evidence.

Review completion is not a runtime-equivalence certificate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from gate_result import SHA256, verify_proofs


def check(contract, report, artifact_root: Path):
    errors, gaps, counterexamples = [], [], []
    if not isinstance(contract, dict) or not isinstance(report, dict):
        return {"status": "BLOCKED", "errors": ["object inputs required"], "gaps": []}
    if report.get("schema_version") != 1:
        errors.append("challenge schema_version must be 1")
    source = contract.get("source", {})
    if report.get("reference_fingerprint") != source.get("fingerprint") or not report.get("reference_fingerprint"):
        errors.append("reference fingerprint mismatch")
    target = contract.get("target") or {}
    if report.get("target_revision") != target.get("revision") or not report.get("target_revision"):
        errors.append("target revision mismatch")
    claims = {c["id"]: c for c in contract.get("claims", []) if isinstance(c, dict) and isinstance(c.get("id"), str)}
    material = {cid for cid, c in claims.items() if c.get("material") is True}
    observations = report.get("challenges", [])
    if not isinstance(observations, list):
        errors.append("challenges must be list")
        observations = []
    seen = set()
    for entry in observations:
        if not isinstance(entry, dict) or not isinstance(entry.get("claim_id"), str):
            errors.append("challenge missing claim_id")
            continue
        cid = entry["claim_id"]
        if cid in seen or cid not in claims:
            errors.append(f"duplicate/unknown challenge for {cid}")
            continue
        seen.add(cid)
        if not isinstance(entry.get("adversarial_input"), str) or not entry["adversarial_input"].strip():
            errors.append(f"{cid}: need discriminating adversarial input")
        verdict = entry.get("verdict")
        if verdict not in {"COUNTEREXAMPLE", "NO_COUNTEREXAMPLE_OBSERVED", "UNKNOWN"}:
            errors.append(f"{cid}: invalid verdict")
        if verdict == "UNKNOWN":
            gaps.append(f"{cid}: reviewer could not verify")
            continue
        evidence = entry.get("evidence")
        if not isinstance(evidence, dict) or not isinstance(evidence.get("path"), str) or Path(evidence["path"]).is_absolute() or not isinstance(evidence.get("sha256"), str) or not SHA256.fullmatch(evidence["sha256"]):
            errors.append(f"{cid}: actual candidate run evidence required")
            continue
        problems = verify_proofs({"evidence": [{"kind": "test", **evidence}]},
                                 {"required_evidence_kinds": ["test"]}, artifact_root)
        errors.extend(f"{cid}: {why}" for why in problems)
        if verdict == "COUNTEREXAMPLE":
            counterexamples.append(cid)
    for cid in material - seen:
        gaps.append(f"{cid}: no adversarial challenge")
    return {"status": "BLOCKED" if errors else "REPAIR" if counterexamples else "GAPS" if gaps else "REVIEWED_NOT_PROVEN",
            "errors": errors, "gaps": sorted(gaps), "counterexample_claim_ids": sorted(counterexamples),
            "runtime_equivalence_proven": False,
            "note": "No counterexample observed is not proof of equivalence. Reviewer must check scenario/oracle semantics."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    try:
        raw = args.report.read_bytes()
        result = check(json.loads(args.contract.read_text(encoding="utf-8")), json.loads(raw), args.report.parent)
        result["report_sha256"] = hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError) as err:
        p.error(str(err))
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "REVIEWED_NOT_PROVEN" else 6


if __name__ == "__main__":
    raise SystemExit(main())
