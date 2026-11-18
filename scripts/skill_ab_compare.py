#!/usr/bin/env python3
"""Validate offline skill A/B evidence. Never invokes a model or trusts prose as correctness."""
from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path

FIELDS = {"arm", "provider", "model", "effort", "scenario", "repeat", "pass",
          "negative_control", "artifacts_verified", "isolation", "evidence"}

def compare(report: dict) -> dict:
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ValueError("schema_version must equal 1")
    baseline, candidate = report.get("baseline_sha"), report.get("candidate_sha")
    if not all(isinstance(s, str) and len(s) == 40 and all(c in "0123456789abcdefABCDEF" for c in s) for s in (baseline, candidate)) or baseline == candidate:
        raise ValueError("baseline_sha and candidate_sha must be distinct full Git SHAs")
    observations = report.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("observations must be a nonempty list")
    groups = defaultdict(dict)
    for row in observations:
        if not isinstance(row, dict) or not FIELDS <= row.keys():
            raise ValueError("observation missing fields")
        arm = row["arm"]
        if arm not in ("baseline", "candidate") or row["provider"] not in ("codex", "claude"):
            raise ValueError("invalid arm/provider")
        if not all(isinstance(row[k], str) and row[k] for k in ("model", "effort", "scenario", "isolation", "evidence")):
            raise ValueError("model/effort/scenario/isolation/evidence must be nonempty strings")
        if not isinstance(row["repeat"], int) or isinstance(row["repeat"], bool) or row["repeat"] < 1:
            raise ValueError("repeat must be a positive integer")
        if not all(type(row[k]) is bool for k in ("pass", "negative_control", "artifacts_verified")):
            raise ValueError("pass, negative_control and artifacts_verified must be booleans")
        key = tuple(row[k] for k in ("provider", "model", "effort", "scenario"))
        sample = (arm, row["repeat"])
        if sample in groups[key]:
            raise ValueError(f"duplicate sample: {key} {sample}")
        groups[key][sample] = row
    results = []
    for key, samples in sorted(groups.items()):
        base_ids = {n for (arm, n) in samples if arm == "baseline"}
        cand_ids = {n for (arm, n) in samples if arm == "candidate"}
        if not base_ids or base_ids != cand_ids:
            raise ValueError(f"unpaired baseline/candidate repeats: {key}")
        if len(base_ids) < 3:
            raise ValueError(f"at least 3 paired repeats required: {key}")
        rows = [samples[("baseline", n)] for n in sorted(base_ids)]
        candidates = [samples[("candidate", n)] for n in sorted(cand_ids)]
        if any(b["negative_control"] != c["negative_control"] for b, c in zip(rows, candidates)):
            raise ValueError(f"negative-control mismatch: {key}")
        def ok(r):
            return r["pass"] and r["artifacts_verified"] and r["isolation"] == "private-home-and-provider-config"
        bpass, cpass = sum(map(ok, rows)), sum(map(ok, candidates))
        negative_regression = any(b["negative_control"] and ok(b) and not ok(c)
                                  for b, c in zip(rows, candidates))
        results.append({"provider": key[0], "model": key[1], "effort": key[2],
                        "scenario": key[3], "samples_per_arm": len(rows),
                        "baseline_pass": bpass, "candidate_pass": cpass,
                        "delta_pass": cpass - bpass, "negative_control_regression": negative_regression})
    return {"results": results,
            "recommendation": "REJECT" if any(x["delta_pass"] < 0 or x["negative_control_regression"] for x in results)
               else "INCONCLUSIVE_OR_MANUAL_REVIEW",
            "warning": "Independent semantic/artifact verification and held-out results are required before KEEP."}

def self_test():
    sha0, sha1 = "a" * 40, "b" * 40
    rows = []
    for n in range(1, 4):
        for arm in ("baseline", "candidate"):
            rows.append(dict(arm=arm, provider="codex", model="gpt-6.2-sol",
                             effort="medium", scenario="safe", repeat=n, pass=True,
                             negative_control=True, artifacts_verified=True,
                             isolation="private-home-and-provider-config", evidence=f"receipt-{arm}-{n}.json"))
    data = dict(schema_version=1, baseline_sha=sha0, candidate_sha=sha1, observations=rows)
    assert compare(data)["results"][0]["delta_pass"] == 0
    rows[-1]["pass"] = False
    assert compare(data)["recommendation"] == "REJECT"
    rows[-1]["pass"] = True
    del rows[-1]
    try:
        compare(data)
    except ValueError:
        pass
    else:
        raise AssertionError("unpaired samples accepted")
    print("PASS: skill-ab-compare self-test")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.report is None:
        p.error("--report is required")
    try:
        result = compare(json.loads(args.report.read_text(encoding="utf-8")))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    print(json.dumps(result, indent=2))
    return 1 if result["recommendation"] == "REJECT" else 0

if __name__ == "__main__":
    raise SystemExit(main())
