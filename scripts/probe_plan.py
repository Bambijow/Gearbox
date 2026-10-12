#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"

def compile_probe(quality_plan:dict)->dict:
    registry=json.loads(REGISTRY.read_text(encoding="utf-8"))
    needs_by_gate={name:set(rule.get("probe_needs",[])) for name,rule in registry["gates"].items()}
    groups=[]
    for group in quality_plan.get("probe_groups",[]):
        gates=group.get("gates",[])
        needs=set()
        gate_needs={}
        for gate in gates:
            n=needs_by_gate.get(gate,set())
            gate_needs[gate]=sorted(n)
            needs.update(n)
        groups.append({
            "group":group["group"],
            "depth":group.get("depth"),
            "state_matrix":group.get("state_matrix"),
            "gates":gates,
            "required_artifacts":sorted(needs),
            "gate_artifacts":gate_needs,
        })
    return {
        "schema_version":1,
        "quality_plan_id":quality_plan.get("quality_plan_id"),
        "quality_profile":quality_plan.get("quality_profile"),
        "probe_groups":groups,
    }

def self_test():
    qp={"quality_plan_id":"x","quality_profile":"standard","probe_groups":[
        {"group":"experience","depth":"representative","state_matrix":"material-states","gates":["A11Y_GATE","PERF_GATE","SLOP_GATE"]}
    ]}
    p=compile_probe(qp)
    needs=set(p["probe_groups"][0]["required_artifacts"])
    assert {"accessibility","interaction","performance","network","console","screenshot"}.issubset(needs)
    assert "playback" not in needs
    print("PASS: probe-plan self-test")

def main():
    ap=argparse.ArgumentParser(description="Compile the minimal artifact collection plan for required Gearbox gate groups.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--quality-plan")
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.quality_plan: ap.error("--quality-plan is required")
    qp=json.loads(Path(args.quality_plan).read_text(encoding="utf-8"))
    result=compile_probe(qp); text=json.dumps(result,indent=2)+"\n"
    if args.output: Path(args.output).write_text(text,encoding="utf-8")
    print(text,end=""); return 0

if __name__=="__main__":
    raise SystemExit(main())
