#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from change_surface import classify

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"

TASK_SURFACES={
    "web-design":{"user_ui"},
    "creative-web":{"user_ui","interactive_ui","creative_runtime","performance_sensitive"},
    "design-system":{"shared_design_system"},
    "a11y-audit":{"user_ui"},
    "visual-regression":{"user_ui"},
    "content-design":{"ux_copy"},
    "experience-perf":{"performance_sensitive"},
    "art-direction":{"art_direction"},
    "audio-design":{"audio"},
    "level-design":{"level"},
    "asset-image":{"visual_asset"},
    "pixel-art":{"visual_asset"},
    "model-3d":{"asset_3d"},
    "motion-design":{"visual_asset"},
}

def load_registry()->dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def compile_plan(task_kind:str|None,profile:str,surfaces:list[str],paths:list[str],hints:list[str],flags:dict[str,bool])->dict:
    registry=load_registry()
    if profile not in registry["quality_profiles"]:
        raise SystemExit(f"unknown quality profile: {profile}")
    detected=classify(paths,hints)
    surface_set=set(surfaces)|set(detected["surfaces"])
    if task_kind:
        surface_set.update(TASK_SURFACES.get(task_kind,set()))

    gates=[]; required_groups:dict[str,list[str]]={}
    for name,rule in registry["gates"].items():
        reasons=[]; triggered=False; explicit=False
        trigger_surfaces=set(rule.get("trigger_surfaces",[]))
        matched=sorted(surface_set & trigger_surfaces)
        if matched:
            triggered=True; reasons.append("surface:"+",".join(matched))
        if task_kind in rule.get("trigger_task_kinds",[]):
            triggered=True; explicit=True; reasons.append("task_kind:"+str(task_kind))
        if task_kind and rule.get("skill")==task_kind:
            triggered=True; explicit=True; reasons.append("explicit_skill:"+task_kind)
        required_flag=rule.get("requires_flag")
        if required_flag and not flags.get(required_flag,False) and not explicit:
            triggered=False; reasons=[f"requires_flag:{required_flag}=false"]
        elif required_flag and flags.get(required_flag,False) and trigger_surfaces.intersection(surface_set):
            reasons.append(f"flag:{required_flag}=true")

        status="REQUIRED" if triggered else "NOT_APPLICABLE"
        item={"gate":name,"status":status,"skill":rule.get("skill"),"probe_group":rule.get("probe_group"),"reason":"; ".join(reasons) if reasons else "no trigger"}
        gates.append(item)
        if triggered and item["probe_group"]:
            required_groups.setdefault(item["probe_group"],[]).append(name)

    profile_cfg=registry["quality_profiles"][profile]
    probe_groups=[
        {"group":group,"gates":sorted(names),"depth":profile_cfg["probe_depth"],"state_matrix":profile_cfg["state_matrix"]}
        for group,names in sorted(required_groups.items())
    ]
    payload={
        "schema_version":1,"task_kind":task_kind,"quality_profile":profile,"profile":profile_cfg,
        "surfaces":sorted(surface_set),"path_classification":detected["paths"],
        "flags":{k:bool(v) for k,v in sorted(flags.items())},"gates":gates,"probe_groups":probe_groups,
    }
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    payload["quality_plan_id"]=hashlib.sha256(canonical).hexdigest()
    return payload

def self_test()->None:
    p=compile_plan("web-design","standard",[],["src/components/ui/Dialog.tsx"],[],{"baseline_exists":True})
    required={g["gate"] for g in p["gates"] if g["status"]=="REQUIRED"}
    assert {"SLOP_GATE","INTERACTION_GATE","A11Y_GATE","VISUAL_REGRESSION_GATE"}.issubset(required)
    exp=[x for x in p["probe_groups"] if x["group"]=="experience"][0]
    assert {"A11Y_GATE","INTERACTION_GATE","SLOP_GATE","VISUAL_REGRESSION_GATE"}.issubset(set(exp["gates"]))

    p=compile_plan("creative-web","release",[],[],[],{"baseline_exists":False})
    required={g["gate"] for g in p["gates"] if g["status"]=="REQUIRED"}
    assert {"SLOP_GATE","INTERACTION_GATE","A11Y_GATE","PERF_GATE","CREATIVE_GATE"}.issubset(required)
    assert "VISUAL_REGRESSION_GATE" not in required

    p=compile_plan("audio-design","standard",[],[],[],{"baseline_exists":False})
    required={g["gate"] for g in p["gates"] if g["status"]=="REQUIRED"}
    assert "AUDIO_GATE" in required and "A11Y_GATE" not in required

    p=compile_plan("visual-regression","standard",[],[],[],{"baseline_exists":False})
    required={g["gate"] for g in p["gates"] if g["status"]=="REQUIRED"}
    assert "VISUAL_REGRESSION_GATE" in required
    print("PASS: quality-plan self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Compile a deterministic Gearbox quality/gate plan from consequence surfaces.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--task-kind")
    ap.add_argument("--profile",default="standard",choices=("dev","standard","release","critical"))
    ap.add_argument("--surface",action="append",default=[])
    ap.add_argument("--path",action="append",default=[])
    ap.add_argument("--hint",action="append",default=[])
    ap.add_argument("--baseline-exists",action="store_true")
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    payload=compile_plan(args.task_kind,args.profile,args.surface,args.path,args.hint,{"baseline_exists":args.baseline_exists})
    text=json.dumps(payload,indent=2,ensure_ascii=False)+"\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
