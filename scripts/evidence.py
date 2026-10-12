#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

from redact import redact_obj, redact_text

PASS_STATES={"PASS","passed","success","0","ok","OK"}
SCHEMA_VERSION=3

def load(path:Path)->dict:
    if not path.exists():
        return {"schema_version":SCHEMA_VERSION,"items":[]}
    data=redact_obj(json.loads(path.read_text(encoding="utf-8")))
    data["schema_version"]=max(int(data.get("schema_version",1)),SCHEMA_VERSION)
    return data

def save(path:Path,data:dict)->None:
    data=redact_obj(data)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def passing(item:dict)->bool:
    status=str(item.get("status",""))
    return status in PASS_STATES or item.get("exit_code")==0

def _sha_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def scope_fingerprint(repo_root:Path,paths:list[str],meta:dict)->dict:
    root=repo_root.resolve()
    deps=[]
    for raw in sorted(set(paths)):
        p=(root/raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        try:
            rel=str(p.relative_to(root))
        except ValueError:
            raise SystemExit(f"dependency escapes repo root: {raw}")
        if not p.exists():
            raise SystemExit(f"dependency missing: {rel}")
        if p.is_dir():
            files=sorted(x for x in p.rglob("*") if x.is_file() and ".git" not in x.parts)
        else:
            files=[p]
        for f in files:
            frel=str(f.relative_to(root))
            deps.append({"path":frel,"sha256":_sha_file(f),"bytes":f.stat().st_size})
    payload={"dependencies":deps,"meta":meta}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {"scope_fingerprint":digest,"dependencies":deps,"meta":meta}

def reuse(data:dict,kind:str,sha:str|None,command:str|None,path:str|None,scope_fp:str|None)->dict:
    now=int(time.time())
    reasons=[]
    candidates=[]
    for item in reversed(data.get("items",[])):
        if item.get("kind")!=kind:
            continue
        if not item.get("valid",True):
            reasons.append(f"item {item.get('id')}: invalidated"); continue
        basis=None
        if scope_fp:
            if item.get("scope_fingerprint")==scope_fp:
                basis="scope_fingerprint"
            else:
                reasons.append(f"item {item.get('id')}: scope fingerprint mismatch"); continue
        else:
            if item.get("sha")!=sha:
                reasons.append(f"item {item.get('id')}: sha mismatch"); continue
            basis="exact_sha"
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
        candidates.append((item,basis))
    if candidates:
        item,basis=candidates[0]
        return {
            "reusable":True,"item_id":item.get("id"),"kind":kind,"sha":item.get("sha"),
            "scope_fingerprint":item.get("scope_fingerprint"),"reuse_basis":basis,
            "summary":item.get("summary"),"command":item.get("command"),"path":item.get("path")
        }
    return {
        "reusable":False,"kind":kind,"sha":sha,"scope_fingerprint":scope_fp,
        "reasons":reasons[-5:] or ["no matching evidence"]
    }

def self_test()->None:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); dep=root/"ui.tsx"; dep.write_text("export const x=1")
        fp=scope_fingerprint(root,["ui.tsx"],{"viewport":"mobile"})
        p=root/"evidence.json"
        d={"schema_version":SCHEMA_VERSION,"items":[
            {"id":1,"kind":"a11y","sha":"abc","scope_fingerprint":fp["scope_fingerprint"],"status":"PASS","summary":"ok","valid":True},
            {"id":2,"kind":"test","sha":"abc","status":"PASS","command":"pytest x","summary":"x passes","valid":True},
        ]}
        save(p,d); loaded=load(p)
        assert reuse(loaded,"test","abc","pytest x",None,None)["reuse_basis"]=="exact_sha"
        cross=reuse(loaded,"a11y","def",None,None,fp["scope_fingerprint"])
        assert cross["reusable"] is True and cross["reuse_basis"]=="scope_fingerprint"
        dep.write_text("export const x=2")
        fp2=scope_fingerprint(root,["ui.tsx"],{"viewport":"mobile"})
        assert fp2["scope_fingerprint"]!=fp["scope_fingerprint"]
        assert reuse(loaded,"a11y","def",None,None,fp2["scope_fingerprint"])["reusable"] is False
    print("PASS: evidence reuse self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Maintain Gearbox's redacted evidence ledger with exact-SHA or dependency-scoped reuse.")
    sp=ap.add_subparsers(dest="cmd",required=True)

    a=sp.add_parser("init"); a.add_argument("--file",required=True)

    a=sp.add_parser("fingerprint")
    a.add_argument("--repo-root",default="."); a.add_argument("--path",action="append",default=[],required=True); a.add_argument("--meta-json",default="{}")

    a=sp.add_parser("add")
    a.add_argument("--file",required=True); a.add_argument("--kind",required=True); a.add_argument("--sha")
    a.add_argument("--scope-fingerprint"); a.add_argument("--status",required=True); a.add_argument("--summary",required=True)
    a.add_argument("--command"); a.add_argument("--exit-code",type=int); a.add_argument("--path"); a.add_argument("--meta-json",default="{}")
    a.add_argument("--volatile",action="store_true"); a.add_argument("--ttl-seconds",type=int)

    a=sp.add_parser("reuse")
    a.add_argument("--file",required=True); a.add_argument("--kind",required=True); a.add_argument("--sha")
    a.add_argument("--scope-fingerprint"); a.add_argument("--command"); a.add_argument("--path"); a.add_argument("--require",action="store_true")

    a=sp.add_parser("invalidate")
    a.add_argument("--file",required=True); a.add_argument("--sha"); a.add_argument("--scope-fingerprint"); a.add_argument("--reason",required=True)

    a=sp.add_parser("show"); a.add_argument("--file",required=True)
    sp.add_parser("self-test")

    args=ap.parse_args()
    if args.cmd=="self-test":
        self_test(); return 0
    if args.cmd=="fingerprint":
        meta=json.loads(args.meta_json)
        print(json.dumps(scope_fingerprint(Path(args.repo_root),args.path,meta),indent=2)); return 0

    path=Path(args.file); data=load(path)
    if args.cmd=="init":
        save(path,data); return 0
    if args.cmd=="show":
        print(json.dumps(redact_obj(data),indent=2)); return 0
    if args.cmd=="reuse":
        if not args.sha and not args.scope_fingerprint:
            raise SystemExit("reuse requires --sha or --scope-fingerprint")
        payload=reuse(data,args.kind,args.sha,args.command,args.path,args.scope_fingerprint)
        print(json.dumps(redact_obj(payload),indent=2))
        return 0 if payload["reusable"] or not args.require else 6
    if args.cmd=="add":
        item={
            "id":len(data["items"])+1,"kind":redact_text(args.kind),"sha":args.sha,
            "scope_fingerprint":args.scope_fingerprint,"status":redact_text(args.status),
            "summary":redact_text(args.summary),"created_at":int(time.time()),
            "valid":True,"reusable":not args.volatile,
        }
        if args.command: item["command"]=redact_text(args.command)
        if args.exit_code is not None: item["exit_code"]=args.exit_code
        if args.path: item["path"]=redact_text(args.path)
        if args.ttl_seconds is not None:
            if args.ttl_seconds<=0: raise SystemExit("--ttl-seconds must be positive")
            item["expires_at"]=int(time.time())+args.ttl_seconds
        meta=json.loads(args.meta_json); item.update(redact_obj(meta)); data["items"].append(item)
    else:
        if not args.sha and not args.scope_fingerprint:
            raise SystemExit("invalidate requires --sha or --scope-fingerprint")
        reason=redact_text(args.reason)
        for item in data["items"]:
            match=(args.sha and item.get("sha")==args.sha) or (args.scope_fingerprint and item.get("scope_fingerprint")==args.scope_fingerprint)
            if match and item.get("valid",True):
                item["valid"]=False; item["invalidated_reason"]=reason

    save(path,data)
    print(json.dumps(redact_obj(data),indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
