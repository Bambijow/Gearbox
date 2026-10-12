#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ALLOWED_KINDS={"research","review","gate","probe","analysis","static-check","route"}

def project_cache_dir()->Path:
    base=Path(os.environ.get("XDG_CACHE_HOME",Path.home()/".cache"))/"gearbox"
    proc=subprocess.run(["git","rev-parse","--git-common-dir"],capture_output=True,text=True,check=False)
    identity=(proc.stdout.strip() if proc.returncode==0 and proc.stdout.strip() else str(Path.cwd().resolve()))
    if proc.returncode==0 and identity:
        p=Path(identity)
        if not p.is_absolute(): p=(Path.cwd()/p).resolve()
        identity=str(p)
    repo_key=hashlib.sha256(identity.encode()).hexdigest()[:16]
    return base/repo_key/"results"

def key_for(kind:str,fingerprint:str)->str:
    return hashlib.sha256(f"{kind}\0{fingerprint}".encode()).hexdigest()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def put(cache:Path,kind:str,fingerprint:str,artifact:Path,meta:dict,ttl:int|None)->dict:
    if kind not in ALLOWED_KINDS:raise SystemExit(f"cache kind not allowed: {kind}")
    if not artifact.is_file():raise SystemExit(f"artifact missing: {artifact}")
    key=key_for(kind,fingerprint);dest=cache/key;dest.mkdir(parents=True,exist_ok=True);target=dest/"artifact";shutil.copy2(artifact,target)
    manifest={"schema_version":1,"key":key,"kind":kind,"fingerprint":fingerprint,"artifact":"artifact","sha256":sha256_file(target),"bytes":target.stat().st_size,"created_at":int(time.time()),"meta":meta}
    if ttl is not None:
        if ttl<=0:raise SystemExit("--ttl-seconds must be positive")
        manifest["expires_at"]=int(time.time())+ttl
    tmp=dest/"manifest.json.tmp";tmp.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8");os.replace(tmp,dest/"manifest.json")
    return manifest

def get(cache:Path,kind:str,fingerprint:str)->dict:
    key=key_for(kind,fingerprint);dest=cache/key;mp=dest/"manifest.json"
    if not mp.is_file():return {"hit":False,"reason":"missing","key":key}
    m=json.loads(mp.read_text(encoding="utf-8"))
    if m.get("kind")!=kind or m.get("fingerprint")!=fingerprint:return {"hit":False,"reason":"manifest mismatch","key":key}
    exp=m.get("expires_at")
    if isinstance(exp,int) and int(time.time())>exp:return {"hit":False,"reason":"expired","key":key}
    artifact=dest/m["artifact"]
    if not artifact.is_file():return {"hit":False,"reason":"artifact missing","key":key}
    if sha256_file(artifact)!=m.get("sha256"):return {"hit":False,"reason":"artifact hash mismatch","key":key}
    return {"hit":True,"key":key,"artifact":str(artifact),"manifest":m}

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);cache=root/"cache";src=root/"x.json";src.write_text('{"ok":true}')
        m=put(cache,"review","fp1",src,{"model":"sonnet"},None)
        hit=get(cache,"review","fp1");assert hit["hit"] and hit["manifest"]["sha256"]==m["sha256"]
        assert not get(cache,"review","fp2")["hit"]
        try:put(cache,"implementation","fp",src,{},None);raise AssertionError("mutation result must not be cached")
        except SystemExit:pass
    print("PASS: result-cache self-test")

def main():
    ap=argparse.ArgumentParser(description="Cache immutable read-only Gearbox results across runs by exact input fingerprint.")
    ap.add_argument("--self-test",action="store_true");sp=ap.add_subparsers(dest="cmd")
    a=sp.add_parser("put");a.add_argument("--cache-dir",type=Path);a.add_argument("--kind",required=True,choices=sorted(ALLOWED_KINDS));a.add_argument("--fingerprint",required=True);a.add_argument("--artifact",type=Path,required=True);a.add_argument("--meta-json",default="{}");a.add_argument("--ttl-seconds",type=int)
    a=sp.add_parser("get");a.add_argument("--cache-dir",type=Path);a.add_argument("--kind",required=True,choices=sorted(ALLOWED_KINDS));a.add_argument("--fingerprint",required=True)
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.cmd:ap.error("command required")
    cache=args.cache_dir or project_cache_dir()
    if args.cmd=="put":
        print(json.dumps(put(cache,args.kind,args.fingerprint,args.artifact,json.loads(args.meta_json),args.ttl_seconds),indent=2));return 0
    payload=get(cache,args.kind,args.fingerprint);print(json.dumps(payload,indent=2));return 0 if payload["hit"] else 6

if __name__=="__main__":
    raise SystemExit(main())
