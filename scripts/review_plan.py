#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"
RISK_RANK={"low":0,"medium":1,"high":2,"critical":3}

def load_registry()->dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def compile_review_plan(quality_plan:dict,risk:str,task_kind:str|None)->dict:
    reg=load_registry()
    policy=reg.get("review_fusion",{})
    required=[g for g in quality_plan.get("gates",[]) if g.get("status")=="REQUIRED"]
    by_name={g["gate"]:g for g in required}
    remaining=set(by_name)
    packs=[]
    allowed=(
        policy.get("enabled",False)
        and risk in RISK_RANK
        and RISK_RANK[risk] <= RISK_RANK.get(policy.get("max_risk","medium"),1)
        and quality_plan.get("quality_profile") in policy.get("allowed_profiles",[])
        and task_kind not in set(policy.get("excluded_task_kinds",[]))
    )
    if allowed:
        for cfg in policy.get("packs",[]):
            members=[g for g in cfg.get("gates",[]) if g in remaining]
            group=cfg.get("require_shared_probe_group")
            if group:
                members=[g for g in members if by_name[g].get("probe_group")==group]
            min_members=int(cfg.get("min_members",2))
            max_members=int(cfg.get("max_members",len(members) or 1))
            members=members[:max_members]
            if len(members)>=min_members:
                packs.append({
                    "kind":"fused-gates",
                    "id":cfg["id"],
                    "gates":members,
                    "provider":cfg["provider"],
                    "model":cfg["model"],
                    "effort":cfg["effort"],
                    "agent":cfg["agent"],
                    "shared_probe_group":group,
                    "independent_judgment":False,
                    "output_contract":"separate normalized gate envelopes per gate",
                })
                remaining.difference_update(members)

    for gate in sorted(remaining):
        g=by_name[gate]
        packs.append({
            "kind":"single-gate",
            "id":gate.lower(),
            "gates":[gate],
            "skill":g.get("skill"),
            "shared_probe_group":g.get("probe_group"),
            "independent_judgment":True,
        })
    return {
        "schema_version":1,
        "quality_plan_id":quality_plan.get("quality_plan_id"),
        "risk":risk,
        "task_kind":task_kind,
        "fusion_allowed":allowed,
        "dispatches":packs,
        "required_gate_count":len(required),
        "dispatch_count":len(packs),
        "dispatches_saved":max(0,len(required)-len(packs)),
    }

def self_test():
    qp={
      "quality_plan_id":"x","quality_profile":"standard",
      "gates":[
        {"gate":"SLOP_GATE","status":"REQUIRED","probe_group":"experience","skill":"web-design"},
        {"gate":"INTERACTION_GATE","status":"REQUIRED","probe_group":"experience","skill":"web-design"},
        {"gate":"A11Y_GATE","status":"REQUIRED","probe_group":"experience","skill":"a11y-audit"},
        {"gate":"PERF_GATE","status":"REQUIRED","probe_group":"experience","skill":"experience-perf"},
      ]
    }
    p=compile_review_plan(qp,"medium","web-design")
    fused=[x for x in p["dispatches"] if x["kind"]=="fused-gates"]
    assert len(fused)==1 and set(fused[0]["gates"])=={"SLOP_GATE","INTERACTION_GATE","A11Y_GATE"}
    assert any(x["gates"]==["PERF_GATE"] for x in p["dispatches"])
    assert p["dispatches_saved"]==2
    p2=compile_review_plan(qp,"high","web-design")
    assert all(x["kind"]=="single-gate" for x in p2["dispatches"])
    p3=compile_review_plan(qp,"low","creative-web")
    assert all(x["kind"]=="single-gate" for x in p3["dispatches"])
    print("PASS: review-plan self-test")

def main():
    ap=argparse.ArgumentParser(description="Compile controlled Gearbox quality-review fusion without collapsing gate semantics.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--quality-plan")
    ap.add_argument("--risk",choices=sorted(RISK_RANK),default="medium")
    ap.add_argument("--task-kind")
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.quality_plan:ap.error("--quality-plan is required")
    qp=json.loads(Path(args.quality_plan).read_text(encoding="utf-8"))
    result=compile_review_plan(qp,args.risk,args.task_kind);text=json.dumps(result,indent=2)+"\n"
    if args.output:Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="");return 0

if __name__=="__main__":
    raise SystemExit(main())
