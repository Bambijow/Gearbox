#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"

def registry_policy()->dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8")).get("adaptive_routing",{})

def collect(runs_root:Path,task_kind:str)->dict[tuple, list[dict]]:
    groups=defaultdict(list)
    for p in runs_root.glob("*/usage.json"):
        try:data=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        for item in data.get("items",[]):
            if item.get("estimated"):continue
            if item.get("task_kind")!=task_kind:continue
            if item.get("outcome") not in {"success","failure"}:continue
            key=(item.get("provider"),item.get("model"),item.get("effort"))
            groups[key].append(item)
    return groups

def metrics(items:list[dict])->dict:
    success=sum(1 for x in items if x.get("outcome")=="success")
    samples=len(items)
    token_samples=[
        int(x.get("input_tokens",0))+int(x.get("output_tokens",0))
        for x in items if isinstance(x.get("input_tokens"),int) or isinstance(x.get("output_tokens"),int)
    ]
    costs=[float(x["reported_cost_usd"]) for x in items if isinstance(x.get("reported_cost_usd"),(int,float))]
    return {
        "samples":samples,
        "successes":success,
        "success_rate":success/samples if samples else None,
        "median_total_tokens":statistics.median(token_samples) if token_samples else None,
        "median_reported_cost_usd":statistics.median(costs) if costs else None,
    }

def advise(runs_root:Path,task_kind:str,surfaces:list[str],registered_specialist:bool)->dict:
    policy=registry_policy()
    groups=collect(runs_root,task_kind)
    rows=[]
    for key,items in groups.items():
        m=metrics(items)
        rows.append({"provider":key[0],"model":key[1],"effort":key[2],**m})
    rows.sort(key=lambda x:(-(x["samples"]),-(x["success_rate"] or 0),x["median_total_tokens"] if x["median_total_tokens"] is not None else 10**18))
    safety=sorted(set(surfaces)&set(policy.get("safety_ceiling_surfaces",[])))
    if registered_specialist and policy.get("never_override_registered_specialist_routes",True):
        mode="observe-only";reason="registered specialist route is pinned"
    elif safety:
        mode="observe-only";reason="safety ceiling surface: "+",".join(safety)
    else:
        mode="advisory";reason="telemetry may advise same-safety-level economics only"

    eligible=[]
    min_samples=int(policy.get("min_samples",5));min_rate=float(policy.get("min_success_rate",0.8))
    for row in rows:
        if row["samples"]>=min_samples and (row["success_rate"] or 0)>=min_rate:
            eligible.append(row)
    eligible.sort(key=lambda x:(
        x["median_total_tokens"] if x["median_total_tokens"] is not None else 10**18,
        x["median_reported_cost_usd"] if x["median_reported_cost_usd"] is not None else 10**18,
        -(x["success_rate"] or 0)
    ))
    recommendation=eligible[0] if eligible and mode=="advisory" else None
    return {
        "schema_version":1,"task_kind":task_kind,"mode":mode,"reason":reason,
        "min_samples":min_samples,"min_success_rate":min_rate,
        "routes":rows,"recommended_route":recommendation,
        "guardrails":{
            "never_promote_to_frontier":bool(policy.get("never_promote_to_frontier_from_telemetry",True)),
            "registered_specialist_override":False,
            "safety_surfaces":safety,
        }
    }

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for i in range(6):
            run=root/f"r{i}";run.mkdir()
            items=[
                {"dispatch_id":f"a{i}","task_kind":"feature","provider":"codex","model":"gpt-6.1-sol","effort":"medium","outcome":"success","input_tokens":100,"output_tokens":20,"estimated":False},
                {"dispatch_id":f"b{i}","task_kind":"feature","provider":"claude","model":"sonnet","effort":"medium","outcome":"success","input_tokens":180,"output_tokens":30,"estimated":False},
            ]
            (run/"usage.json").write_text(json.dumps({"schema_version":2,"items":items}))
        a=advise(root,"feature",[],False)
        assert a["mode"]=="advisory" and a["recommended_route"]["provider"]=="codex"
        b=advise(root,"feature",["security_boundary"],False)
        assert b["mode"]=="observe-only" and b["recommended_route"] is None
        c=advise(root,"feature",[],True)
        assert c["mode"]=="observe-only"
    print("PASS: routing-advisor self-test")

def main():
    ap=argparse.ArgumentParser(description="Advise Gearbox routing economics from measured prior runs without overriding safety ceilings.")
    ap.add_argument("--self-test",action="store_true");ap.add_argument("--runs-root",type=Path,default=Path(".gearbox/runs"));ap.add_argument("--task-kind");ap.add_argument("--surface",action="append",default=[]);ap.add_argument("--registered-specialist",action="store_true");ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.task_kind:ap.error("--task-kind is required")
    result=advise(args.runs_root,args.task_kind,args.surface,args.registered_specialist);text=json.dumps(result,indent=2)+"\n"
    if args.output:Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="");return 0

if __name__=="__main__":
    raise SystemExit(main())
