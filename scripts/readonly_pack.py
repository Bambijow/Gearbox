#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"

def load_policy()->dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8")).get("readonly_packing",{})

def pack(tasks:list[dict])->dict:
    policy=load_policy()
    allowed=set(policy.get("allowed_kinds",[]))
    max_members=max(1,int(policy.get("max_members",6)))
    groups=defaultdict(list)
    singles=[]
    for task in tasks:
        if not policy.get("enabled",False):
            singles.append(task);continue
        if task.get("kind") not in allowed:
            singles.append(task);continue
        if bool(task.get("independent_judgment",False)) and policy.get("forbid_independent_judgment",True):
            singles.append(task);continue
        context=task.get("context_fingerprint")
        if policy.get("require_same_context_fingerprint",True) and not context:
            singles.append(task);continue
        key=(
            task.get("provider") if policy.get("require_same_provider",True) else "*",
            task.get("model") if policy.get("require_same_model",True) else "*",
            task.get("effort") if policy.get("require_same_effort",True) else "*",
            context if policy.get("require_same_context_fingerprint",True) else "*",
            task.get("pack_key") or task.get("kind"),
        )
        groups[key].append(task)

    dispatches=[]
    saved=0
    for key,members in sorted(groups.items(),key=lambda kv:str(kv[0])):
        for i in range(0,len(members),max_members):
            chunk=members[i:i+max_members]
            if len(chunk)<2:
                singles.extend(chunk);continue
            dispatches.append({
                "kind":"packed-read-only",
                "provider":chunk[0].get("provider"),
                "model":chunk[0].get("model"),
                "effort":chunk[0].get("effort"),
                "context_fingerprint":chunk[0].get("context_fingerprint"),
                "pack_key":chunk[0].get("pack_key") or chunk[0].get("kind"),
                "members":[
                    {
                        "id":x["id"],
                        "kind":x.get("kind"),
                        "output_contract":x.get("output_contract"),
                        "artifact":x.get("artifact"),
                    } for x in chunk
                ],
                "member_count":len(chunk),
                "requires_separate_member_outputs":True,
            })
            saved+=len(chunk)-1
    for task in sorted(singles,key=lambda x:str(x.get("id"))):
        dispatches.append({
            "kind":"single-read-only",
            "member_count":1,
            "members":[{
                "id":task["id"],
                "kind":task.get("kind"),
                "output_contract":task.get("output_contract"),
                "artifact":task.get("artifact"),
            }],
            "provider":task.get("provider"),
            "model":task.get("model"),
            "effort":task.get("effort"),
            "context_fingerprint":task.get("context_fingerprint"),
        })
    return {
        "schema_version":1,
        "input_count":len(tasks),
        "dispatch_count":len(dispatches),
        "dispatches_saved":saved,
        "dispatches":dispatches,
    }

def self_test():
    tasks=[
      {"id":"A","kind":"analysis","provider":"claude","model":"sonnet","effort":"medium","context_fingerprint":"ctx","independent_judgment":False,"output_contract":"a"},
      {"id":"B","kind":"analysis","provider":"claude","model":"sonnet","effort":"medium","context_fingerprint":"ctx","independent_judgment":False,"output_contract":"b"},
      {"id":"C","kind":"review","provider":"claude","model":"sonnet","effort":"medium","context_fingerprint":"ctx","independent_judgment":True,"output_contract":"c"},
      {"id":"D","kind":"implementation","provider":"codex","model":"gpt-6.1-sol","effort":"medium","context_fingerprint":"ctx","independent_judgment":False,"output_contract":"d"},
    ]
    p=pack(tasks)
    fused=[x for x in p["dispatches"] if x["kind"]=="packed-read-only"]
    assert len(fused)==1 and {m["id"] for m in fused[0]["members"]}=={"A","B"}
    assert p["dispatches_saved"]==1
    assert any(d["members"][0]["id"]=="C" and d["kind"]=="single-read-only" for d in p["dispatches"])
    assert any(d["members"][0]["id"]=="D" and d["kind"]=="single-read-only" for d in p["dispatches"])
    print("PASS: read-only-pack self-test")

def main():
    ap=argparse.ArgumentParser(description="Pack compatible Gearbox read-only tasks into one model dispatch without merging member outputs or independent judgments.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--input")
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.input:ap.error("--input is required")
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    tasks=data.get("tasks",data) if isinstance(data,dict) else data
    result=pack(tasks);text=json.dumps(result,indent=2)+"\n"
    if args.output:Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="");return 0

if __name__=="__main__":
    raise SystemExit(main())
