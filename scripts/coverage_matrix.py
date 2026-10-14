#!/usr/bin/env python3
"""Compile coverage from run-bound, file-verified proof records (schema 2)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from gate_result import SHA256, verify_proofs

PASS = {"PASS", "PASSED", "SUCCESS", "OK"}
BLOCK = {"BLOCKED", "FAILED", "FAIL", "ERROR"}
PENDING = {"PENDING", "UNKNOWN", "RUNNING", "PARTIAL"}
BINDING = ("run_id", "scope", "input_fingerprint")


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _index(items, label, errors):
    result = {}
    if not isinstance(items, list):
        errors.append(f"{label} must be a list")
        return result
    for item in items:
        if not isinstance(item, dict) or not _text(item.get("id")):
            errors.append(f"{label} entries require a non-empty string id")
        elif item["id"] in result:
            errors.append(f"duplicate {label} id: {item['id']}")
        else:
            result[item["id"]] = item
    return result


def compile_matrix(data: dict, artifact_root: Path | None = None) -> dict:
    errors = []
    if not isinstance(data, dict):
        data = {}
        errors.append("coverage input must be an object")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 2:
        errors.append("coverage schema_version must be 2; legacy declarations are not verified proof")
    for key in BINDING:
        if not _text(data.get(key)):
            errors.append(f"coverage requires {key}")
    requirements = _index(data.get("requirements"), "requirements", errors)
    proofs = _index(data.get("proofs", []), "proofs", errors)
    if not requirements and not _text(data.get("not_applicable_reason")):
        errors.append("empty requirements need an explicit not_applicable_reason")
    failure_modes = data.get("failure_modes", [])
    if not isinstance(failure_modes, list) or not all(_text(x) for x in failure_modes):
        errors.append("failure_modes must be a list of non-empty strings")
        failure_modes = []

    verified = set()
    proof_errors = {}
    for pid, proof in proofs.items():
        reasons = []
        status = str(proof.get("status", "")).upper()
        if status not in PASS | BLOCK | PENDING:
            reasons.append("unrecognized proof status")
        if status in PASS:
            for key in BINDING:
                if not _text(proof.get(key)) or proof[key] != data.get(key):
                    reasons.append(f"{key} mismatch or missing")
            code = proof.get("exit_code")
            if code is not None and (type(code) is not int or code != 0):
                reasons.append("PASS contradicts execution exit_code")
            if not _text(proof.get("kind")) or not _text(proof.get("pointer")):
                reasons.append("proof requires kind and pointer")
            digest = proof.get("sha256")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                reasons.append("proof requires an actual SHA-256 digest")
            if not reasons:
                # Same confinement and full-file hashing as the quality-gate layer.
                reasons.extend(verify_proofs({"evidence": [{"kind": proof["kind"],
                    "path": proof["pointer"], "sha256": digest}]},
                    {"required_evidence_kinds": [proof["kind"]]}, artifact_root))
            if not reasons:
                verified.add(pid)
        proof_errors[pid] = reasons

    rows, missing, blocked, partial = [], [], [], []
    used_verified = set()
    for rid, req in requirements.items():
        kinds, refs = req.get("required_kinds"), req.get("proof_ids", [])
        row_errors = []
        if not isinstance(kinds, list) or not all(_text(x) for x in kinds):
            row_errors.append("required_kinds must be an explicit string list")
            kinds = []
        if not isinstance(refs, list) or not all(_text(x) for x in refs):
            row_errors.append("proof_ids must be a string list")
            refs = []
        na = not kinds and _text(req.get("not_applicable_reason")) and not refs
        if not kinds and not na:
            row_errors.append("empty required_kinds need non-applicability with no proof references")
        found, passing_kinds = [], set()
        for pid in refs:
            proof = proofs.get(pid)
            if proof is None:
                continue
            status = str(proof.get("status", "")).upper()
            found.append({"id": pid, "kind": proof.get("kind"), "status": status,
                          "pointer": proof.get("pointer")})
            row_errors.extend(f"{pid}: {reason}" for reason in proof_errors[pid])
            if status in BLOCK:
                row_errors.append(f"{pid}: failed or blocked proof")
            if pid in verified:
                passing_kinds.add(proof["kind"])
                used_verified.add(pid)
        missing_kinds = sorted(set(kinds) - passing_kinds)
        unresolved = [pid for pid in refs if pid not in verified]
        if row_errors:
            status = "BLOCKED"
            blocked.append(rid)
        elif na:
            status = "NOT_APPLICABLE"
        elif not found or missing_kinds or unresolved:
            status = "MISSING" if not found else "PARTIAL"
            (missing if status == "MISSING" else partial).append(rid)
        else:
            status = "COVERED"
        rows.append({"requirement_id": rid, "critical": bool(req.get("critical", False)),
                     "status": status, "required_kinds": sorted(set(kinds)),
                     "missing_kinds": missing_kinds, "unresolved_proof_ids": unresolved,
                     "proofs": found, "errors": row_errors,
                     "not_applicable_reason": req.get("not_applicable_reason") if na else None})
    uncovered = [mode for mode in failure_modes if not any(
        proofs[pid].get("covers_failure_mode") == mode for pid in used_verified)]
    overall = "BLOCKED" if errors or blocked else ("GAPS" if missing or partial or uncovered else "COMPLETE")
    return {"schema_version": 2, "status": overall, "requirements": rows,
            "missing": missing, "partial": partial, "blocked": blocked,
            "uncovered_failure_modes": uncovered, "errors": errors,
            **{key: data.get(key) for key in BINDING}}


def self_test():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "test.txt").write_text("1 test passed", encoding="utf-8")
        binding = {"run_id": "r1", "scope": "feature", "input_fingerprint": "sha:abc"}
        data = {"schema_version": 2, **binding,
                "requirements": [{"id": "R1", "required_kinds": ["test"], "proof_ids": ["T1"]}],
                "proofs": [{"id": "T1", "kind": "test", "status": "PASS", **binding,
                            "pointer": "test.txt", "sha256": hashlib.sha256((root / "test.txt").read_bytes()).hexdigest()}]}
        assert compile_matrix(data, root)["status"] == "COMPLETE"
        data["proofs"][0]["status"] = "PENDING"
        assert compile_matrix(data, root)["status"] == "GAPS"
    print("PASS: coverage-matrix self-test")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--artifact-root", type=Path)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.input:
        ap.error("--input is required")
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        result = compile_matrix(data, args.artifact_root or args.input.parent)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "COMPLETE" else 6


if __name__ == "__main__":
    raise SystemExit(main())
