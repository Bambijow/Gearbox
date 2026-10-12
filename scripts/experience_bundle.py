#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

MANIFEST="experience-bundle.json"
KINDS={"screenshot","accessibility","console","network","performance","interaction","playback","dom","other"}

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def canonical_hash(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def load(root:Path)->dict:
    return json.loads((root/MANIFEST).read_text(encoding="utf-8"))

def save(root:Path,data:dict)->None:
    root.mkdir(parents=True,exist_ok=True)
    tmp=root/(MANIFEST+".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,root/MANIFEST)

def init_bundle(root:Path,target:str,sha:str|None,profile:str,scenario_path:str|None,environment:dict)->dict:
    scenario_text=""
    if scenario_path:
        scenario_text=Path(scenario_path).read_text(encoding="utf-8")
    seed={"target":target,"profile":profile,"scenario":scenario_text,"environment":environment}
    data={
        "schema_version":1,
        "status":"DRAFT",
        "target":target,
        "sha":sha,
        "profile":profile,
        "scenario_path":scenario_path,
        "scenario_fingerprint":canonical_hash(seed),
        "environment":environment,
        "artifacts":{},
        "created_at":int(time.time()),
    }
    save(root,data); return data

def add_artifact(root:Path,kind:str,path_str:str,meta:dict)->dict:
    if kind not in KINDS: raise SystemExit(f"unknown artifact kind: {kind}")
    data=load(root)
    path=Path(path_str).resolve()
    if not path.is_file(): raise SystemExit(f"artifact missing: {path}")
    item={"path":str(path),"sha256":sha256_file(path),"bytes":path.stat().st_size,"meta":meta}
    data.setdefault("artifacts",{}).setdefault(kind,[]).append(item)
    data["status"]="DRAFT"
    save(root,data); return item

def verify_bundle(root:Path)->list[str]:
    data=load(root); errors=[]
    for kind,items in data.get("artifacts",{}).items():
        for item in items:
            p=Path(item["path"])
            if not p.is_file():
                errors.append(f"{kind}: missing {p}"); continue
            if sha256_file(p)!=item.get("sha256"):
                errors.append(f"{kind}: hash mismatch {p}")
    return errors

def finalize(root:Path,required:list[str])->dict:
    data=load(root)
    errors=verify_bundle(root)
    for kind in required:
        if not data.get("artifacts",{}).get(kind):
            errors.append(f"required artifact kind missing: {kind}")
    if errors:
        raise SystemExit("; ".join(errors))
    fingerprint_input={
        "target":data.get("target"),
        "profile":data.get("profile"),
        "scenario_fingerprint":data.get("scenario_fingerprint"),
        "environment":data.get("environment"),
        "artifacts":{
            k:[{"sha256":x["sha256"],"meta":x.get("meta",{})} for x in v]
            for k,v in sorted(data.get("artifacts",{}).items())
        },
    }
    data["bundle_fingerprint"]=canonical_hash(fingerprint_input)
    data["status"]="READY"
    data["finalized_at"]=int(time.time())
    save(root,data); return data

def self_test()->None:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"bundle"; art=Path(td)/"desktop.txt"; art.write_text("pixels")
        data=init_bundle(root,"/settings","abc","standard",None,{"viewport":"desktop"})
        assert data["status"]=="DRAFT"
        add_artifact(root,"screenshot",str(art),{"viewport":"1440x900"})
        final=finalize(root,["screenshot"])
        assert final["status"]=="READY" and final["bundle_fingerprint"]
        assert verify_bundle(root)==[]
        art.write_text("changed")
        assert verify_bundle(root)
    print("PASS: experience-bundle self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Create one reusable runtime evidence bundle for multiple Gearbox quality gates.")
    sp=ap.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("init"); a.add_argument("--dir",required=True); a.add_argument("--target",required=True); a.add_argument("--sha"); a.add_argument("--profile",default="standard"); a.add_argument("--scenario"); a.add_argument("--environment-json",default="{}")
    a=sp.add_parser("add"); a.add_argument("--dir",required=True); a.add_argument("--kind",required=True,choices=sorted(KINDS)); a.add_argument("--path",required=True); a.add_argument("--meta-json",default="{}")
    a=sp.add_parser("finalize"); a.add_argument("--dir",required=True); a.add_argument("--require-kind",action="append",default=[])
    a=sp.add_parser("verify"); a.add_argument("--dir",required=True)
    a=sp.add_parser("show"); a.add_argument("--dir",required=True)
    sp.add_parser("self-test")
    args=ap.parse_args()
    if args.cmd=="self-test":
        self_test(); return 0
    root=Path(args.dir)
    if args.cmd=="init":
        env=json.loads(args.environment_json)
        print(json.dumps(init_bundle(root,args.target,args.sha,args.profile,args.scenario,env),indent=2)); return 0
    if args.cmd=="add":
        meta=json.loads(args.meta_json)
        print(json.dumps(add_artifact(root,args.kind,args.path,meta),indent=2)); return 0
    if args.cmd=="finalize":
        print(json.dumps(finalize(root,args.require_kind),indent=2)); return 0
    if args.cmd=="verify":
        errors=verify_bundle(root); print(json.dumps({"valid":not errors,"errors":errors},indent=2)); return 0 if not errors else 6
    print(json.dumps(load(root),indent=2)); return 0

if __name__=="__main__":
    raise SystemExit(main())
