#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA_VERSION=6
DEFAULT_BUDGETS={
    "max_cycles":3,
    "max_worker_dispatches":10,
    "max_codex_dispatches":12,
    "max_review_dispatches":14,
    "max_model_escalations":3,
    "max_pr_repair_cycles":3,
    "max_total_tokens":None,
    "max_reported_cost_usd":None,
}

def load(p): return json.loads(p.read_text()) if p.exists() else None
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    os.replace(tmp,p)
def state_path(run): return Path(run)/"state.json"
def die(msg,code=2):
    print("run-state:",msg,file=sys.stderr)
    raise SystemExit(code)

def default_plan_approval(required=True):
    return {
        "required":required,
        "status":"UNSET",
        "plan_path":None,
        "plan_resolved":None,
        "plan_sha256":None,
        "approved_sha256":None,
        "requested_at":None,
        "approved_at":None,
        "approved_by":None,
    }

def normalize(d):
    changed=False
    if d.get("schema_version",1)<SCHEMA_VERSION:
        d["schema_version"]=SCHEMA_VERSION; changed=True
    if "clarification" not in d:
        d["clarification"]={"status":"UNSET","round":0,"questions":[],"answers":{}}; changed=True
    if "plan_approval" not in d:
        beyond_plan=d.get("phase") in {"IMPLEMENT","INTEGRATE","SIMPLIFY","REVIEW","VERIFY","LEARN","SHIP","POST_PR","DONE"} or bool(d.get("github",{}).get("pr"))
        d["plan_approval"]=default_plan_approval(required=not beyond_plan)
        if beyond_plan:
            d["plan_approval"]["status"]="LEGACY_NOT_REQUIRED"
        changed=True
    else:
        defaults=default_plan_approval(required=d["plan_approval"].get("required",True))
        for k,v in defaults.items():
            if k not in d["plan_approval"]:
                d["plan_approval"][k]=v; changed=True
    if "blocker" not in d:
        d["blocker"]=None; changed=True
    if "orchestration" not in d:
        d["orchestration"]={"mode":"delegated-control-plane","product_writes":"workers-only"}; changed=True
    if "repair_findings" not in d:
        d["repair_findings"]={"policy":{"same_strategy_limit":2,"max_attempts_per_finding":5},"items":{}}; changed=True
    d.setdefault("budgets",{})
    for k,v in DEFAULT_BUDGETS.items():
        if k not in d["budgets"]:
            d["budgets"][k]=v; changed=True
    d.setdefault("usage",{})
    for k in ["worker_dispatches","codex_dispatches","review_dispatches","model_escalations","pr_repair_cycles"]:
        if k not in d["usage"]:
            d["usage"][k]=0; changed=True
    return d,changed

def init(run,run_id):
    p=state_path(run)
    if p.exists():
        d=load(p); d,changed=normalize(d)
        if changed:
            d["updated_at"]=int(time.time()); save(p,d)
        return d
    d={
        "schema_version":SCHEMA_VERSION,
        "run_id":run_id,
        "status":"ACTIVE",
        "phase":"INTAKE",
        "cycle":0,
        "source":{},
        "git":{"base_sha":None,"head_sha":None,"branch":None},
        "github":{"issue":None,"pr":None,"technical_comment_id":None},
        "completed":{},
        "pending":[],
        "worktrees":[],
        "budgets":DEFAULT_BUDGETS.copy(),
        "usage":{"worker_dispatches":0,"codex_dispatches":0,"review_dispatches":0,"model_escalations":0,"pr_repair_cycles":0},
        "model_policy":{},
        "model_assignments":{},
        "orchestration":{"mode":"delegated-control-plane","product_writes":"workers-only"},
        "repair_findings":{"policy":{"same_strategy_limit":2,"max_attempts_per_finding":5},"items":{}},
        "clarification":{"status":"UNSET","round":0,"questions":[],"answers":{}},
        "plan_approval":default_plan_approval(required=True),
        "blocker":None,
        "learning":{},
        "last_error":None,
        "updated_at":int(time.time()),
    }
    save(p,d)
    return d

def read_json_file(path):
    try: return json.loads(Path(path).read_text())
    except Exception as e: die(f"cannot read JSON file {path}: {e}")

def plan_file(path_value):
    p=Path(path_value)
    if not p.is_absolute():
        p=(Path.cwd()/p).resolve()
    return p

def digest_file(path_value):
    p=plan_file(path_value)
    if not p.is_file():
        die(f"plan file missing: {p}",5)
    return hashlib.sha256(p.read_bytes()).hexdigest(),p

def plan_gate_problem(d):
    pa=d.get("plan_approval") or {}
    if not pa.get("required"):
        return None
    if pa.get("status")!="APPROVED":
        return "plan approval is required before implementation"
    resolved=pa.get("plan_resolved") or pa.get("plan_path")
    if not resolved:
        return "approved plan has no recorded path"
    p=Path(resolved)
    if not p.is_file():
        return f"approved plan file is missing: {p}"
    current=hashlib.sha256(p.read_bytes()).hexdigest()
    if current!=pa.get("approved_sha256"):
        return "approved plan changed after approval"
    return None

def mark_plan_stale(d,reason):
    pa=d.setdefault("plan_approval",default_plan_approval(required=True))
    pa["status"]="PENDING"
    pa["approved_at"]=None
    pa["approved_by"]=None
    pa["approved_sha256"]=None
    d["phase"]="PLAN"
    d["status"]="AWAITING_APPROVAL"
    d["blocker"]={"code":"PLAN_APPROVAL_REQUIRED","message":reason}
    d["pending"]=[x for x in d.get("pending",[]) if x!="plan-approval"]+["plan-approval"]

def set_plan_approval(d,plan,auto=False):
    digest,resolved=digest_file(plan)
    now=int(time.time())
    pa=default_plan_approval(required=not auto)
    pa.update({
        "required":not auto,
        "status":"AUTO_APPROVED" if auto else "PENDING",
        "plan_path":str(plan),
        "plan_resolved":str(resolved),
        "plan_sha256":digest,
        "approved_sha256":digest if auto else None,
        "requested_at":now,
        "approved_at":now if auto else None,
        "approved_by":"auto" if auto else None,
    })
    d["plan_approval"]=pa
    if auto:
        if (d.get("blocker") or {}).get("code")=="PLAN_APPROVAL_REQUIRED":
            d["blocker"]=None
        d["pending"]=[x for x in d.get("pending",[]) if x!="plan-approval"]
        d["status"]="ACTIVE"
        d["phase"]="IMPLEMENT"
    else:
        d["status"]="AWAITING_APPROVAL"
        d["phase"]="PLAN"
        d["blocker"]={
            "code":"PLAN_APPROVAL_REQUIRED",
            "message":"Review and approve the exact persisted plan before implementation dispatch",
        }
        d["pending"]=[x for x in d.get("pending",[]) if x!="plan-approval"]+["plan-approval"]
    return pa

def approve_plan(d,approved_by="user"):
    pa=d.get("plan_approval") or {}
    if not pa.get("required"):
        if pa.get("status")=="AUTO_APPROVED":
            return pa
        die("this run does not require plan approval",5)
    if not pa.get("plan_resolved"):
        die("no persisted plan is awaiting approval",5)
    p=Path(pa["plan_resolved"])
    if not p.is_file():
        mark_plan_stale(d,"Persisted plan is missing; regenerate and present it again")
        die(f"plan file missing: {p}",5)
    current=hashlib.sha256(p.read_bytes()).hexdigest()
    if pa.get("status")=="APPROVED" and current==pa.get("approved_sha256"):
        return pa
    if current!=pa.get("plan_sha256"):
        mark_plan_stale(d,"Plan changed after it was presented; present the updated plan and request approval again")
        die("plan changed after approval was requested; call plan-await again after presenting the new plan",5)
    pa["status"]="APPROVED"
    pa["approved_sha256"]=current
    pa["approved_at"]=int(time.time())
    pa["approved_by"]=approved_by
    d["plan_approval"]=pa
    if (d.get("blocker") or {}).get("code")=="PLAN_APPROVAL_REQUIRED":
        d["blocker"]=None
    d["pending"]=[x for x in d.get("pending",[]) if x!="plan-approval"]
    d["status"]="ACTIVE"
    d["phase"]="IMPLEMENT"
    return pa

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        run=root/"run"
        plan=root/"dag.yaml"
        plan.write_text("tasks: [A]\n",encoding="utf-8")
        d=init(run,"test")
        assert d["plan_approval"]["required"] is True
        assert plan_gate_problem(d)
        set_plan_approval(d,str(plan),auto=False)
        assert d["status"]=="AWAITING_APPROVAL"
        assert d["plan_approval"]["status"]=="PENDING"
        assert plan_gate_problem(d)
        approve_plan(d,"test-user")
        assert d["status"]=="ACTIVE"
        assert d["plan_approval"]["status"]=="APPROVED"
        assert plan_gate_problem(d) is None
        plan.write_text("tasks: [A, B]\n",encoding="utf-8")
        assert plan_gate_problem(d)=="approved plan changed after approval"
        mark_plan_stale(d,"changed")
        assert d["status"]=="AWAITING_APPROVAL"
        set_plan_approval(d,str(plan),auto=True)
        assert d["plan_approval"]["status"]=="AUTO_APPROVED"
        assert plan_gate_problem(d) is None
    print("PASS: run-state plan approval self-test")
    return 0

def main():
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("init"); a.add_argument("--run-dir",required=True); a.add_argument("--run-id",required=True)
    a=sp.add_parser("show"); a.add_argument("--run-dir",required=True)
    a=sp.add_parser("transition"); a.add_argument("--run-dir",required=True); a.add_argument("--phase",required=True); a.add_argument("--status"); a.add_argument("--cycle",type=int)
    a=sp.add_parser("set"); a.add_argument("--run-dir",required=True); a.add_argument("--key",required=True); a.add_argument("--json",required=True)
    a=sp.add_parser("consume"); a.add_argument("--run-dir",required=True); a.add_argument("--kind",choices=["worker","codex","review","model-escalation","pr-repair"],required=True); a.add_argument("--count",type=int,default=1)
    a=sp.add_parser("lock"); a.add_argument("--run-dir",required=True); a.add_argument("--break-stale",action="store_true"); a.add_argument("--stale-seconds",type=int,default=21600)
    a=sp.add_parser("unlock"); a.add_argument("--run-dir",required=True)
    a=sp.add_parser("cleanup-worktrees"); a.add_argument("--run-dir",required=True); a.add_argument("--repo",default=".")
    a=sp.add_parser("spec-block"); a.add_argument("--run-dir",required=True); a.add_argument("--clarification-file",required=True); a.add_argument("--message",default="Material product decisions are required before planning")
    a=sp.add_parser("spec-resolve"); a.add_argument("--run-dir",required=True); a.add_argument("--answers-file",required=True)
    a=sp.add_parser("plan-await"); a.add_argument("--run-dir",required=True); a.add_argument("--plan",required=True); a.add_argument("--auto",action="store_true")
    a=sp.add_parser("plan-approve"); a.add_argument("--run-dir",required=True); a.add_argument("--approved-by",default="user")
    a=sp.add_parser("plan-check"); a.add_argument("--run-dir",required=True)
    sp.add_parser("self-test")

    args=ap.parse_args()
    if args.cmd=="self-test":
        return self_test()

    run=Path(args.run_dir)
    p=state_path(run)
    if args.cmd=="init":
        d=init(run,args.run_id)
        print(json.dumps(d,indent=2))
        return 0
    if not p.exists():
        die("state.json missing; run init first")

    d=load(p)
    d,changed=normalize(d)
    if changed:
        d["updated_at"]=int(time.time()); save(p,d)

    if args.cmd=="show":
        print(json.dumps(d,indent=2,sort_keys=True)); return 0

    if args.cmd=="lock":
        lp=run/".lock"; run.mkdir(parents=True,exist_ok=True)
        if lp.exists():
            try:
                old=json.loads(lp.read_text()); age=time.time()-old.get("created_at",time.time())
            except Exception:
                old={}; age=0
            owner_alive=False
            if old.get("host")==socket.gethostname() and isinstance(old.get("pid"),int):
                try: os.kill(old["pid"],0); owner_alive=True
                except (ProcessLookupError,PermissionError): owner_alive=False
            if not (args.break_stale and age>args.stale_seconds and not owner_alive):
                die(f"lock exists: {old}",3)
            lp.unlink()
        fd=os.open(lp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        meta={"pid":os.getpid(),"host":socket.gethostname(),"created_at":time.time()}
        os.write(fd,json.dumps(meta).encode()); os.close(fd)
        print(json.dumps(meta)); return 0

    if args.cmd=="unlock":
        (run/".lock").unlink(missing_ok=True); return 0

    if args.cmd=="cleanup-worktrees":
        repo=Path(args.repo).resolve(); kept=[]; removed=[]
        for wt in d.get("worktrees",[]):
            path=Path(wt.get("path",""))
            if not path.exists(): continue
            integrated=bool(wt.get("integrated"))
            clean=subprocess.run(["git","-C",str(path),"status","--porcelain"],capture_output=True,text=True,check=False).stdout.strip()==""
            if not (integrated or clean):
                kept.append(wt); continue
            proc=subprocess.run(["git","-C",str(repo),"worktree","remove","--force",str(path)],capture_output=True,text=True,check=False)
            if proc.returncode==0: removed.append(str(path))
            else: kept.append(wt)
        d["worktrees"]=kept
        d["updated_at"]=int(time.time())
        save(p,d)
        print(json.dumps({"removed":removed,"kept":kept},indent=2))
        return 0

    if args.cmd=="spec-block":
        clarification=read_json_file(args.clarification_file)
        questions=clarification.get("questions",[])
        if not questions:
            die("spec-block requires at least one unresolved question")
        clarification["status"]="NEEDS_INPUT"
        clarification["round"]=max(int(clarification.get("round",0)),int(d.get("clarification",{}).get("round",0))+1)
        clarification.setdefault("answers",{})
        d["phase"]="SPEC"; d["status"]="BLOCKED"; d["clarification"]=clarification
        d["blocker"]={"code":"SPEC_BLOCKED","message":args.message}
        d["pending"]=[f"clarification:{q.get('id','unknown')}" for q in questions]

    elif args.cmd=="spec-resolve":
        if (d.get("blocker") or {}).get("code")!="SPEC_BLOCKED":
            die("run is not SPEC_BLOCKED")
        answers=read_json_file(args.answers_file)
        current=d.get("clarification",{})
        qids={q.get("id") for q in current.get("questions",[]) if q.get("id")}
        missing=sorted(qids-set(answers))
        if missing:
            die(f"missing answers for: {missing}")
        current["answers"]=answers; current["status"]="ANSWERED"
        d["clarification"]=current; d["blocker"]=None; d["status"]="ACTIVE"; d["phase"]="SPEC"; d["pending"]=[]

    elif args.cmd=="plan-await":
        if (d.get("blocker") or {}).get("code")=="SPEC_BLOCKED":
            die("cannot create plan approval gate while SPEC_BLOCKED",5)
        set_plan_approval(d,args.plan,args.auto)

    elif args.cmd=="plan-approve":
        try:
            approve_plan(d,args.approved_by)
        except SystemExit:
            d["updated_at"]=int(time.time()); save(p,d)
            raise

    elif args.cmd=="plan-check":
        problem=plan_gate_problem(d)
        if problem:
            if d.get("plan_approval",{}).get("status")=="APPROVED":
                mark_plan_stale(d,problem)
                d["updated_at"]=int(time.time()); save(p,d)
            print(json.dumps({"approved":False,"reason":problem,"plan_approval":d.get("plan_approval")},indent=2))
            return 5
        print(json.dumps({"approved":True,"plan_approval":d.get("plan_approval")},indent=2))
        return 0

    elif args.cmd=="transition":
        d["phase"]=args.phase
        if args.status: d["status"]=args.status
        if args.cycle is not None: d["cycle"]=args.cycle

    elif args.cmd=="set":
        cur=d; parts=args.key.split(".")
        for k in parts[:-1]:
            cur=cur.setdefault(k,{})
        cur[parts[-1]]=json.loads(args.json)

    elif args.cmd=="consume":
        if d.get("status")=="BLOCKED" and (d.get("blocker") or {}).get("code")=="SPEC_BLOCKED" and args.kind in ("worker","codex","review","model-escalation"):
            die("cannot consume implementation/model/review budget while SPEC_BLOCKED",5)
        if args.kind in ("worker","codex","review","model-escalation"):
            problem=plan_gate_problem(d)
            if problem:
                if d.get("plan_approval",{}).get("status")=="APPROVED":
                    mark_plan_stale(d,problem)
                    d["updated_at"]=int(time.time()); save(p,d)
                die(f"cannot consume {args.kind} budget: {problem}",5)
        mapping={
            "worker":("worker_dispatches","max_worker_dispatches"),
            "codex":("codex_dispatches","max_codex_dispatches"),
            "review":("review_dispatches","max_review_dispatches"),
            "model-escalation":("model_escalations","max_model_escalations"),
            "pr-repair":("pr_repair_cycles","max_pr_repair_cycles"),
        }
        uk,bk=mapping[args.kind]
        new=d["usage"].get(uk,0)+args.count
        limit=d["budgets"].get(bk)
        if limit is not None and new>limit:
            die(f"budget exceeded: {uk} {new}>{limit}",4)
        d["usage"][uk]=new

    d["updated_at"]=int(time.time())
    save(p,d)
    print(json.dumps(d,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
