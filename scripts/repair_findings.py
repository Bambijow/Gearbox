#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path

DEFAULT_POLICY={"same_strategy_limit":2,"max_attempts_per_finding":5}

def die(msg: str, code: int=2) -> None:
    print(json.dumps({"allowed":False,"action":"error","reason":msg}))
    raise SystemExit(code)

def load(path: Path) -> dict:
    if not path.exists():
        die(f"state missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def save(path: Path, data: dict) -> None:
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def store(data: dict) -> dict:
    rf=data.setdefault("repair_findings",{})
    rf.setdefault("policy",DEFAULT_POLICY.copy())
    rf.setdefault("items",{})
    return rf

def open_finding(data: dict, fid: str, source: str, summary: str, severity: str) -> dict:
    items=store(data)["items"]
    item=items.setdefault(fid,{
        "id":fid,"source":source,"summary":summary,"severity":severity,
        "status":"OPEN","attempts":[],"opened_at":int(time.time())
    })
    item.update({"source":source,"summary":summary,"severity":severity})
    return item

def attempt(data: dict, fid: str, strategy: str, worker: str|None, model: str|None) -> tuple[dict,int]:
    rf=store(data)
    item=rf["items"].get(fid)
    if not item:
        die(f"unknown finding: {fid}")
    if item.get("status")=="RESOLVED":
        die(f"finding already resolved: {fid}")
    policy=rf["policy"]
    attempts=item.setdefault("attempts",[])
    if len(attempts)>=int(policy["max_attempts_per_finding"]):
        item["status"]="ADJUDICATION_REQUIRED"
        return {"allowed":False,"action":"adjudicate","finding":fid,"attempts":len(attempts)},7
    same=sum(1 for a in attempts if a.get("strategy")==strategy and a.get("outcome")!="strategy-blocked")
    if same>=int(policy["same_strategy_limit"]):
        item["status"]="REDIAGNOSE_REQUIRED"
        item["last_blocked_strategy"]=strategy
        return {
            "allowed":False,"action":"rediagnose","finding":fid,
            "strategy":strategy,"same_strategy_attempts":same
        },6
    rec={
        "n":len(attempts)+1,"strategy":strategy,"worker":worker,"model":model,
        "started_at":int(time.time()),"outcome":"in-progress"
    }
    attempts.append(rec)
    item["status"]="IN_REPAIR"
    return {"allowed":True,"action":"dispatch","finding":fid,"attempt":rec["n"]},0

def result(data: dict, fid: str, outcome: str, note: str|None) -> dict:
    item=store(data)["items"].get(fid)
    if not item or not item.get("attempts"):
        die(f"no active attempt for: {fid}")
    a=item["attempts"][-1]
    if a.get("outcome")!="in-progress":
        die(f"latest attempt already closed: {fid}")
    a["outcome"]=outcome
    a["finished_at"]=int(time.time())
    if note:
        a["note"]=note
    item["status"]="OPEN" if outcome!="fixed" else "RESOLVED"
    if outcome=="fixed":
        item["resolved_at"]=int(time.time())
    return {"finding":fid,"status":item["status"],"attempt":a["n"],"outcome":outcome}

def resolve(data: dict, fid: str, ruling: str) -> dict:
    item=store(data)["items"].get(fid)
    if not item:
        die(f"unknown finding: {fid}")
    item["status"]="RESOLVED"
    item["ruling"]=ruling
    item["resolved_at"]=int(time.time())
    return {"finding":fid,"status":"RESOLVED","ruling":ruling}

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"state.json"
        p.write_text('{"run_id":"t"}\n',encoding="utf-8")
        d=load(p)
        open_finding(d,"REV-1","review","bug","Important")
        assert attempt(d,"REV-1","same","w","m")[1]==0
        result(d,"REV-1","failed","still red")
        assert attempt(d,"REV-1","same","w","m")[1]==0
        result(d,"REV-1","failed","still red")
        payload,code=attempt(d,"REV-1","same","w","m")
        assert code==6 and payload["action"]=="rediagnose"
        payload,code=attempt(d,"REV-1","new-strategy","w","m")
        assert code==0 and payload["allowed"]
    print("PASS: repair-findings self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Maintain Gearbox finding-scoped repair circuit breakers.")
    ap.add_argument("--self-test",action="store_true")
    sub=ap.add_subparsers(dest="cmd")
    for name in ("open","attempt","result","resolve","show"):
        s=sub.add_parser(name)
        s.add_argument("--run-dir",required=True,type=Path)
        if name in ("open","attempt","result","resolve"):
            s.add_argument("--id",required=True)
        if name=="open":
            s.add_argument("--source",required=True)
            s.add_argument("--summary",required=True)
            s.add_argument("--severity",default="Important")
        elif name=="attempt":
            s.add_argument("--strategy",required=True)
            s.add_argument("--worker")
            s.add_argument("--model")
        elif name=="result":
            s.add_argument("--outcome",choices=("fixed","failed","blocked"),required=True)
            s.add_argument("--note")
        elif name=="resolve":
            s.add_argument("--ruling",required=True)
    a=ap.parse_args()
    if a.self_test:
        self_test()
        return 0
    if not a.cmd:
        ap.error("command required")
    p=a.run_dir/"state.json"
    d=load(p)
    store(d)
    code=0
    if a.cmd=="open":
        payload=open_finding(d,a.id,a.source,a.summary,a.severity)
    elif a.cmd=="attempt":
        payload,code=attempt(d,a.id,a.strategy,a.worker,a.model)
    elif a.cmd=="result":
        payload=result(d,a.id,a.outcome,a.note)
    elif a.cmd=="resolve":
        payload=resolve(d,a.id,a.ruling)
    else:
        payload=d["repair_findings"]
    save(p,d)
    print(json.dumps(payload,indent=2))
    return code

if __name__=="__main__":
    raise SystemExit(main())
