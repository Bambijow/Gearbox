#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import context_compiler
import frontier_scheduler
import probe_plan
import quality_plan
import repo_facts_cache
import review_plan
import readonly_pack
import route_task
import test_impact
import verification_plan

def precompute(data:dict,output_dir:Path|None)->dict:
    profile=data.get("quality_profile","standard")
    task_kind=data.get("task_kind")
    expected_paths=data.get("expected_paths",[])
    hints=data.get("surface_hints",[])
    explicit_surfaces=data.get("surfaces",[])
    flags={"baseline_exists":bool(data.get("baseline_exists",False))}

    q=quality_plan.compile_plan(task_kind,profile,explicit_surfaces,expected_paths,hints,flags)
    p=probe_plan.compile_probe(q)
    review=review_plan.compile_review_plan(q,data.get("risk","medium"),task_kind)

    catalog=data.get("verification_catalog") or {"checks":[]}
    v=verification_plan.compile_plan(catalog,expected_paths,q.get("surfaces",[]),profile)
    candidates=[x.get("id") for x in v.get("checks",[]) if x.get("id")]
    if candidates:
        if "test_impact_observations" in data:
            impact_data={"schema_version":1,"observations":data.get("test_impact_observations",[])}
        else:
            impact_data=test_impact.load(
                Path(data["test_impact_file"]) if data.get("test_impact_file") else test_impact.project_cache_dir()
            )
        impact=test_impact.rank(impact_data,candidates,expected_paths)
    else:
        impact={"schema_version":1,"ranked":[],"never_drop_required_checks":True}
    rank_index={x["check_id"]:i for i,x in enumerate(impact.get("ranked",[]))}
    v["checks"].sort(key=lambda x:(rank_index.get(x.get("id"),10**6),x.get("id","")))
    v["historical_impact"]=impact

    dag=data.get("dag") or {"max_parallel_workers":data.get("max_parallel_workers",1),"tasks":[]}
    sched=frontier_scheduler.plan(dag)

    route_results=[]
    for item in data.get("route_requests",[]):
        route_results.append(route_task.route_task(
            item["task_kind"],
            item.get("claude_capabilities",[]),
            item.get("codex_capabilities",[]),
            scope=item.get("scope","surface"),
            comp_policy=item.get("comp_policy","auto"),
            image_generation_available=bool(item.get("image_generation_available",False)),
            image_model=item.get("image_model","gpt-image-2.5-flare"),
            image_edit_model=item.get("image_edit_model","gpt-image-2.5-sunburst"),
        ))

    contexts=[]
    for item in data.get("context_descriptors",[]):
        packet,manifest=context_compiler.compile_packet(item["data"],int(item.get("max_bytes",12288)))
        record={"id":item["id"],"manifest":manifest}
        if output_dir:
            output_dir.mkdir(parents=True,exist_ok=True)
            packet_path=output_dir/f"{item['id']}.packet.md"
            manifest_path=output_dir/f"{item['id']}.packet.json"
            packet_path.write_text(packet,encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
            record["packet_path"]=str(packet_path)
            record["manifest_path"]=str(manifest_path)
        contexts.append(record)

    facts=None
    repo_root=Path(data.get("repo_root","."))
    if data.get("repo_facts_auto") or data.get("repo_fact_paths"):
        facts=repo_facts_cache.compile_facts(
            repo_root,
            data.get("repo_fact_paths",[]),
            bool(data.get("repo_facts_auto",False)),
            Path(data["repo_facts_cache_dir"]) if data.get("repo_facts_cache_dir") else repo_facts_cache.repo_cache_root(),
        )

    packed=readonly_pack.pack(data.get("readonly_tasks",[])) if data.get("readonly_tasks") else {"schema_version":1,"input_count":0,"dispatch_count":0,"dispatches_saved":0,"dispatches":[]}

    result={
        "schema_version":1,
        "side_effect_class":"deterministic-artifacts-only",
        "model_calls":0,
        "worker_dispatches":0,
        "quality_plan":q,
        "probe_plan":p,
        "review_plan":review,
        "verification_plan":v,
        "readonly_packs":packed,
        "scheduler":sched,
        "routes":route_results,
        "context_packets":contexts,
        "repo_facts":facts,
        "approval_safe":True,
        "live_capability_preflight_required_after_approval":True,
    }
    return result

def self_test():
    data={
      "quality_profile":"standard",
      "task_kind":"web-design",
      "expected_paths":["src/components/Button.tsx"],
      "baseline_exists":False,
      "verification_catalog":{"checks":[
        {"id":"ui","kind":"test","command":"vitest Button","cost":"low","surfaces":["user_ui"]}
      ]},
      "dag":{"max_parallel_workers":2,"tasks":[
        {"id":"A","status":"READY","dependencies":[],"owned_paths":["src/a"],"risk":"low"}
      ]},
      "route_requests":[{"task_kind":"web-design","scope":"surface","claude_capabilities":[],"codex_capabilities":[]}],
      "context_descriptors":[{"id":"A","max_bytes":2048,"data":{
        "role":"worker","outcome":"button","task":"implement","required_capabilities":[],"ownership":["src/a"],"verify":["vitest"]
      }}],
    }
    with __import__("tempfile").TemporaryDirectory() as td:
        r=precompute(data,Path(td))
        assert r["model_calls"]==0 and r["worker_dispatches"]==0
        assert r["quality_plan"]["quality_plan_id"]
        assert r["review_plan"]["required_gate_count"]>=1
        assert r["scheduler"]["dispatch_units"][0]["id"]=="A"
        assert r["routes"][0]["task_kind"]=="web-design"
        assert Path(r["context_packets"][0]["packet_path"]).is_file()
    print("PASS: precompute self-test")

def main():
    ap=argparse.ArgumentParser(description="Precompute Gearbox deterministic orchestration artifacts before human plan approval without spending model/worker budget.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--input")
    ap.add_argument("--output")
    ap.add_argument("--artifact-dir",type=Path)
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.input:ap.error("--input is required")
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    result=precompute(data,args.artifact_dir)
    text=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="");return 0

if __name__=="__main__":
    raise SystemExit(main())
