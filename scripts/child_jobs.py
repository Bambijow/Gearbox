#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import tempfile
import time
from pathlib import Path

def load(path: Path) -> dict:
    if not path.exists():
        return {"schema_version":1,"children":{}}
    return json.loads(path.read_text(encoding="utf-8"))

def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def path_for(run: Path) -> Path:
    return run/"children.json"

def alive(pid: int) -> bool:
    try: os.kill(pid,0); return True
    except (ProcessLookupError,PermissionError): return False

def reconcile(data: dict, base: Path, now: int|None=None) -> dict:
    now=now or int(time.time())
    counts={}
    for child in data.setdefault("children",{}).values():
        status=child.get("status","RUNNING")
        if status in {"COMPLETED","FAILED","CANCELLED"}:
            counts[status]=counts.get(status,0)+1; continue
        artifact=child.get("artifact")
        if artifact:
            p=Path(artifact)
            if not p.is_absolute(): p=base/p
            if p.is_file() and p.stat().st_size>0:
                child["status"]="ARTIFACT_READY"; child["updated_at"]=now
                counts["ARTIFACT_READY"]=counts.get("ARTIFACT_READY",0)+1
                continue
        pid=child.get("pid")
        if isinstance(pid,int) and child.get("host")==socket.gethostname() and not alive(pid):
            child["status"]="ORPHANED"; child["updated_at"]=now
            counts["ORPHANED"]=counts.get("ORPHANED",0)+1
            continue
        timeout=int(child.get("timeout_seconds",3600))
        if now-int(child.get("started_at",now))>timeout:
            child["status"]="STALE"; child["updated_at"]=now
            counts["STALE"]=counts.get("STALE",0)+1
            continue
        child["status"]="RUNNING"
        counts["RUNNING"]=counts.get("RUNNING",0)+1
    return counts

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        run=Path(td)
        data={"schema_version":1,"children":{}}
        data["children"]["a"]={"id":"a","status":"RUNNING","started_at":1,"timeout_seconds":2}
        counts=reconcile(data,run,now=10)
        assert counts["STALE"]==1
        art=run/"r.json"; art.write_text("{}\n",encoding="utf-8")
        data["children"]["b"]={"id":"b","status":"RUNNING","started_at":9,"timeout_seconds":20,"artifact":"r.json"}
        counts=reconcile(data,run,now=10)
        assert data["children"]["b"]["status"]=="ARTIFACT_READY"
    print("PASS: child-jobs self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Track and reconcile Gearbox background/delegated child work without tight polling.")
    ap.add_argument("--self-test",action="store_true")
    sub=ap.add_subparsers(dest="cmd")
    a=sub.add_parser("register"); a.add_argument("--run-dir",type=Path,required=True); a.add_argument("--id",required=True); a.add_argument("--kind",required=True); a.add_argument("--provider",required=True); a.add_argument("--artifact"); a.add_argument("--timeout-seconds",type=int,default=3600); a.add_argument("--pid",type=int)
    for name in ("complete","fail","cancel"):
        a=sub.add_parser(name); a.add_argument("--run-dir",type=Path,required=True); a.add_argument("--id",required=True); a.add_argument("--note")
    a=sub.add_parser("reconcile"); a.add_argument("--run-dir",type=Path,required=True)
    a=sub.add_parser("show"); a.add_argument("--run-dir",type=Path,required=True)
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.cmd: ap.error("command required")
    p=path_for(args.run_dir); data=load(p); children=data.setdefault("children",{})
    now=int(time.time())
    if args.cmd=="register":
        old=children.get(args.id)
        if old and old.get("status") not in {"COMPLETED","FAILED","CANCELLED","STALE","ORPHANED"}:
            raise SystemExit(f"child id already active: {args.id}")
        children[args.id]={
            "id":args.id,"kind":args.kind,"provider":args.provider,"artifact":args.artifact,
            "timeout_seconds":args.timeout_seconds,"pid":args.pid,"host":socket.gethostname(),
            "status":"RUNNING","started_at":now,"updated_at":now
        }
        payload=children[args.id]
    elif args.cmd in {"complete","fail","cancel"}:
        if args.id not in children: raise SystemExit(f"unknown child: {args.id}")
        status={"complete":"COMPLETED","fail":"FAILED","cancel":"CANCELLED"}[args.cmd]
        children[args.id]["status"]=status; children[args.id]["updated_at"]=now
        if args.note: children[args.id]["note"]=args.note
        payload=children[args.id]
    elif args.cmd=="reconcile":
        payload={"counts":reconcile(data,args.run_dir.resolve(),now),"children":children}
    else:
        payload=data
    save(p,data); print(json.dumps(payload,indent=2)); return 0

if __name__=="__main__":
    raise SystemExit(main())
