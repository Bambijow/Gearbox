#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import shlex
import shutil
import statistics
import subprocess
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_RUNS=ROOT/"benchmarks"/"agentic"/"runs"
CODE_EXT={".py",".js",".jsx",".ts",".tsx",".go",".rs",".java",".rb",".php",".cs",".sh"}

def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")

def load_manifest(path: Path) -> dict:
    try: data=json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: fail(f"{path}: invalid JSON: {exc}")
    if data.get("schema_version")!=1: fail(f"{path}: schema_version must be 1")
    for key in ("name","repo","arms","models","runs","tasks"):
        if key not in data: fail(f"{path}: missing {key}")
    repo=data["repo"]
    if not isinstance(repo,dict) or not (repo.get("path") or repo.get("url")) or not repo.get("commit"):
        fail(f"{path}: repo needs path|url and pinned commit")
    if not isinstance(data["arms"],dict) or len(data["arms"])<2:
        fail(f"{path}: define at least two arms")
    if not isinstance(data["models"],list) or not data["models"]:
        fail(f"{path}: models must be non-empty")
    if not isinstance(data["runs"],int) or data["runs"]<1:
        fail(f"{path}: runs must be >=1")
    if not isinstance(data["tasks"],list) or not data["tasks"]:
        fail(f"{path}: tasks must be non-empty")
    ids=set()
    for t in data["tasks"]:
        for key in ("id","prompt","correctness_command","safety_command"):
            if not isinstance(t.get(key),str) or not t[key].strip():
                fail(f"{path}: task missing non-empty {key}")
        if t["id"] in ids: fail(f"{path}: duplicate task id {t['id']}")
        ids.add(t["id"])
    return data

def run_cmd(argv:list[str],cwd:Path,env:dict|None=None,timeout:int=600) -> subprocess.CompletedProcess:
    return subprocess.run(argv,cwd=str(cwd),env=env,capture_output=True,text=True,timeout=timeout,check=False)

def prepare_workspace(repo:dict, dest:Path) -> str:
    source=repo.get("path") or repo.get("url")
    clone=run_cmd(["git","clone","--quiet","--no-hardlinks",str(source),str(dest)],dest.parent,timeout=180)
    if clone.returncode!=0: fail(f"clone failed: {clone.stderr[-800:]}")
    checkout=run_cmd(["git","checkout","--quiet",repo["commit"]],dest)
    if checkout.returncode!=0: fail(f"checkout {repo['commit']} failed: {checkout.stderr[-800:]}")
    sha=run_cmd(["git","rev-parse","HEAD"],dest).stdout.strip()
    if not sha: fail("unable to resolve benchmark workspace SHA")
    return sha

def diff_stats(ws:Path) -> dict:
    run_cmd(["git","add","-A"],ws)
    out=run_cmd(["git","diff","--cached","--numstat","HEAD"],ws).stdout
    added=deleted=src_added=files=0
    for line in out.splitlines():
        parts=line.split("\t")
        if len(parts)!=3 or parts[0]=="-" or parts[1]=="-": continue
        a,d,path=parts
        try: ai,di=int(a),int(d)
        except ValueError: continue
        if path.startswith(".gearbox/") or path.startswith("benchmarks/agentic/runs/"):
            continue
        added+=ai; deleted+=di; files+=1
        if Path(path).suffix.lower() in CODE_EXT and not any(x in path.lower() for x in ("/test/","/tests/","_test.","test_")):
            src_added+=ai
    return {"changed_files":files,"added_lines":added,"deleted_lines":deleted,"source_added_lines":src_added}


def gearbox_metrics(ws:Path) -> dict:
    runs=ws/".gearbox"/"runs"
    if not runs.exists():
        return {}
    states=sorted(runs.glob("*/state.json"),key=lambda p:p.stat().st_mtime,reverse=True)
    if not states:
        return {}
    try:
        state=json.loads(states[0].read_text(encoding="utf-8"))
    except Exception:
        return {}
    usage=state.get("usage") if isinstance(state.get("usage"),dict) else {}
    final_review=state.get("final_review") if isinstance(state.get("final_review"),dict) else {}
    return {
        "gearbox_status":state.get("status"),
        "gearbox_phase":state.get("phase"),
        "gearbox_cycle":state.get("cycle"),
        "worker_dispatches":usage.get("worker_dispatches"),
        "codex_dispatches":usage.get("codex_dispatches"),
        "review_dispatches":usage.get("review_dispatches"),
        "model_escalations":usage.get("model_escalations"),
        "pr_repair_cycles":usage.get("pr_repair_cycles"),
        "final_review_mode":final_review.get("mode"),
    }

def runner_payload(task:dict, arm_name:str, arm:dict, model:str, run_index:int, ws:Path) -> dict:
    plugin=arm.get("plugin_dir")
    if plugin is not None:
        plugin=str(Path(plugin).expanduser().resolve())
    return {
        "schema_version":1,
        "task_id":task["id"],
        "prompt":task["prompt"],
        "arm":arm_name,
        "model":model,
        "run_index":run_index,
        "workspace":str(ws.resolve()),
        "plugin_dir":plugin,
        "timeout_seconds":int(task.get("timeout_seconds",arm.get("timeout_seconds",600))),
        "append_system_prompt":arm.get("append_system_prompt"),
    }

def invoke_runner(runner:list[str], payload:dict, ws:Path) -> tuple[dict,str]:
    env={**os.environ,"GEARBOX_BENCH_CELL":"1"}
    proc=subprocess.run(
        runner,input=json.dumps(payload),text=True,capture_output=True,cwd=str(ws),env=env,
        timeout=int(payload["timeout_seconds"])+30,check=False
    )
    if proc.returncode!=0:
        return {"runner_ok":False,"runner_exit_code":proc.returncode},proc.stderr[-4000:]
    try: data=json.loads(proc.stdout)
    except Exception:
        return {"runner_ok":False,"runner_exit_code":proc.returncode,"raw_stdout":proc.stdout[-4000:]},proc.stderr[-4000:]
    data["runner_ok"]=True
    data["runner_exit_code"]=proc.returncode
    return data,proc.stderr[-4000:]

def check_command(command:str,ws:Path,timeout:int=120) -> dict:
    start=time.time()
    proc=subprocess.run(command,shell=True,cwd=str(ws),capture_output=True,text=True,timeout=timeout,check=False)
    return {
        "pass":proc.returncode==0,
        "exit_code":proc.returncode,
        "duration_seconds":round(time.time()-start,3),
        "stdout":proc.stdout[-2000:],
        "stderr":proc.stderr[-2000:],
    }

def run_cell(manifest:dict, task:dict, arm_name:str, model:str, idx:int, out:Path, runner:list[str]) -> dict:
    ws=out/f"{task['id']}__{arm_name}__{model}__{idx}"
    ws.parent.mkdir(parents=True,exist_ok=True)
    base_sha=prepare_workspace(manifest["repo"],ws)
    payload=runner_payload(task,arm_name,manifest["arms"][arm_name],model,idx,ws)
    (ws/"_gearbox_bench_request.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    result,stderr=invoke_runner(runner,payload,ws)
    (ws/"_gearbox_bench_runner.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    (ws/"_gearbox_bench_runner.stderr.txt").write_text(stderr,encoding="utf-8")
    correctness=check_command(task["correctness_command"],ws,int(task.get("score_timeout_seconds",120)))
    safety=check_command(task["safety_command"],ws,int(task.get("score_timeout_seconds",120)))
    metrics=diff_stats(ws)
    gearbox=gearbox_metrics(ws)
    record={
        "task":task["id"],"arm":arm_name,"model":model,"run":idx,"base_sha":base_sha,
        "runner_ok":bool(result.get("runner_ok")),
        "correct":bool(correctness["pass"]),"safe":bool(safety["pass"]),
        "correctness":correctness,"safety":safety,**metrics,**gearbox,
        "input_tokens":result.get("input_tokens"),
        "output_tokens":result.get("output_tokens"),
        "cached_input_tokens":result.get("cached_input_tokens"),
        "reported_cost_usd":result.get("reported_cost_usd"),
        "duration_seconds":result.get("duration_seconds"),
        "turns":result.get("turns"),
    }
    (ws/"_gearbox_bench_score.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    return record

def aggregate(records:list[dict]) -> list[dict]:
    groups=defaultdict(list)
    for r in records: groups[(r["task"],r["arm"],r["model"])].append(r)
    rows=[]
    for (task,arm,model),cells in sorted(groups.items()):
        n=len(cells)
        gated=[c for c in cells if c["runner_ok"] and c["correct"] and c["safe"]]
        def mean(key):
            vals=[float(c[key]) for c in cells if isinstance(c.get(key),(int,float))]
            return round(statistics.mean(vals),4) if vals else None
        modes=[c.get("final_review_mode") for c in cells if c.get("final_review_mode")]
        rows.append({
            "task":task,"arm":arm,"model":model,"n":n,
            "correct_rate":round(sum(c["correct"] for c in cells)/n,3),
            "safe_rate":round(sum(c["safe"] for c in cells)/n,3),
            "gate_pass_rate":round(len(gated)/n,3),
            "economy_comparable":len(gated)==n,
            "source_added_lines_mean":mean("source_added_lines"),
            "input_tokens_mean":mean("input_tokens"),
            "output_tokens_mean":mean("output_tokens"),
            "cached_input_tokens_mean":mean("cached_input_tokens"),
            "reported_cost_usd_mean":mean("reported_cost_usd"),
            "duration_seconds_mean":mean("duration_seconds"),
            "turns_mean":mean("turns"),
            "worker_dispatches_mean":mean("worker_dispatches"),
            "review_dispatches_mean":mean("review_dispatches"),
            "model_escalations_mean":mean("model_escalations"),
            "repair_cycles_mean":mean("gearbox_cycle"),
            "final_review_modes":sorted(set(modes)),
        })
    return rows

def compare(rows:list[dict], baseline:str, candidate:str) -> list[dict]:
    by={(r["task"],r["model"],r["arm"]):r for r in rows}
    out=[]
    keys=sorted({(r["task"],r["model"]) for r in rows})
    metrics=("source_added_lines_mean","input_tokens_mean","output_tokens_mean","reported_cost_usd_mean","duration_seconds_mean","turns_mean","worker_dispatches_mean","review_dispatches_mean","model_escalations_mean","repair_cycles_mean")
    for task,model in keys:
        b=by.get((task,model,baseline)); c=by.get((task,model,candidate))
        if not b or not c: continue
        item={"task":task,"model":model,"baseline":baseline,"candidate":candidate,
              "correctness_gate":bool(b["economy_comparable"] and c["economy_comparable"])}
        if not item["correctness_gate"]:
            item["economy"]="NOT_COMPARABLE"
        else:
            deltas={}
            for m in metrics:
                bv,cv=b.get(m),c.get(m)
                if bv is None or cv is None or bv==0: continue
                deltas[m+"_pct"]=round((cv-bv)/bv*100,2)
            item["economy"]="COMPARABLE"; item["candidate_vs_baseline_pct"]=deltas
        out.append(item)
    return out

def rescore(run_dir:Path,manifest:dict) -> tuple[list[dict],list[dict]]:
    records=[]
    tasks={t["id"]:t for t in manifest["tasks"]}
    for ws in sorted(p for p in run_dir.iterdir() if p.is_dir()):
        parts=ws.name.split("__")
        if len(parts)!=4 or parts[0] not in tasks: continue
        task_id,arm,model,idx=parts
        runner_path=ws/"_gearbox_bench_runner.json"
        result=json.loads(runner_path.read_text(encoding="utf-8")) if runner_path.exists() else {}
        correctness=check_command(tasks[task_id]["correctness_command"],ws,int(tasks[task_id].get("score_timeout_seconds",120)))
        safety=check_command(tasks[task_id]["safety_command"],ws,int(tasks[task_id].get("score_timeout_seconds",120)))
        records.append({
            "task":task_id,"arm":arm,"model":model,"run":int(idx),
            "runner_ok":bool(result.get("runner_ok",True)),
            "correct":bool(correctness["pass"]),"safe":bool(safety["pass"]),
            "correctness":correctness,"safety":safety,**diff_stats(ws),**gearbox_metrics(ws),
            "input_tokens":result.get("input_tokens"),"output_tokens":result.get("output_tokens"),
            "cached_input_tokens":result.get("cached_input_tokens"),"reported_cost_usd":result.get("reported_cost_usd"),
            "duration_seconds":result.get("duration_seconds"),"turns":result.get("turns"),
        })
    return records,aggregate(records)

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); source=root/"source"; source.mkdir()
        run_cmd(["git","init","--quiet"],source)
        (source/"value.txt").write_text("0\n",encoding="utf-8")
        run_cmd(["git","add","."],source)
        run_cmd(["git","-c","user.email=bench@local","-c","user.name=bench","commit","-qm","base"],source)
        sha=run_cmd(["git","rev-parse","HEAD"],source).stdout.strip()
        runner=root/"runner.py"
        runner.write_text(
            "import json,sys,pathlib\n"
            "r=json.load(sys.stdin); w=pathlib.Path(r['workspace']); (w/'value.txt').write_text('1\\n')\n"
            "print(json.dumps({'input_tokens':10,'output_tokens':2,'reported_cost_usd':0.01,'duration_seconds':0.1,'turns':1}))\n",
            encoding="utf-8",
        )
        manifest={
            "schema_version":1,"name":"selftest","repo":{"path":str(source),"commit":sha},
            "arms":{"baseline":{"plugin_dir":None},"candidate":{"plugin_dir":None}},
            "models":["test"],"runs":1,
            "tasks":[{"id":"flip","prompt":"flip","correctness_command":"test \"$(cat value.txt)\" = 1","safety_command":"test \"$(cat value.txt)\" = 1"}]
        }
        out=root/"runs"; runner_cmd=[shutil.which("python3") or "python3",str(runner)]
        records=[]
        for arm in manifest["arms"]:
            records.append(run_cell(manifest,manifest["tasks"][0],arm,"test",0,out,runner_cmd))
        rows=aggregate(records); cmp=compare(rows,"baseline","candidate")
        assert len(rows)==2 and cmp[0]["correctness_gate"] is True
    print("PASS: agentic-bench self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Run isolated baseline-vs-candidate Gearbox agentic benchmark cells.")
    sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("validate"); a.add_argument("manifest",type=Path)
    a=sub.add_parser("run"); a.add_argument("manifest",type=Path); a.add_argument("--runner",default="python3 benchmarks/agentic/claude_runner.py"); a.add_argument("--out-dir",type=Path); a.add_argument("--workers",type=int,default=2); a.add_argument("--baseline",default="baseline"); a.add_argument("--candidate",default="candidate")
    a=sub.add_parser("rescore"); a.add_argument("manifest",type=Path); a.add_argument("run_dir",type=Path); a.add_argument("--baseline",default="baseline"); a.add_argument("--candidate",default="candidate")
    sub.add_parser("self-test")
    args=ap.parse_args()
    if args.cmd=="self-test": self_test(); return 0
    manifest=load_manifest(args.manifest)
    if args.cmd=="validate":
        print(f"PASS: agentic benchmark manifest ({len(manifest['tasks'])} task(s), {len(manifest['arms'])} arm(s))"); return 0
    if args.cmd=="rescore":
        records,rows=rescore(args.run_dir,manifest); comp=compare(rows,args.baseline,args.candidate)
        (args.run_dir/"results.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")
        (args.run_dir/"summary.json").write_text(json.dumps({"rows":rows,"comparisons":comp},indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"rows":rows,"comparisons":comp},indent=2)); return 0

    runner=shlex.split(args.runner)
    if not runner: fail("empty runner command")
    stamp=dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out=(args.out_dir or DEFAULT_RUNS/stamp).resolve(); out.mkdir(parents=True,exist_ok=True)
    cells=[(task,arm,model,i) for task in manifest["tasks"] for model in manifest["models"] for arm in manifest["arms"] for i in range(manifest["runs"])]
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,args.workers)) as pool:
        futures={pool.submit(run_cell,manifest,t,a,m,i,out,runner):(t["id"],a,m,i) for t,a,m,i in cells}
        for fut in concurrent.futures.as_completed(futures):
            records.append(fut.result())
    rows=aggregate(records); comp=compare(rows,args.baseline,args.candidate)
    metadata={"manifest":str(args.manifest.resolve()),"created_at":int(time.time()),"rows":rows,"comparisons":comp}
    (out/"results.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")
    (out/"summary.json").write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(metadata,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
