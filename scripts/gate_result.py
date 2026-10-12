#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

SCHEMA_VERSION = 2
STATUSES = {"PASS", "REPAIR", "BLOCKED", "NOT_APPLICABLE"}
BINDING_KEYS = ("run_id", "quality_plan_id", "scope", "input_fingerprint")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate(data: dict) -> list[str]:
    """Validate an envelope without trusting a model's declared PASS."""
    if not isinstance(data, dict):
        return ["gate result must be an object"]
    errors = []
    if type(data.get("schema_version")) is not int or data["schema_version"] != SCHEMA_VERSION:
        errors.append("schema_version must be 2; legacy results must be revalidated, not relabelled")
    for key in ("gate", *BINDING_KEYS):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} must be a non-empty string")
    status = data.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        errors.append("invalid status")
    for key in ("findings", "evidence"):
        if not isinstance(data.get(key), list) or not all(isinstance(x, dict) for x in data[key]):
            errors.append(f"{key} must be a list of objects")
    if "details" in data and not isinstance(data["details"], dict):
        errors.append("details must be an object")
    if status == "PASS":
        if not data.get("evidence"):
            errors.append("PASS requires concrete evidence")
        code = data.get("exit_code")
        if code is not None and (type(code) is not int or code != 0):
            errors.append("PASS contradicts execution exit_code")
    if isinstance(data.get("evidence"), list):
        for i, proof in enumerate(data["evidence"]):
            if not isinstance(proof, dict):
                continue
            for key in ("kind", "path"):
                if not isinstance(proof.get(key), str) or not proof[key].strip():
                    errors.append(f"evidence[{i}].{key} is required")
            if not isinstance(proof.get("sha256"), str) or not SHA256.fullmatch(proof["sha256"]):
                errors.append(f"evidence[{i}].sha256 must be a SHA-256 digest")
    return errors


def load(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        raise SystemExit(f"{path}: " + "; ".join(errors))
    return data


def verify_proofs(result: dict, gate: dict, artifact_root: Path | None) -> list[str]:
    errors = []
    kinds = {proof["kind"] for proof in result["evidence"]}
    for kind in gate.get("required_evidence_kinds", []):
        if kind not in kinds:
            errors.append(f"required evidence kind missing: {kind}")
    if artifact_root is None:
        return errors + ["artifact root is required to verify PASS evidence"]
    root = artifact_root.resolve()
    for proof in result["evidence"]:
        raw = Path(proof["path"])
        try:
            path = (root / raw).resolve()
            path.relative_to(root)
            if not path.is_file():
                errors.append(f"evidence file missing: {proof['path']}")
                continue
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != proof["sha256"]:
                errors.append(f"evidence hash mismatch: {proof['path']}")
        except (OSError, ValueError, RuntimeError):
            errors.append(f"evidence path inaccessible or outside run: {proof['path']}")
    return errors


def aggregate(plan: dict, results: list[dict], artifact_root: Path | None = None) -> dict:
    """Fail closed on stale identities, duplicate verdicts or unverifiable files."""
    plan_errors = []
    if not isinstance(plan, dict):
        plan = {}
        plan_errors.append("quality plan must be an object")
    for key in BINDING_KEYS:
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            plan_errors.append(f"bound quality plan requires {key}")
    if plan.get("gate_contract_version") != SCHEMA_VERSION:
        plan_errors.append("quality plan requires gate_contract_version 2")
    canonical = {key: value for key, value in plan.items() if key != "quality_plan_id"}
    expected_id = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if plan.get("quality_plan_id") != expected_id:
        plan_errors.append("quality plan content does not match quality_plan_id; recompile")
    gates = plan.get("gates")
    if not isinstance(gates, list):
        gates = []
        plan_errors.append("quality plan gates must be a list")
    expected = {}
    for gate in gates:
        if not isinstance(gate, dict) or not isinstance(gate.get("gate"), str):
            plan_errors.append("invalid gate in quality plan")
            continue
        name = gate["gate"]
        if name in expected:
            plan_errors.append(f"duplicate gate in quality plan: {name}")
        expected[name] = gate
        if not isinstance(gate.get("status"), str) or gate["status"] not in {"REQUIRED", "NOT_APPLICABLE"}:
            plan_errors.append(f"invalid requiredness for {name}")
        needs = gate.get("required_evidence_kinds")
        if not isinstance(needs, list) or not all(isinstance(x, str) for x in needs):
            plan_errors.append(f"{name}: required_evidence_kinds must be explicit")

    by_gate = {}
    invalid = []
    invalid_names = set()
    for index, result in enumerate(results):
        errors = validate(result)
        name = result.get("gate") if isinstance(result, dict) else None
        if not isinstance(name, str):
            name = f"result[{index}]"
        if name not in expected:
            errors.append("unexpected gate")
        if name in by_gate:
            errors.append("duplicate gate results; select one current verdict explicitly")
        if isinstance(result, dict):
            for key in BINDING_KEYS:
                if result.get(key) != plan.get(key):
                    errors.append(f"{key} mismatch")
        if not errors and result["status"] == "PASS" and not plan_errors:
            errors.extend(verify_proofs(result, expected[name], artifact_root))
        by_gate[name] = result
        if errors:
            invalid.append({"gate": name, "reasons": errors})
            invalid_names.add(name)

    missing = []; repair = []; blocked = []; passed = []; na = []
    for name, gate in expected.items():
        if gate.get("status") != "REQUIRED":
            if name not in invalid_names and by_gate.get(name, {}).get("status") == "NOT_APPLICABLE":
                na.append(name)
            continue
        if name in invalid_names:
            blocked.append(name)
        elif name not in by_gate:
            missing.append(name)
        else:
            status = by_gate[name]["status"]
            if status == "PASS" and not plan_errors:
                passed.append(name)
            elif status == "REPAIR":
                repair.append(name)
            else:
                blocked.append(name)
    overall = "BLOCKED" if plan_errors or invalid or blocked or missing else "REPAIR" if repair else "PASS"
    return {
        "schema_version": SCHEMA_VERSION, "status": overall,
        "quality_plan_id": plan.get("quality_plan_id"), "run_id": plan.get("run_id"),
        "passed": sorted(passed), "repair": sorted(repair), "blocked": sorted(blocked),
        "missing_required": sorted(missing), "not_applicable": sorted(na),
        "plan_errors": plan_errors, "invalid_results": invalid,
    }


def self_test() -> None:
    from quality_plan import compile_plan
    plan = compile_plan("audio-design", "standard", [], [], [], {}, run_id="test", scope="audio", input_fingerprint="sha:abc")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        proof = root / "playback.txt"
        proof.write_text("checked")
        good = {"schema_version": 2, "gate": "AUDIO_GATE", "status": "PASS", "run_id": "test",
                "quality_plan_id": plan["quality_plan_id"], "scope": "audio", "input_fingerprint": "sha:abc",
                "findings": [], "evidence": [{"kind": "playback", "path": proof.name,
                                             "sha256": hashlib.sha256(proof.read_bytes()).hexdigest()}]}
        assert validate(good) == []
        assert aggregate(plan, [good], root)["status"] == "PASS"
        assert aggregate(plan, [{**good, "status": "REPAIR"}], root)["status"] == "REPAIR"
        assert aggregate(plan, [], root)["status"] == "BLOCKED"
        assert aggregate(plan, [good, good], root)["status"] == "BLOCKED"
        proof.write_text("changed")
        assert aggregate(plan, [good], root)["status"] == "BLOCKED"
    print("PASS: gate-result self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate and aggregate run-bound Gearbox gate results with hashed evidence.")
    sp = ap.add_subparsers(dest="cmd", required=True)
    command = sp.add_parser("validate"); command.add_argument("file")
    command = sp.add_parser("aggregate")
    command.add_argument("--plan", required=True)
    command.add_argument("--result", action="append", default=[])
    command.add_argument("--artifact-root", type=Path, help="Run directory containing evidence; defaults to plan directory")
    sp.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    try:
        if args.cmd == "validate":
            data = load(args.file)
            print(json.dumps({"valid": True, "gate": data["gate"], "status": data["status"]}, indent=2))
            return 0
        plan_path = Path(args.plan)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        results = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.result]
        result = aggregate(plan, results, args.artifact_root or plan_path.resolve().parent)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, indent=2))
        return 6
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 6


if __name__ == "__main__":
    raise SystemExit(main())
