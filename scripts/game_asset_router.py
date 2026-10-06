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
    },
    "pixel-art": {
        "engine": "codex",
        "model": "gpt-6.1-sol",
        "effort": "medium",
        "review_engine": None,
        "review_model": None,
    },
    "model-3d": {
        "engine": "claude",
        "model": "claude-opus-5-5",
        "effort": "high",
        "review_engine": "codex",
        "review_model": "gpt-6-astra",
    },
    "review-3d": {
        "engine": "codex",
        "model": "gpt-6-astra",
        "effort": "high",
        "review_engine": None,
        "review_model": None,
    },
}


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
    rationale: str


def _available(values: list[str]) -> dict[str, str]:
    return {str(value).casefold(): str(value) for value in values if str(value).strip()}


def route(task_kind: str, available_capabilities: list[str]) -> Route:
    base = ROUTES[task_kind]
    available = _available(available_capabilities)
    required: list[str] = []
    preferred: list[str] = []
    blocked = False
    blocker = None
    mode = "direct-model"

    if task_kind == "pixel-art":
        preferred = ["aseprite"]
        if "aseprite" in available:
            required = [available["aseprite"]]
            mode = "aseprite-mcp"
        else:
            mode = "direct-sol-generation"

    elif task_kind == "model-3d":
        preferred = ["blender", "godot"]
        if "blender" in available:
            required = [available["blender"]]
            mode = "blender-mcp"
        elif "godot" in available:
            required = [available["godot"]]
            mode = "godot-mcp"
        else:
            blocked = True
            blocker = "3D creation requires an available Blender or Godot capability"
            mode = "capability-blocked"

    elif task_kind == "review-3d":
        preferred = ["blender", "godot"]
        if "blender" in available:
            required = [available["blender"]]
            mode = "blender-review"
        elif "godot" in available:
            required = [available["godot"]]
            mode = "godot-review"
        else:
            blocked = True
            blocker = "3D review requires an available Blender or Godot capability"
            mode = "capability-blocked"

    elif task_kind == "asset-image":
        mode = "direct-sol-generation"

    rationale = {
        "asset-image": "game image generation is pinned to Codex GPT-6.1 Sol",
        "pixel-art": "pixel art is pinned to Codex GPT-6.1 Sol; Aseprite MCP is preferred when available",
        "model-3d": "3D creation is pinned to Claude Opus 5.5 and requires a 3D-capable tool surface",
        "review-3d": "3D asset review is pinned to Codex GPT-6 Astra and requires a 3D-capable tool surface",
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
        rationale=rationale,
    )


def self_test() -> None:
    image = route("asset-image", [])
    assert image.engine == "codex" and image.model == "gpt-6.1-sol" and not image.blocked

    pixel = route("pixel-art", ["aseprite", "godot"])
    assert pixel.model == "gpt-6.1-sol"
    assert pixel.required_capabilities == ["aseprite"]
    assert pixel.mode == "aseprite-mcp"

    pixel_fallback = route("pixel-art", [])
    assert pixel_fallback.mode == "direct-sol-generation"
    assert pixel_fallback.required_capabilities == []

    model = route("model-3d", ["blender"])
    assert model.engine == "claude"
    assert model.model == "claude-opus-5-5"
    assert model.review_model == "gpt-6-astra"
    assert model.required_capabilities == ["blender"]

    blocked_model = route("model-3d", [])
    assert blocked_model.blocked is True

    review = route("review-3d", ["godot"])
    assert review.engine == "codex" and review.model == "gpt-6-astra"
    assert review.required_capabilities == ["godot"]
    print("PASS: game-asset-router self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic forced routing for Gearbox game asset specialists.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--task-kind", choices=sorted(ROUTES))
    ap.add_argument("--available-capability", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.task_kind:
        ap.error("--task-kind is required")

    result = route(args.task_kind, args.available_capability)
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
