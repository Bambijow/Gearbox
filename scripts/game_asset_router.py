#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

ROUTES = {
    "asset-image": {
        "engine": "codex",
        "model": "gpt-6.1-sol",
        "effort": "medium",
        "review_engine": None,
        "review_model": None,
        "delegate_engine": None,
        "delegate_model": None,
        "delegate_effort": None,
    },
    "pixel-art": {
        "engine": "codex",
        "model": "gpt-6.1-sol",
        "effort": "medium",
        "review_engine": None,
        "review_model": None,
        "delegate_engine": None,
        "delegate_model": None,
        "delegate_effort": None,
    },
    "model-3d": {
        "engine": "claude",
        "model": "claude-opus-5-5",
        "effort": "high",
        "review_engine": "codex",
        "review_model": "gpt-6-astra",
        "delegate_engine": "codex",
        "delegate_model": "gpt-6.1-sol",
        "delegate_effort": "high",
    },
    "motion-design": {
        "engine": "claude",
        "model": "claude-opus-5-5",
        "effort": "high",
        "review_engine": None,
        "review_model": None,
        "delegate_engine": "codex",
        "delegate_model": "gpt-6.1-sol",
        "delegate_effort": "high",
    },
    "review-3d": {
        "engine": "codex",
        "model": "gpt-6-astra",
        "effort": "high",
        "review_engine": None,
        "review_model": None,
        "delegate_engine": None,
        "delegate_model": None,
        "delegate_effort": None,
    },
}

THREE_D_CAPABILITIES = ("blender", "godot")
MOTION_CAPABILITIES = ("blender", "godot", "aseprite")


@dataclass
class Route:
    task_kind: str
    forced: bool
    engine: str
    model: str
    effort: str
    mode: str
    required_capabilities: list[str]
    preferred_capabilities: list[str]
    blocked: bool
    blocker: str | None
    review_engine: str | None
    review_model: str | None
    delegate_engine: str | None
    delegate_model: str | None
    delegate_effort: str | None
    delegate_required_capabilities: list[str]
    delegation_available: bool
    delegation_required: bool
    delegation_policy: str | None
    rationale: str


def _available(values: list[str]) -> dict[str, str]:
    return {str(value).casefold(): str(value) for value in values if str(value).strip()}


def _pick(available: dict[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in available:
            return available[name]
    return None


def route(
    task_kind: str,
    claude_capabilities: list[str],
    codex_capabilities: list[str],
) -> Route:
    base = ROUTES[task_kind]
    claude = _available(claude_capabilities)
    codex = _available(codex_capabilities)
    required: list[str] = []
    delegate_required: list[str] = []
    preferred: list[str] = []
    blocked = False
    blocker = None
    mode = "direct-model"
    delegation_available = False
    delegation_required = False
    delegation_policy = None

    if task_kind == "pixel-art":
        preferred = ["aseprite"]
        if "aseprite" in codex:
            required = [codex["aseprite"]]
            mode = "aseprite-mcp"
        else:
            mode = "direct-sol-generation"

    elif task_kind == "model-3d":
        preferred = list(THREE_D_CAPABILITIES)
        claude_tool = _pick(claude, THREE_D_CAPABILITIES)
        codex_tool = _pick(codex, THREE_D_CAPABILITIES)
        delegation_available = codex_tool is not None
        delegation_policy = (
            "Opus 5.5 owns art direction, topology/rig decisions and acceptance; "
            "Codex GPT-6.1 Sol may execute bounded Blender/Godot operations or the concrete tool pass."
        )
        if claude_tool:
            required = [claude_tool]
            mode = "opus-direct-with-codex-delegation" if codex_tool else "opus-direct"
            if codex_tool:
                delegate_required = [codex_tool]
        elif codex_tool:
            mode = "opus-directed-codex-execution"
            delegation_required = True
            delegate_required = [codex_tool]
        else:
            blocked = True
            blocker = "3D creation requires Blender or Godot on Claude or Codex"
            mode = "capability-blocked"

    elif task_kind == "motion-design":
        preferred = list(MOTION_CAPABILITIES)
        claude_tool = _pick(claude, MOTION_CAPABILITIES)
        codex_tool = _pick(codex, MOTION_CAPABILITIES)
        delegation_available = codex_tool is not None
        delegation_policy = (
            "Opus 5.5 owns motion language, timing, hierarchy and acceptance; "
            "Codex GPT-6.1 Sol may execute bounded animation/tool operations."
        )
        if claude_tool:
            required = [claude_tool]
            mode = "opus-motion-direct-with-codex-delegation" if codex_tool else "opus-motion-direct"
            if codex_tool:
                delegate_required = [codex_tool]
        elif codex_tool:
            mode = "opus-directed-codex-motion-execution"
            delegation_required = True
            delegate_required = [codex_tool]
        else:
            blocked = True
            blocker = "motion execution requires Blender, Godot or Aseprite on Claude or Codex"
            mode = "capability-blocked"

    elif task_kind == "review-3d":
        preferred = list(THREE_D_CAPABILITIES)
        codex_tool = _pick(codex, THREE_D_CAPABILITIES)
        if codex_tool:
            required = [codex_tool]
            mode = f"{codex_tool.casefold()}-review"
        else:
            blocked = True
            blocker = "3D Astra review requires Blender or Godot available to Codex"
            mode = "capability-blocked"

    elif task_kind == "asset-image":
        mode = "direct-sol-generation"

    rationale = {
        "asset-image": "game image generation is pinned to Codex GPT-6.1 Sol",
        "pixel-art": "pixel art is pinned to Codex GPT-6.1 Sol; Aseprite MCP is preferred when available",
        "model-3d": "Opus 5.5 directs 3D creation; Codex Sol may execute tool-bounded modeling; Astra remains mandatory review",
        "motion-design": "Opus 5.5 directs motion language and timing; Codex Sol may execute tool-bounded animation",
        "review-3d": "3D asset review is pinned to Codex GPT-6 Astra with a live 3D inspection capability",
    }[task_kind]

    return Route(
        task_kind=task_kind,
        forced=True,
        engine=base["engine"],
        model=base["model"],
        effort=base["effort"],
        mode=mode,
        required_capabilities=required,
        preferred_capabilities=preferred,
        blocked=blocked,
        blocker=blocker,
        review_engine=base["review_engine"],
        review_model=base["review_model"],
        delegate_engine=base["delegate_engine"],
        delegate_model=base["delegate_model"],
        delegate_effort=base["delegate_effort"],
        delegate_required_capabilities=delegate_required,
        delegation_available=delegation_available,
        delegation_required=delegation_required,
        delegation_policy=delegation_policy,
        rationale=rationale,
    )


def self_test() -> None:
    image = route("asset-image", [], [])
    assert image.engine == "codex" and image.model == "gpt-6.1-sol" and not image.blocked

    pixel = route("pixel-art", [], ["aseprite", "godot"])
    assert pixel.required_capabilities == ["aseprite"] and pixel.mode == "aseprite-mcp"

    pixel_fallback = route("pixel-art", [], [])
    assert pixel_fallback.mode == "direct-sol-generation"

    direct = route("model-3d", ["blender"], ["blender"])
    assert direct.model == "claude-opus-5-5"
    assert direct.delegate_model == "gpt-6.1-sol"
    assert direct.delegation_available is True
    assert direct.review_model == "gpt-6-astra"

    delegated = route("model-3d", [], ["blender"])
    assert delegated.mode == "opus-directed-codex-execution"
    assert delegated.delegation_required is True
    assert delegated.delegate_required_capabilities == ["blender"]

    blocked_model = route("model-3d", [], [])
    assert blocked_model.blocked is True

    motion = route("motion-design", ["godot"], ["blender"])
    assert motion.model == "claude-opus-5-5"
    assert motion.delegate_model == "gpt-6.1-sol"
    assert motion.delegation_available is True

    review = route("review-3d", ["blender"], ["godot"])
    assert review.engine == "codex" and review.model == "gpt-6-astra"
    assert review.required_capabilities == ["godot"]
    print("PASS: game-asset-router self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic specialist routing for Gearbox game assets and motion.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--task-kind", choices=sorted(ROUTES))
    ap.add_argument("--available-capability", action="append", default=[], help="Compatibility shortcut: capability visible to both providers.")
    ap.add_argument("--claude-capability", action="append", default=[])
    ap.add_argument("--codex-capability", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.task_kind:
        ap.error("--task-kind is required")

    shared = args.available_capability
    result = route(
        args.task_kind,
        [*shared, *args.claude_capability],
        [*shared, *args.codex_capability],
    )
    payload = asdict(result)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"{result.task_kind}: {result.engine}/{result.model} "
            f"effort={result.effort} mode={result.mode}"
        )
    return 7 if result.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
