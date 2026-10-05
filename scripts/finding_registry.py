#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path

SEVERITY_RANK={"Advisory":0,"Minor":1,"Important":2,"Blocker":3}

def die(msg: str, code: int=2) -> None:
    print(json.dumps({"ok":False,"reason":msg}))
    raise SystemExit(code)

def load(path: Path) -> dict:
    if not path.exists():
        die(f"state missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def save(path: Path, data: dict) -> None:
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def norm(value: str) -> str:
    value=value.strip().lower()
    value=re.sub(r"\\","/",value)
    value=re.sub(r"\s+"," ",value)
    return value

def fingerprint(identity: str) -> str:
    canonical=norm(identity)
    if len(canonical)<4:
        die("canonical identity is too vague")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

def registry(state: dict) -> dict:
    rf=state.setdefault("repair_findings",{})
    rf.setdefault("policy",{"same_strategy_limit":2,"max_attempts_per_finding":5})
    return rf.setdefault("items",{})

def ingest(state: dict, identity: str, source_kind: str, source_id: str, summary: str, severity: str, primary_path: str|None) -> dict:
    if severity not in SEVERITY_RANK:
        die(f"invalid severity: {severity}")
    fp=fingerprint(identity)
    items=registry(state)
    existing=None
    for item in items.values():
        if item.get("fingerprint")==fp:
            existing=item
            break
    src={"kind":source_kind,"id":source_id,"summary":summary,"seen_at":int(time.time())}
    if primary_path:
        src["path"]=primary_path
    if existing:
        sources=existing.setdefault("sources",[])
        if not any(s.get("kind")==source_kind and s.get("id")==source_id for s in sources):
            sources.append(src)
        if SEVERITY_RANK[severity] > SEVERITY_RANK.get(existing.get("severity","Advisory"),0):
            existing["severity"]=severity
        existing["last_seen_at"]=int(time.time())
        return {"ok":True,"deduplicated":True,"finding_id":existing["id"],"fingerprint":fp,"source_count":len(sources)}
    fid="FND-"+fp[:8].upper()
    items[fid]={
        "id":fid,
        "fingerprint":fp,
        "identity":identity.strip(),
        "summary":summary,
        "severity":severity,
        "primary_path":primary_path,
        "status":"OPEN",
        "attempts":[],
        "sources":[src],
        "opened_at":int(time.time()),
    }
    return {"ok":True,"deduplicated":False,"finding_id":fid,"fingerprint":fp,"source_count":1}

def merge(state: dict, into: str, source: str, ruling: str) -> dict:
    items=registry(state)
    if into not in items or source not in items:
        die("both --into and --from findings must exist")
    if into==source:
        die("cannot merge a finding into itself")
    target=items[into]; other=items[source]
    for src in other.get("sources",[]):
        if not any(s.get("kind")==src.get("kind") and s.get("id")==src.get("id") for s in target.setdefault("sources",[])):
            target["sources"].append(src)
    if SEVERITY_RANK.get(other.get("severity","Advisory"),0) > SEVERITY_RANK.get(target.get("severity","Advisory"),0):
        target["severity"]=other["severity"]
    other["status"]="MERGED"
    other["merged_into"]=into
    other["merge_ruling"]=ruling
    other["resolved_at"]=int(time.time())
    return {"ok":True,"merged":source,"into":into,"source_count":len(target.get("sources",[]))}

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"state.json"
        p.write_text('{"run_id":"t"}\n',encoding="utf-8")
        s=load(p)
        a=ingest(s,"anonymous request|null deref|src/foo.ts","ci","job-1","500 on anonymous","Important","src/foo.ts")
        b=ingest(s,"  Anonymous request | null deref | src/foo.ts  ","review","rev-4","missing null guard","Blocker","src/foo.ts")
        assert a["finding_id"]==b["finding_id"] and b["deduplicated"] and b["source_count"]==2
        c=ingest(s,"timeout|remote call|src/bar.ts","human","comment-7","slow path","Minor","src/bar.ts")
        assert c["finding_id"]!=a["finding_id"]
        save(p,s)
    print("PASS: finding-registry self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Deterministically deduplicate Gearbox repair findings by caller-supplied canonical failure identity.")
    ap.add_argument("--self-test",action="store_true")
    sub=ap.add_subparsers(dest="cmd")
    a=sub.add_parser("ingest")
    a.add_argument("--run-dir",required=True,type=Path); a.add_argument("--identity",required=True)
    a.add_argument("--source-kind",required=True,choices=("ci","review","human","verifier","runtime"))
    a.add_argument("--source-id",required=True); a.add_argument("--summary",required=True)
    a.add_argument("--severity",default="Important",choices=tuple(SEVERITY_RANK))
    a.add_argument("--primary-path")
    a=sub.add_parser("merge")
    a.add_argument("--run-dir",required=True,type=Path); a.add_argument("--into",required=True); a.add_argument("--from",dest="source",required=True); a.add_argument("--ruling",required=True)
    a=sub.add_parser("show"); a.add_argument("--run-dir",required=True,type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.cmd:
        ap.error("command required")
    p=args.run_dir/"state.json"; state=load(p)
    if args.cmd=="ingest":
        payload=ingest(state,args.identity,args.source_kind,args.source_id,args.summary,args.severity,args.primary_path)
    elif args.cmd=="merge":
        payload=merge(state,args.into,args.source,args.ruling)
    else:
        payload=registry(state)
    save(p,state)
    print(json.dumps(payload,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
