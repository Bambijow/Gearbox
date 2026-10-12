#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"
AUTO_COMP={"refine":False,"surface":True,"redesign":True}

def _defaults()->dict:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    return data["routing_defaults"]["web_design"]

@dataclass
class Route:
    task_kind:str
    scope:str
    creative:bool
    director_engine:str
    director_model:str
    director_effort:str
    director_agent:str
    comp_generator_engine:str
    comp_generator_model:str
    comp_generator_effort:str
    comp_policy:str
    comp_enabled:bool
    comp_required:bool
    image_generation_available:bool
    image_generation_model:str
    image_edit_model:str
    comp_outputs:list[dict]
    blocked:bool
    blocker:str|None
    builder_engine:str
    builder_model:str
    builder_effort:str
    reviewer_engine:str
    reviewer_model:str
    reviewer_effort:str
    reviewer_agent:str
    interaction_gate_required:bool
    creative_gate_required:bool
    preferred_director_capabilities:list[str]
    preferred_builder_capabilities:list[str]
    preferred_reviewer_capabilities:list[str]
    inspo_available:bool
    visual_evidence_available:bool
    rationale:str

def _keys(values:list[str])->set[str]:
    return {str(v).strip().casefold() for v in values if str(v).strip()}

def route(
    scope:str,
    claude_capabilities:list[str],
    codex_capabilities:list[str],
    *,
    comp_policy:str="auto",
    image_generation_available:bool=False,
    image_generation_model:str="gpt-image-2.5-flare",
    image_edit_model:str="gpt-image-2.5-sunburst",
    creative:bool=False,
)->Route:
    if scope not in AUTO_COMP:
        raise SystemExit(f"unknown web-design scope: {scope}")
    defaults=_defaults()
    director=defaults["director"]; comp=defaults["comp_generator"]; builder=defaults["builder"]
    review_key="creative" if creative else scope
    reviewer=defaults["reviewer"][review_key]
    claude=_keys(claude_capabilities); codex=_keys(codex_capabilities)
    browser_names={"browser","playwright","chrome","chromium"}
    visual_evidence=bool((claude|codex)&browser_names)

    comp_required=comp_policy=="require"
    auto_comp=True if creative else AUTO_COMP[scope]
    if comp_policy=="skip":
        comp_enabled=False
    elif comp_required:
        comp_enabled=image_generation_available
    else:
        comp_enabled=bool(auto_comp and image_generation_available)

    blocked=bool(comp_required and not image_generation_available)
    blocker="WEB_COMP_BLOCKED: required image-generation path unavailable" if blocked else None
    effort_key="creative" if creative else scope

    return Route(
        task_kind="creative-web" if creative else "web-design",
        scope=scope,creative=creative,
        director_engine=director["engine"],director_model=director["model"],director_effort=director["effort"],
        director_agent="creative-web-director" if creative else "web-design-director",
        comp_generator_engine=comp["engine"],comp_generator_model=comp["model"],comp_generator_effort=comp["effort_by_scope"][effort_key],
        comp_policy=comp_policy,comp_enabled=comp_enabled,comp_required=comp_required,
        image_generation_available=image_generation_available,image_generation_model=image_generation_model,image_edit_model=image_edit_model,
        comp_outputs=[{"kind":"desktop","size":"1536x1024"},{"kind":"mobile","size":"1024x1536"}],
        blocked=blocked,blocker=blocker,
        builder_engine=builder["engine"],builder_model=builder["model"],builder_effort=builder["effort_by_scope"][effort_key],
        reviewer_engine=reviewer["engine"],reviewer_model=reviewer["model"],reviewer_effort=reviewer["effort"],reviewer_agent=reviewer["agent"],
        interaction_gate_required=True,creative_gate_required=creative,
        preferred_director_capabilities=["inspo"],preferred_builder_capabilities=["browser"],preferred_reviewer_capabilities=["browser"],
        inspo_available="inspo" in claude,visual_evidence_available=visual_evidence,
        rationale="Opus owns visual/interaction direction; optional Codex comp generation visualizes the approved system; Codex builds; fresh Claude judges rendered evidence. Static model identities come from orchestration-registry.json.",
    )

def self_test()->None:
    refine=route("refine",["inspo"],["browser"],image_generation_available=True)
    assert refine.director_model=="claude-opus-5-5" and refine.builder_model=="gpt-6.1-sol"
    assert refine.reviewer_model=="sonnet" and not refine.comp_enabled
    surface=route("surface",[],["browser"],image_generation_available=True)
    assert surface.comp_enabled and surface.comp_generator_model=="gpt-6.1-sol"
    creative=route("surface",["inspo"],["browser"],creative=True,image_generation_available=True)
    assert creative.task_kind=="creative-web" and creative.builder_effort=="high"
    assert creative.reviewer_model=="claude-opus-5-5" and creative.creative_gate_required
    required=route("surface",[],[],comp_policy="require",image_generation_available=False)
    assert required.blocked and required.blocker and "WEB_COMP_BLOCKED" in required.blocker
    print("PASS: web-design-router self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Deterministic routing for Gearbox web-design lanes.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--scope",choices=sorted(AUTO_COMP),default="surface")
    ap.add_argument("--creative",action="store_true")
    ap.add_argument("--claude-capability",action="append",default=[])
    ap.add_argument("--codex-capability",action="append",default=[])
    ap.add_argument("--comp",choices=("auto","require","skip"),default="auto")
    ap.add_argument("--image-generation-available",action="store_true")
    ap.add_argument("--image-model",default="gpt-image-2.5-flare")
    ap.add_argument("--image-edit-model",default="gpt-image-2.5-sunburst")
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    result=route(
        args.scope,args.claude_capability,args.codex_capability,
        comp_policy=args.comp,image_generation_available=args.image_generation_available,
        image_generation_model=args.image_model,image_edit_model=args.image_edit_model,creative=args.creative,
    )
    if args.json: print(json.dumps(asdict(result),indent=2,ensure_ascii=False))
    else: print(f"{result.task_kind}/{result.scope}: director={result.director_model} comp={'on' if result.comp_enabled else 'off'} builder={result.builder_model} reviewer={result.reviewer_model}")
    return 7 if result.blocked else 0

if __name__=="__main__":
    raise SystemExit(main())
