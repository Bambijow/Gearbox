#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path

from redact import redact_obj, redact_text

PASS_STATES={"PASS","passed","success","0","ok","OK"}

def load(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 2, "items": []}
    data=redact_obj(json.loads(path.read_text(encoding="utf-8")))
    data["schema_version"]=max(int(data.get("schema_version",1)),2)
    return data

def save(path: Path, data: dict) -> None:
    data=redact_obj(data)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def passing(item: dict) -> bool:
    status=str(item.get("status",""))
    return status in PASS_STATES or item.get("exit_code")==0

def reuse(data: dict, kind: str, sha: str, command: str|None, path: str|None) -> dict:
    now=int(time.time())
    reasons=[]
    candidates=[]
    for item in reversed(data.get("items",[])):
        if item.get("kind")!=kind:
            continue
        if not item.get("valid",True):
            reasons.append(f"item {item.get('id')}: invalidated"); continue
        if item.get("sha")!=sha:
            reasons.append(f"item {item.get('id')}: sha mismatch"); continue
        if not passing(item):
            reasons.append(f"item {item.get('id')}: not passing"); continue
        if item.get("reusable") is False:
            reasons.append(f"item {item.get('id')}: marked volatile"); continue
        expires=item.get("expires_at")
        if isinstance(expires,int) and now>expires:
            reasons.append(f"item {item.get('id')}: expired"); continue
        if command is not None and item.get("command")!=command:
            reasons.append(f"item {item.get('id')}: command mismatch"); continue
        if path is not None and item.get("path")!=path:
            reasons.append(f"item {item.get('id')}: path mismatch"); continue
        candidates.append(item)
    if candidates:
        item=candidates[0]
        return {"reusable":True,"item_id":item.get("id"),"kind":kind,"sha":sha,"summary":item.get("summary"),"command":item.get("command"),"path":item.get("path")}
    return {"reusable":False,"kind":kind,"sha":sha,"reasons":reasons[-5:] or ["no matching evidence"]}

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"evidence.json"
        d={"schema_version":2,"items":[
            {"id":1,"kind":"test","sha":"abc","status":"PASS","command":"pytest x","summary":"x passes","valid":True},
            {"id":2,"kind":"test","sha":"abc","status":"PASS","command":"pytest volatile","summary":"volatile","valid":True,"reusable":False},
        ]}
        save(p,d); loaded=load(p)
        assert reuse(loaded,"test","abc","pytest x",None)["reusable"] is True
        assert reuse(loaded,"test","def","pytest x",None)["reusable"] is False
        assert reuse(loaded,"test","abc","pytest volatile",None)["reusable"] is False
    print("PASS: evidence reuse self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Maintain Gearbox's redacted, SHA-scoped evidence ledger.")
    sp=ap.add_subparsers(dest="cmd",required=True)

    a=sp.add_parser("init"); a.add_argument("--file",required=True)

    a=sp.add_parser("add")
    a.add_argument("--file",required=True); a.add_argument("--kind",required=True); a.add_argument("--sha")
    a.add_argument("--status",required=True); a.add_argument("--summary",required=True); a.add_argument("--command")
    a.add_argument("--exit-code",type=int); a.add_argument("--path"); a.add_argument("--meta-json",default="{}")
    a.add_argument("--volatile",action="store_true",help="Evidence is informational but must not be reused as a later completion proof.")
    a.add_argument("--ttl-seconds",type=int,help="Optional freshness window for environment-dependent evidence.")

    a=sp.add_parser("reuse")
    a.add_argument("--file",required=True); a.add_argument("--kind",required=True); a.add_argument("--sha",required=True)
    a.add_argument("--command"); a.add_argument("--path"); a.add_argument("--require",action="store_true")

    a=sp.add_parser("invalidate")
    a.add_argument("--file",required=True); a.add_argument("--sha",required=True); a.add_argument("--reason",required=True)

    a=sp.add_parser("show"); a.add_argument("--file",required=True)
    sp.add_parser("self-test")

    args=ap.parse_args()
    if args.cmd=="self-test":
        self_test(); return 0
    path=Path(args.file); data=load(path)

    if args.cmd=="init":
        save(path,data); return 0
    if args.cmd=="show":
        print(json.dumps(redact_obj(data),indent=2)); return 0
    if args.cmd=="reuse":
        payload=reuse(data,args.kind,args.sha,args.command,args.path)
        print(json.dumps(redact_obj(payload),indent=2))
        return 0 if payload["reusable"] or not args.require else 6
    if args.cmd=="add":
        item={
            "id":len(data["items"])+1,
            "kind":redact_text(args.kind),
            "sha":args.sha,
            "status":redact_text(args.status),
            "summary":redact_text(args.summary),
            "created_at":int(time.time()),
            "valid":True,
            "reusable":not args.volatile,
        }
        if args.command: item["command"]=redact_text(args.command)
        if args.exit_code is not None: item["exit_code"]=args.exit_code
        if args.path: item["path"]=redact_text(args.path)
        if args.ttl_seconds is not None:
            if args.ttl_seconds<=0: raise SystemExit("--ttl-seconds must be positive")
            item["expires_at"]=int(time.time())+args.ttl_seconds
        try: meta=json.loads(args.meta_json)
        except json.JSONDecodeError as exc: raise SystemExit(f"invalid --meta-json: {exc}")
        item.update(redact_obj(meta)); data["items"].append(item)
    else:
        reason=redact_text(args.reason)
        for item in data["items"]:
            if item.get("sha")==args.sha and item.get("valid",True):
                item["valid"]=False; item["invalidated_reason"]=reason

    save(path,data)
    print(json.dumps(redact_obj(data),indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
