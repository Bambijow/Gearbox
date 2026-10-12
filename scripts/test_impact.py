#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"

def project_cache_dir()->Path:
    base=Path(os.environ.get("XDG_CACHE_HOME",Path.home()/".cache"))/"gearbox"
    proc=subprocess.run(["git","rev-parse","--git-common-dir"],capture_output=True,text=True,check=False)
    identity=(proc.stdout.strip() if proc.returncode==0 and proc.stdout.strip() else str(Path.cwd().resolve()))
    if proc.returncode==0 and identity:
        p=Path(identity)
        if not p.is_absolute():p=(Path.cwd()/p).resolve()
        identity=str(p)
    key=hashlib.sha256(identity.encode()).hexdigest()[:16]
    return base/key/"test-impact.json"

def load(path:Path)->dict:
    if not path.exists():return {"schema_version":1,"observations":[]}
    return json.loads(path.read_text(encoding="utf-8"))

def save(path:Path,data:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def bucket(path:str,depth:int)->str:
    parts=[x for x in path.replace("\\","/").split("/") if x]
    if not parts:return ""
    return "/".join(parts[:max(1,depth)])

def policy()->dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8")).get("test_impact",{})

def record(data:dict,check_id:str,paths:list[str],status:str,duration_ms:int|None)->dict:
    cfg=policy();depth=int(cfg.get("bucket_depth",2))
    item={
        "check_id":check_id,
        "path_buckets":sorted({bucket(p,depth) for p in paths if bucket(p,depth)}),
        "status":status,
        "duration_ms":duration_ms,
        "recorded_at":int(time.time()),
    }
    data.setdefault("observations",[]).append(item)
    return item

def rank(data:dict,candidates:list[str],paths:list[str])->dict:
    cfg=policy();depth=int(cfg.get("bucket_depth",2));min_samples=int(cfg.get("min_samples",5))
    current={bucket(p,depth) for p in paths if bucket(p,depth)}
    rows=[]
    for cid in candidates:
        obs=[x for x in data.get("observations",[]) if x.get("check_id")==cid]
        relevant=[x for x in obs if current.intersection(x.get("path_buckets",[]))]
        failures=sum(1 for x in relevant if x.get("status")=="fail")
        samples=len(relevant)
        pass_count=sum(1 for x in relevant if x.get("status")=="pass")
        durations=[x["duration_ms"] for x in relevant if isinstance(x.get("duration_ms"),int)]
        # Smoothed failure correlation. This ranks historically sensitive checks first,
        # but never authorizes dropping other required checks.
        impact_score=(failures+1)/(samples+2) if samples else 0.0
        confidence=min(1.0,samples/min_samples) if min_samples>0 else 1.0
        priority=impact_score*confidence
        rows.append({
            "check_id":cid,
            "samples":samples,
            "failures":failures,
            "passes":pass_count,
            "impact_score":round(impact_score,6),
            "confidence":round(confidence,6),
            "priority":round(priority,6),
            "median_duration_ms":sorted(durations)[len(durations)//2] if durations else None,
        })
    rows.sort(key=lambda x:(-x["priority"],-x["samples"],x["median_duration_ms"] if x["median_duration_ms"] is not None else 10**18,x["check_id"]))
    return {
        "schema_version":1,
        "mode":cfg.get("mode","rank-only"),
        "changed_buckets":sorted(current),
        "min_samples":min_samples,
        "ranked":rows,
        "never_drop_required_checks":bool(cfg.get("never_drop_required_checks",True)),
    }

def apply_to_plan(data:dict,plan:dict,paths:list[str])->dict:
    candidates=[x.get("id") for x in plan.get("checks",[]) if x.get("id")]
    ranked=rank(data,candidates,paths)
    order={x["check_id"]:i for i,x in enumerate(ranked.get("ranked",[]))}
    out=json.loads(json.dumps(plan))
    out["checks"].sort(key=lambda x:(order.get(x.get("id"),10**6),x.get("id","")))
    out["historical_test_impact"]=ranked
    return out

def self_test():
    data={"schema_version":1,"observations":[]}
    for _ in range(6):
        record(data,"ui-unit",["src/components/Button.tsx"],"fail",100)
        record(data,"all-tests",["src/components/Button.tsx"],"pass",1000)
    r=rank(data,["all-tests","ui-unit"],["src/components/Button.tsx"])
    assert r["ranked"][0]["check_id"]=="ui-unit"
    assert r["never_drop_required_checks"] is True
    r2=rank(data,["ui-unit"],["docs/README.md"])
    assert r2["ranked"][0]["samples"]==0
    plan={"checks":[{"id":"all-tests"},{"id":"ui-unit"}]}
    applied=apply_to_plan(data,plan,["src/components/Button.tsx"])
    assert applied["checks"][0]["id"]=="ui-unit"
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"impact.json";save(p,data);assert len(load(p)["observations"])==12
    print("PASS: test-impact self-test")

def main():
    ap=argparse.ArgumentParser(description="Record and rank repository checks from historical changed-path/check outcomes without dropping required verification.")
    ap.add_argument("--self-test",action="store_true")
    sp=ap.add_subparsers(dest="cmd")
    a=sp.add_parser("record");a.add_argument("--file",type=Path);a.add_argument("--check-id",required=True);a.add_argument("--changed-path",action="append",default=[]);a.add_argument("--status",choices=("pass","fail"),required=True);a.add_argument("--duration-ms",type=int)
    a=sp.add_parser("rank");a.add_argument("--file",type=Path);a.add_argument("--candidate",action="append",default=[]);a.add_argument("--changed-path",action="append",default=[])
    a=sp.add_parser("apply");a.add_argument("--file",type=Path);a.add_argument("--plan",type=Path,required=True);a.add_argument("--changed-path",action="append",default=[]);a.add_argument("--output")
    a=sp.add_parser("show");a.add_argument("--file",type=Path)
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.cmd:ap.error("command required")
    path=args.file or project_cache_dir()
    data=load(path)
    if args.cmd=="record":
        item=record(data,args.check_id,args.changed_path,args.status,args.duration_ms);save(path,data);print(json.dumps({"recorded":item,"file":str(path)},indent=2));return 0
    if args.cmd=="rank":
        print(json.dumps(rank(data,args.candidate,args.changed_path),indent=2));return 0
    if args.cmd=="apply":
        plan=json.loads(args.plan.read_text(encoding="utf-8"))
        result=apply_to_plan(data,plan,args.changed_path);text=json.dumps(result,indent=2)+"\n"
        if args.output:Path(args.output).write_text(text,encoding="utf-8")
        print(text,end="");return 0
    print(json.dumps(data,indent=2));return 0

if __name__=="__main__":
    raise SystemExit(main())
