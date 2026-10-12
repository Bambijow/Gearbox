#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

PASS={"PASS","PASSED","SUCCESS","OK"}
BLOCK={"BLOCKED","FAILED","FAIL","ERROR"}

def compile_matrix(data:dict)->dict:
    proofs={str(p["id"]):p for p in data.get("proofs",[])}
    rows=[];missing=[];blocked=[];partial=[]
    for req in data.get("requirements",[]):
        rid=str(req["id"]); required_kinds=set(req.get("required_kinds",[])); refs=req.get("proof_ids",[])
        found=[];passing_kinds=set();bad=[]
        for pid in refs:
            p=proofs.get(str(pid))
            if not p: continue
            status=str(p.get("status","")).upper()
            found.append({"id":str(pid),"kind":p.get("kind"),"status":status,"pointer":p.get("pointer")})
            if status in PASS: passing_kinds.add(str(p.get("kind")))
            elif status in BLOCK: bad.append(str(pid))
        missing_kinds=sorted(required_kinds-passing_kinds)
        if bad:
            status="BLOCKED";blocked.append(rid)
        elif not found or missing_kinds:
            status="MISSING" if not found else "PARTIAL"
            (missing if status=="MISSING" else partial).append(rid)
        else:
            status="COVERED"
        rows.append({
            "requirement_id":rid,
            "critical":bool(req.get("critical",False)),
            "status":status,
            "required_kinds":sorted(required_kinds),
            "missing_kinds":missing_kinds,
            "proofs":found,
        })
    overall="BLOCKED" if blocked else ("GAPS" if missing or partial else "COMPLETE")
    return {
        "schema_version":1,"status":overall,"requirements":rows,
        "missing":missing,"partial":partial,"blocked":blocked,
        "uncovered_failure_modes":[
            str(x) for x in data.get("failure_modes",[]) if not any(
                str(x)==str(p.get("covers_failure_mode")) and str(p.get("status","")).upper() in PASS
                for p in data.get("proofs",[])
            )
        ],
    }

def self_test():
    d={
      "requirements":[
        {"id":"R1","required_kinds":["test","a11y"],"proof_ids":["T1","A1"]},
        {"id":"R2","required_kinds":["test"],"proof_ids":["T2"]},
      ],
      "proofs":[
        {"id":"T1","kind":"test","status":"PASS"},
        {"id":"A1","kind":"a11y","status":"PASS"},
        {"id":"T2","kind":"test","status":"FAIL"},
      ],
      "failure_modes":["silent retry duplication"],
    }
    r=compile_matrix(d)
    assert r["requirements"][0]["status"]=="COVERED"
    assert r["requirements"][1]["status"]=="BLOCKED"
    assert r["status"]=="BLOCKED" and r["uncovered_failure_modes"]==["silent retry duplication"]
    print("PASS: coverage-matrix self-test")

def main():
    ap=argparse.ArgumentParser(description="Compile requirement-to-proof coverage for Gearbox final review and completion.")
    ap.add_argument("--self-test",action="store_true");ap.add_argument("--input");ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.input:ap.error("--input is required")
    data=json.loads(Path(args.input).read_text(encoding="utf-8"));result=compile_matrix(data);text=json.dumps(result,indent=2)+"\n"
    if args.output:Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="");return 0

if __name__=="__main__":
    raise SystemExit(main())
