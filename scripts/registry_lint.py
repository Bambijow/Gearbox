#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"
ROUTERS={"game_asset","web_design","product_quality"}
ARTIFACTS={"screenshot","accessibility","console","network","performance","interaction","playback","dom","other"}
PROFILES={"dev","standard","release","critical"}

def validate(data:dict)->list[str]:
    errors=[]
    routes=data.get("task_routes",{})
    surfaces=data.get("task_surfaces",{})
    if not routes:errors.append("task_routes missing")
    for task,entry in routes.items():
        if entry.get("router") not in ROUTERS:errors.append(f"{task}: invalid router {entry.get('router')}")
        if task not in surfaces:errors.append(f"{task}: task_surfaces missing")
    extra=sorted(set(surfaces)-set(routes))
    if extra:errors.append(f"task_surfaces without task_routes: {extra}")
    profiles=set(data.get("quality_profiles",{}))
    if profiles!=PROFILES:errors.append(f"quality profiles must be {sorted(PROFILES)}, got {sorted(profiles)}")
    gates=data.get("gates",{})
    if not gates:errors.append("gates missing")
    for name,gate in gates.items():
        if "probe_needs" not in gate:errors.append(f"{name}: probe_needs missing")
        invalid=sorted(set(gate.get("probe_needs",[]))-ARTIFACTS)
        if invalid:errors.append(f"{name}: invalid probe artifacts {invalid}")
        skill=gate.get("skill")
        if skill and skill not in routes:errors.append(f"{name}: skill {skill} not registered")
    sched=data.get("scheduler",{})
    if not isinstance(sched.get("max_batch_members"),int) or sched.get("max_batch_members",0)<1:
        errors.append("scheduler.max_batch_members must be positive integer")
    adaptive=data.get("adaptive_routing",{})
    if adaptive.get("mode") not in {"advisory","off"}:errors.append("adaptive_routing.mode invalid")

    fusion=data.get("review_fusion",{})
    if not isinstance(fusion.get("enabled"),bool):errors.append("review_fusion.enabled must be boolean")
    if fusion.get("max_risk") not in {"low","medium","high","critical"}:errors.append("review_fusion.max_risk invalid")
    for pack in fusion.get("packs",[]):
        unknown=sorted(set(pack.get("gates",[]))-set(gates))
        if unknown:errors.append(f"review_fusion {pack.get('id')}: unknown gates {unknown}")
        if int(pack.get("min_members",0))<2:errors.append(f"review_fusion {pack.get('id')}: min_members must be >=2")
        if int(pack.get("max_members",0))<int(pack.get("min_members",0)):errors.append(f"review_fusion {pack.get('id')}: max_members < min_members")

    depth=data.get("quality_depth",{})
    if depth.get("mode") not in {"escalate-only","off"}:errors.append("quality_depth.mode invalid")
    if depth.get("mode")=="escalate-only" and depth.get("never_remove_required_gates") is not True:
        errors.append("quality_depth escalate-only must preserve required gates")

    packing=data.get("readonly_packing",{})
    if packing.get("enabled") and packing.get("forbid_independent_judgment") is not True:
        errors.append("readonly_packing must forbid independent judgment")
    if not isinstance(packing.get("max_members"),int) or packing.get("max_members",0)<2:
        errors.append("readonly_packing.max_members must be >=2")

    impact=data.get("test_impact",{})
    if impact.get("mode") not in {"rank-only","off"}:errors.append("test_impact.mode invalid")
    if impact.get("mode")=="rank-only" and impact.get("never_drop_required_checks") is not True:
        errors.append("test_impact rank-only must preserve required checks")

    facts=data.get("repo_facts_cache",{})
    if facts.get("enabled") and facts.get("cache_scope")!="user-xdg-per-repo":
        errors.append("repo_facts_cache enabled cache_scope must be user-xdg-per-repo")
    return errors

def self_test():
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors=validate(data)
    assert not errors,errors
    bad=json.loads(json.dumps(data));del bad["task_surfaces"]["web-design"]
    assert any("web-design" in e for e in validate(bad))
    bad2=json.loads(json.dumps(data));bad2["quality_depth"]["never_remove_required_gates"]=False
    assert any("preserve required gates" in e for e in validate(bad2))
    print("PASS: orchestration-registry lint")

def main():
    ap=argparse.ArgumentParser(description="Validate Gearbox orchestration-registry consistency.")
    ap.add_argument("--self-test",action="store_true");ap.add_argument("--file",type=Path,default=REGISTRY)
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    data=json.loads(args.file.read_text(encoding="utf-8"));errors=validate(data)
    print(json.dumps({"valid":not errors,"errors":errors},indent=2))
    return 0 if not errors else 6

if __name__=="__main__":
    raise SystemExit(main())
