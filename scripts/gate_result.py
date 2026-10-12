#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

STATUSES={"PASS","REPAIR","BLOCKED","NOT_APPLICABLE"}

def validate(data:dict)->list[str]:
    errors=[]
    if data.get("schema_version")!=1: errors.append("schema_version must be 1")
    if not isinstance(data.get("gate"),str) or not data.get("gate"): errors.append("gate is required")
    if data.get("status") not in STATUSES: errors.append("invalid status")
    if not isinstance(data.get("scope"),str): errors.append("scope must be a string")
    if not isinstance(data.get("findings"),list): errors.append("findings must be a list")
    if not isinstance(data.get("evidence"),list): errors.append("evidence must be a list")
    fp=data.get("input_fingerprint")
    if fp is not None and not isinstance(fp,str): errors.append("input_fingerprint must be string|null")
    if "details" in data and not isinstance(data["details"],dict): errors.append("details must be an object")
    return errors

def load(path:str)->dict:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    errs=validate(data)
    if errs: raise SystemExit(f"{path}: "+"; ".join(errs))
    return data

def aggregate(plan:dict,results:list[dict])->dict:
    by_gate={r["gate"]:r for r in results}
    missing=[]
    repair=[]
    blocked=[]
    passed=[]
    na=[]
    for gate in plan.get("gates",[]):
        if gate.get("status")!="REQUIRED":
            continue
        name=gate["gate"]
        r=by_gate.get(name)
        if not r:
            missing.append(name); continue
        s=r["status"]
        if s=="PASS": passed.append(name)
        elif s=="REPAIR": repair.append(name)
        elif s=="BLOCKED": blocked.append(name)
        else: missing.append(name)
    if blocked or missing:
        overall="BLOCKED"
    elif repair:
        overall="REPAIR"
    else:
        overall="PASS"
    for r in results:
        if r["status"]=="NOT_APPLICABLE": na.append(r["gate"])
    return {
        "schema_version":1,
        "status":overall,
        "quality_plan_id":plan.get("quality_plan_id"),
        "passed":sorted(set(passed)),
        "repair":sorted(set(repair)),
        "blocked":sorted(set(blocked)),
        "missing_required":sorted(set(missing)),
        "not_applicable":sorted(set(na)),
    }

def self_test()->None:
    good={"schema_version":1,"gate":"A11Y_GATE","status":"PASS","scope":"settings","findings":[],"evidence":[]}
    assert validate(good)==[]
    bad={**good,"status":"MAYBE"}
    assert validate(bad)
    plan={"quality_plan_id":"x","gates":[
        {"gate":"A11Y_GATE","status":"REQUIRED"},
        {"gate":"PERF_GATE","status":"NOT_APPLICABLE"},
    ]}
    assert aggregate(plan,[good])["status"]=="PASS"
    repair={**good,"status":"REPAIR"}
    assert aggregate(plan,[repair])["status"]=="REPAIR"
    assert aggregate(plan,[])["status"]=="BLOCKED"
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"gate.json"; p.write_text(json.dumps(good))
        assert load(str(p))["gate"]=="A11Y_GATE"
    print("PASS: gate-result self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Validate and aggregate normalized Gearbox gate results.")
    sp=ap.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("validate"); a.add_argument("file")
    a=sp.add_parser("aggregate"); a.add_argument("--plan",required=True); a.add_argument("--result",action="append",default=[])
    sp.add_parser("self-test")
    args=ap.parse_args()
    if args.cmd=="self-test":
        self_test(); return 0
    if args.cmd=="validate":
        data=load(args.file); print(json.dumps({"valid":True,"gate":data["gate"],"status":data["status"]},indent=2)); return 0
    plan=json.loads(Path(args.plan).read_text(encoding="utf-8"))
    results=[load(p) for p in args.result]
    print(json.dumps(aggregate(plan,results),indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
