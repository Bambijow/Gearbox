#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

import game_asset_router
import product_quality_router
import web_design_router

ROOT=Path(__file__).resolve().parents[1]
REGISTRY_PATH=ROOT/"orchestration-registry.json"

def load_registry()->dict:
    data=json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version")!=1:
        raise SystemExit("unsupported orchestration registry schema")
    return data

def route_task(
    task_kind:str,
    claude_capabilities:list[str],
    codex_capabilities:list[str],
    *,
    scope:str="surface",
    comp_policy:str="auto",
    image_generation_available:bool=False,
    image_model:str="gpt-image-2.5-flare",
    image_edit_model:str="gpt-image-2.5-sunburst",
):
    registry=load_registry()
    entry=registry.get("task_routes",{}).get(task_kind)
    if not entry:
        raise SystemExit(f"no specialist route registered for task kind: {task_kind}")
    router=entry["router"]
    if router=="game_asset":
        result=game_asset_router.route(task_kind,claude_capabilities,codex_capabilities)
    elif router=="web_design":
        result=web_design_router.route(
            scope,
            claude_capabilities,
            codex_capabilities,
            comp_policy=comp_policy,
            image_generation_available=image_generation_available,
            image_generation_model=image_model,
            image_edit_model=image_edit_model,
            creative=bool(entry.get("creative",False)),
        )
    elif router=="product_quality":
        result=product_quality_router.route(task_kind)
    else:
        raise SystemExit(f"unknown router backend: {router}")
    payload=asdict(result) if is_dataclass(result) else dict(result)
    return {
        "schema_version":1,
        "task_kind":task_kind,
        "router_backend":router,
        "route":payload,
    }

def self_test()->None:
    r=route_task("model-3d",["blender"],["blender"])
    assert r["router_backend"]=="game_asset" and r["route"]["model"]=="claude-opus-5-5"
    r=route_task("creative-web",["inspo"],["browser"],image_generation_available=True)
    assert r["router_backend"]=="web_design" and r["route"]["creative"] is True
    r=route_task("a11y-audit",[],[])
    assert r["router_backend"]=="product_quality" and r["route"]["owner_model"]=="sonnet"
    print("PASS: unified route-task self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Unified specialist routing facade for Gearbox.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--task-kind")
    ap.add_argument("--scope",choices=("refine","surface","redesign"),default="surface")
    ap.add_argument("--claude-capability",action="append",default=[])
    ap.add_argument("--codex-capability",action="append",default=[])
    ap.add_argument("--comp",choices=("auto","require","skip"),default="auto")
    ap.add_argument("--image-generation-available",action="store_true")
    ap.add_argument("--image-model",default="gpt-image-2.5-flare")
    ap.add_argument("--image-edit-model",default="gpt-image-2.5-sunburst")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.task_kind:
        ap.error("--task-kind is required")
    payload=route_task(
        args.task_kind,args.claude_capability,args.codex_capability,
        scope=args.scope,
        comp_policy=args.comp,
        image_generation_available=args.image_generation_available,
        image_model=args.image_model,
        image_edit_model=args.image_edit_model,
    )
    print(json.dumps(payload,indent=2,ensure_ascii=False))
    blocked=bool(payload["route"].get("blocked",False))
    return 7 if blocked else 0

if __name__=="__main__":
    raise SystemExit(main())
