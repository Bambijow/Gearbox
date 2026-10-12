#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import posixpath
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"

DONE={"INTEGRATED","COMPLETED","PASS","PASSED"}
ACTIVE={"RUNNING","DISPATCHED","REVIEWING","INTEGRATING"}
WAITING={"PENDING","READY","PLANNED"}
BAD={"FAILED","BLOCKED","CANCELLED"}
RISK_RANK={"low":0,"medium":1,"high":2,"critical":3}

def norm_path(value:str)->str:
    p=value.replace("\\","/").strip()
    for suffix in ("/**","/*"):
        if p.endswith(suffix): p=p[:-len(suffix)]
    p = posixpath.normpath(p)
    # Ownership is repository-relative. Unbounded/glob scopes reserve the whole repo.
    if p in {".", "/", ".."} or p.startswith(("../", "/")) or any(c in p for c in "*?["):
        return "."
    return p.rstrip("/")

def conflicts(a:list[str],b:list[str])->bool:
    aa=[norm_path(x) for x in a if norm_path(x)]
    bb=[norm_path(x) for x in b if norm_path(x)]
    for x in aa:
        for y in bb:
            if x=="." or y=="." or x==y or x.startswith(y+"/") or y.startswith(x+"/"):
                return True
    return False

def descendants(tasks:dict[str,dict])->dict[str,set[str]]:
    rev=defaultdict(set)
    for tid,t in tasks.items():
        for dep in t.get("dependencies",[]):
            if dep in tasks: rev[dep].add(tid)
    memo={}
    def walk(tid,stack):
        if tid in memo: return memo[tid]
        if tid in stack: return set()
        out=set()
        for child in rev.get(tid,set()):
            out.add(child); out.update(walk(child,stack|{tid}))
        memo[tid]=out; return out
    return {tid:walk(tid,set()) for tid in tasks}

def critical_lengths(tasks:dict[str,dict])->dict[str,int]:
    rev=defaultdict(set)
    for tid,t in tasks.items():
        for dep in t.get("dependencies",[]):
            if dep in tasks: rev[dep].add(tid)
    memo={}
    def length(tid,stack):
        if tid in memo:return memo[tid]
        if tid in stack:return 1
        kids=[x for x in rev.get(tid,set()) if tasks[x].get("status","PENDING") not in DONE]
        val=1+(max((length(x,stack|{tid}) for x in kids),default=0))
        memo[tid]=val; return val
    return {tid:length(tid,set()) for tid in tasks}

def priority_key(t:dict,critical:int,desc:int):
    risk=RISK_RANK.get(str(t.get("risk","medium")).casefold(),1)
    return (-critical,-desc,-risk,str(t.get("id","")))

def plan(data:dict)->dict:
    task_list=data.get("tasks",[])
    tasks={str(t["id"]):dict(t) for t in task_list}
    scheduler_cfg=json.loads(REGISTRY.read_text(encoding="utf-8")).get("scheduler",{})
    max_workers=max(1,int(data.get("max_parallel_workers",1)))
    active=[t for t in tasks.values() if t.get("status") in ACTIVE]
    slots=max(0,max_workers-len(active))
    active_paths=[p for t in active for p in t.get("owned_paths",[])]

    desc=descendants(tasks); crit=critical_lengths(tasks)
    ready=[]; blocked=[]; waiting=[]
    for tid,t in tasks.items():
        status=t.get("status","PENDING")
        if status not in WAITING: continue
        deps=t.get("dependencies",[])
        missing=[d for d in deps if d not in tasks]
        bad=[d for d in deps if d in tasks and tasks[d].get("status") in BAD]
        pending=[d for d in deps if d in tasks and tasks[d].get("status") not in DONE]
        if missing or bad:
            blocked.append({"id":tid,"missing_dependencies":missing,"failed_dependencies":bad})
        elif pending:
            waiting.append({"id":tid,"waiting_on":pending})
        elif conflicts(t.get("owned_paths",[]),active_paths):
            waiting.append({"id":tid,"waiting_on_active_ownership":True})
        else:
            item=dict(t); item["_critical"]=crit[tid]; item["_descendants"]=len(desc[tid]); ready.append(item)

    ready.sort(key=lambda t:priority_key(t,t["_critical"],t["_descendants"]))

    used=set(); dispatch=[]
    reserved_paths=list(active_paths)
    batch_enabled=bool(data.get("batch_same_shape",scheduler_cfg.get("batch_same_shape",True)))
    max_batch=max(1,int(data.get("max_batch_members",scheduler_cfg.get("max_batch_members",6))))
    for t in ready:
        if len(dispatch)>=slots:
            break
        if t["id"] in used:
            continue
        if conflicts(t.get("owned_paths",[]),reserved_paths):
            waiting.append({"id":t["id"],"waiting_on_selected_ownership":True})
            continue
        key=t.get("batch_key")
        risk=str(t.get("risk","medium")).casefold()
        if batch_enabled and key and risk in {"low","medium"}:
            members=[]
            for cand in ready:
                if cand["id"] in used or cand.get("batch_key")!=key: continue
                if conflicts(cand.get("owned_paths",[]),reserved_paths): continue
                if str(cand.get("risk","medium")).casefold() not in {"low","medium"}: continue
                if any(conflicts(cand.get("owned_paths",[]),m.get("owned_paths",[])) for m in members): continue
                members.append(cand)
                if len(members)>=max_batch: break
            if len(members)>=2:
                for m in members:
                    used.add(m["id"])
                    reserved_paths.extend(m.get("owned_paths",[]))
                dispatch.append({
                    "kind":"batch","batch_key":key,"members":[m["id"] for m in members],
                    "critical_path":max(m["_critical"] for m in members),
                    "descendant_count":sum(m["_descendants"] for m in members),
                })
                continue
        used.add(t["id"])
        reserved_paths.extend(t.get("owned_paths",[]))
        dispatch.append({
            "kind":"task","id":t["id"],"critical_path":t["_critical"],
            "descendant_count":t["_descendants"],"risk":t.get("risk","medium")
        })

    return {
        "schema_version":1,
        "max_parallel_workers":max_workers,
        "active_workers":len(active),
        "available_slots":slots,
        "ready":[{"id":t["id"],"critical_path":t["_critical"],"descendant_count":t["_descendants"]} for t in ready],
        "dispatch_units":dispatch,
        "blocked":blocked,
        "waiting":waiting,
    }

def self_test():
    data={"max_parallel_workers":2,"tasks":[
        {"id":"A","status":"READY","dependencies":[],"owned_paths":["src/a"],"risk":"medium"},
        {"id":"B","status":"READY","dependencies":[],"owned_paths":["src/b1"],"risk":"low","batch_key":"rename"},
        {"id":"C","status":"READY","dependencies":[],"owned_paths":["src/b2"],"risk":"low","batch_key":"rename"},
        {"id":"D","status":"PENDING","dependencies":["A"],"owned_paths":["src/d"],"risk":"high"},
        {"id":"E","status":"PENDING","dependencies":["D"],"owned_paths":["src/e"],"risk":"medium"},
    ]}
    p=plan(data)
    assert p["dispatch_units"][0]["kind"]=="task" and p["dispatch_units"][0]["id"]=="A"
    assert p["dispatch_units"][1]["kind"]=="batch" and set(p["dispatch_units"][1]["members"])=={"B","C"}
    data2={"max_parallel_workers":2,"tasks":[
        {"id":"R","status":"RUNNING","dependencies":[],"owned_paths":["src/shared"]},
        {"id":"X","status":"READY","dependencies":[],"owned_paths":["src/shared/x"]},
    ]}
    p2=plan(data2)
    assert not p2["dispatch_units"] and p2["waiting"][0]["waiting_on_active_ownership"]
    print("PASS: frontier-scheduler self-test")

def main():
    ap=argparse.ArgumentParser(description="Deterministically choose Gearbox ready-frontier dispatch units.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--input")
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.input: ap.error("--input is required")
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    result=plan(data); text=json.dumps(result,indent=2)+"\n"
    if args.output: Path(args.output).write_text(text,encoding="utf-8")
    print(text,end=""); return 0

if __name__=="__main__":
    raise SystemExit(main())
