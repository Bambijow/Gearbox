#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"
ORDER=["dev","standard","release","critical"]
RISK_RANK={"low":0,"medium":1,"high":2,"critical":3}

def load_registry()->dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def max_profile(a:str,b:str)->str:
    return ORDER[max(ORDER.index(a),ORDER.index(b))]

def step(profile:str,n:int)->str:
    return ORDER[min(len(ORDER)-1,ORDER.index(profile)+max(0,n))]

def adapt(quality_plan:dict,risk:str,repair_cycles:int,silent_finding:bool,integration_repair:bool,group_signals:dict|None=None)->dict:
    reg=load_registry()
    policy=reg.get("quality_depth",{})
    if policy.get("mode")!="escalate-only":
        return {"schema_version":1,"base_profile":quality_plan.get("quality_profile","standard"),"groups":quality_plan.get("probe_groups",[]),"reasons":["adaptive depth disabled"]}
    base=quality_plan.get("quality_profile","standard")
    if base not in ORDER:raise SystemExit(f"unknown base quality profile: {base}")
    target=base;reasons=[]
    if risk=="critical":
        target=max_profile(target,policy.get("critical_risk_profile","critical"));reasons.append("critical risk")
    elif risk=="high":
        target=max_profile(target,policy.get("high_risk_min_profile","release"));reasons.append("high risk")
    if silent_finding:
        target=max_profile(target,policy.get("silent_finding_min_profile","release"));reasons.append("silent finding")
    threshold=int(policy.get("repair_cycle_threshold",2))
    if repair_cycles>=threshold:
        target=step(target,1);reasons.append(f"repair cycles {repair_cycles}>={threshold}")
    if integration_repair:
        target=step(target,int(policy.get("integration_repair_step",1)));reasons.append("integration repair")
    profiles=reg["quality_profiles"]
    groups=[]
    gs=group_signals or {}
    for group in quality_plan.get("probe_groups",[]):
        gp=target;greasons=list(reasons)
        local=gs.get(group.get("group"),{})
        local_risk=local.get("risk")
        if local_risk=="critical":
            gp=max_profile(gp,policy.get("critical_risk_profile","critical"));greasons.append("group critical risk")
        elif local_risk=="high":
            gp=max_profile(gp,policy.get("high_risk_min_profile","release"));greasons.append("group high risk")
        if local.get("silent_finding"):
            gp=max_profile(gp,policy.get("silent_finding_min_profile","release"));greasons.append("group silent finding")
        lrep=int(local.get("repair_cycles",0))
        if lrep>=threshold:
            gp=step(gp,1);greasons.append(f"group repairs {lrep}>={threshold}")
        cfg=profiles[gp]
        groups.append({
            **group,
            "base_profile":base,
            "effective_profile":gp,
            "depth":cfg["probe_depth"],
            "state_matrix":cfg["state_matrix"],
            "review_depth":cfg["review_depth"],
            "adaptation_reasons":greasons,
        })
    return {
        "schema_version":1,
        "quality_plan_id":quality_plan.get("quality_plan_id"),
        "base_profile":base,
        "effective_profile":target,
        "required_gates_unchanged":True,
        "groups":groups,
        "reasons":reasons,
    }

def self_test():
    qp={"quality_plan_id":"x","quality_profile":"standard","gates":[{"gate":"A11Y_GATE","status":"REQUIRED"}],"probe_groups":[{"group":"experience","gates":["A11Y_GATE"],"depth":"representative","state_matrix":"material-states"}]}
    a=adapt(qp,"medium",0,False,False)
    assert a["effective_profile"]=="standard" and a["required_gates_unchanged"]
    b=adapt(qp,"medium",2,False,False)
    assert b["effective_profile"]=="release"
    c=adapt(qp,"critical",0,False,False)
    assert c["effective_profile"]=="critical"
    d=adapt(qp,"low",0,True,False)
    assert d["effective_profile"]=="release"
    assert qp["gates"][0]["status"]=="REQUIRED"
    print("PASS: quality-depth self-test")

def main():
    ap=argparse.ArgumentParser(description="Escalate Gearbox quality evidence depth from runtime risk signals without removing required gates.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--quality-plan")
    ap.add_argument("--risk",choices=sorted(RISK_RANK),default="medium")
    ap.add_argument("--repair-cycles",type=int,default=0)
    ap.add_argument("--silent-finding",action="store_true")
    ap.add_argument("--integration-repair",action="store_true")
    ap.add_argument("--group-signals-json",default="{}")
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.quality_plan:ap.error("--quality-plan is required")
    qp=json.loads(Path(args.quality_plan).read_text(encoding="utf-8"))
    result=adapt(qp,args.risk,args.repair_cycles,args.silent_finding,args.integration_repair,json.loads(args.group_signals_json))
    text=json.dumps(result,indent=2)+"\n"
    if args.output:Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="");return 0

if __name__=="__main__":
    raise SystemExit(main())
