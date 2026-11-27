#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"
THREE_D_CAPABILITIES=("blender","godot")
MOTION_CAPABILITIES=("blender","godot","aseprite")

def _routes()->dict:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    return data["routing_defaults"]["game_asset"]

@dataclass
class Route:
    task_kind:str
    forced:bool
    engine:str
    model:str
    effort:str
    mode:str
    required_capabilities:list[str]
    preferred_capabilities:list[str]
    blocked:bool
    blocker:str|None
    review_engine:str|None
    review_model:str|None
    delegate_engine:str|None
    delegate_model:str|None
    delegate_effort:str|None
    delegate_required_capabilities:list[str]
    delegation_available:bool
    delegation_required:bool
    delegation_policy:str|None
    rationale:str

def _available(values:list[str])->dict[str,str]:
    return {str(value).casefold():str(value) for value in values if str(value).strip()}

def _pick(available:dict[str,str],names:tuple[str,...])->str|None:
    for name in names:
        if name in available:
            return available[name]
    return None

def route(task_kind:str,claude_capabilities:list[str],gemini_capabilities:list[str],three_d:bool=False)->Route:
    routes=_routes()
    if task_kind not in routes:
        raise SystemExit(f"unknown game-asset task kind: {task_kind}")
    base=routes[task_kind]
    claude=_available(claude_capabilities); gemini=_available(gemini_capabilities)
    required=[]; delegate_required=[]; preferred=[]; blocked=False; blocker=None
    mode="direct-model"; delegation_available=False; delegation_required=False; delegation_policy=None

    if task_kind=="pixel-art":
        preferred=["aseprite"]
        if "aseprite" in gemini:
            required=[gemini["aseprite"]]; mode="aseprite-mcp"
        else:
            mode="direct-sol-generation"
    elif task_kind=="model-3d":
        preferred=list(THREE_D_CAPABILITIES)
        gemini_tool=_pick(gemini,THREE_D_CAPABILITIES)
        delegation_policy="Gemini Carbon/high produces substantive 3D assets with Blender/Godot. A fresh independent Gemini session reviews the exported artifact."
        delegation_available=gemini_tool is not None
        delegation_required=False
        if gemini_tool:
            required=[gemini_tool]
            mode="gemini-carbon-3d-execution"
        else:
            blocked=True; blocker="3D production requires Blender or Godot available to Gemini Carbon; Claude-only tools cannot satisfy the forced execution route"; mode="capability-blocked"
    elif task_kind=="motion-design":
        preferred=list(MOTION_CAPABILITIES)
        claude_tool=_pick(claude,MOTION_CAPABILITIES); gemini_tool=_pick(gemini,MOTION_CAPABILITIES)
        delegation_available=gemini_tool is not None
        if three_d:
            preferred=list(THREE_D_CAPABILITIES)
            gemini_tool=_pick(gemini,THREE_D_CAPABILITIES)
            delegation_policy="3D motion production uses Gemini GPT-6.2 Carbon/high and an independent Carbon review; Opus directs."
            delegation_required=True
            delegation_available=gemini_tool is not None
            if gemini_tool:
                delegate_required=[gemini_tool]; mode="opus-directed-astra-3d-motion"
            else:
                blocked=True; blocker="3D motion requires Blender or Godot available to Gemini Carbon"; mode="capability-blocked"
        else:
            delegation_policy="Opus 5.5 directs non-3D motion; Gemini GPT-6.2 Neon may execute bounded animation/tool operations."
            if claude_tool:
                required=[claude_tool]; mode="opus-motion-direct-with-gemini-delegation" if gemini_tool else "opus-motion-direct"
                if gemini_tool: delegate_required=[gemini_tool]
            elif gemini_tool:
                mode="opus-directed-gemini-motion-execution"; delegation_required=True; delegate_required=[gemini_tool]
            else:
                blocked=True; blocker="motion execution requires Blender, Godot or Aseprite on Claude or Gemini"; mode="capability-blocked"
    elif task_kind=="review-3d":
        preferred=list(THREE_D_CAPABILITIES)
        gemini_tool=_pick(gemini,THREE_D_CAPABILITIES)
        if gemini_tool:
            required=[gemini_tool]; mode=f"{gemini_tool.casefold()}-review"
        else:
            blocked=True; blocker="3D Carbon review requires Blender or Godot available to Gemini"; mode="capability-blocked"
    elif task_kind=="video-create":
        preferred=["fal-video"]
        tool=_pick(claude,("fal-video",)) or _pick(gemini,("fal-video",))
        if tool:
            required=[tool]; mode="image-first-fal-model-selection"
        else:
            blocked=True; blocker="Video requires FAL_KEY and fal-client on an available execution worker"; mode="capability-blocked"
    elif task_kind=="asset-image":
        mode="direct-sol-generation"

    rationale={
        "video-create":"Opus video producer chooses the cheapest capable fal image-to-video model after image dependency and spend approval",
        "asset-image":"game image generation is pinned to Gemini GPT-6.2 Neon",
        "pixel-art":"pixel art is pinned to Gemini GPT-6.2 Neon; Aseprite MCP is preferred when available",
        "model-3d":"Gemini Carbon/high owns substantive 3D production; fresh independent Gemini Carbon review is mandatory",
        "motion-design":"Opus 5.5 directs motion; Gemini Carbon/high executes 3D motion, while non-3D motion may use Neon",
        "review-3d":"3D asset review is pinned to Gemini GPT-6.2 Carbon with a live 3D inspection capability",
    }[task_kind]

    return Route(
        task_kind=task_kind,forced=True,engine=base["engine"],model=base["model"],effort=base["effort"],mode=mode,
        required_capabilities=required,preferred_capabilities=preferred,blocked=blocked,blocker=blocker,
        review_engine=base.get("review_engine"),review_model=base.get("review_model"),
        delegate_engine=base.get("delegate_engine"),delegate_model=("gemini-4-carbon-high" if task_kind=="motion-design" and three_d else base.get("delegate_model")),delegate_effort=base.get("delegate_effort"),
        delegate_required_capabilities=delegate_required,delegation_available=delegation_available,
        delegation_required=delegation_required,delegation_policy=delegation_policy,rationale=rationale,
    )

def self_test()->None:
    image=route("asset-image",[],[])
    assert image.engine=="gemini" and image.model=="gemini-4-neon-medium" and not image.blocked
    pixel=route("pixel-art",[],["aseprite","godot"])
    assert pixel.required_capabilities==["aseprite"] and pixel.mode=="aseprite-mcp"
    direct=route("model-3d",["blender"],["blender"])
    assert direct.model=="gemini-4-carbon-high" and direct.delegate_model is None and direct.review_model=="gemini-4-carbon-high"
    delegated=route("model-3d",[],["blender"])
    assert delegated.mode=="gemini-carbon-3d-execution" and not delegated.delegation_required and delegated.required_capabilities==["blender"]
    assert route("model-3d",[],[]).blocked
    assert route("model-3d",["blender"],[]).blocked
    motion=route("motion-design",["godot"],["blender"])
    assert motion.delegate_model=="gemini-4-neon-high" and motion.delegation_available
    motion3d=route("motion-design",["godot"],["blender"],three_d=True)
    assert motion3d.delegate_model=="gemini-4-carbon-high" and motion3d.delegation_required and motion3d.delegate_required_capabilities==["blender"]
    assert route("motion-design",["godot"],[],three_d=True).blocked
    review=route("review-3d",["blender"],["godot"])
    assert review.model=="gemini-4-carbon-high" and review.required_capabilities==["godot"]
    print("PASS: game-asset-router self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Deterministic specialist routing for Gearbox game assets and motion.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--three-d",action="store_true",help="Force Carbon/Gemini 3D motion execution; only applies to motion-design")
    ap.add_argument("--task-kind",choices=sorted(_routes()))
    ap.add_argument("--available-capability",action="append",default=[])
    ap.add_argument("--claude-capability",action="append",default=[])
    ap.add_argument("--gemini-capability",action="append",default=[])
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.task_kind: ap.error("--task-kind is required")
    if args.three_d and args.task_kind!="motion-design": ap.error("--three-d is only valid for motion-design")
    shared=args.available_capability
    result=route(args.task_kind,[*shared,*args.claude_capability],[*shared,*args.gemini_capability],three_d=args.three_d)
    if args.json: print(json.dumps(asdict(result),indent=2,ensure_ascii=False))
    else: print(f"{result.task_kind}: {result.engine}/{result.model} effort={result.effort} mode={result.mode}")
    return 7 if result.blocked else 0

if __name__=="__main__":
    raise SystemExit(main())
