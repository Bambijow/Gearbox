#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

SCOPES = {
    "refine": {
        "builder_effort": "medium",
        "review_model": "sonnet",
        "review_effort": "high",
        "auto_comp": False,
    },
    "surface": {
        "builder_effort": "medium",
        "review_model": "sonnet",
        "review_effort": "high",
        "auto_comp": True,
    },
    "redesign": {
        "builder_effort": "high",
        "review_model": "claude-opus-5-5",
        "review_effort": "high",
        "auto_comp": True,
    },
}

@dataclass
class Route:
    task_kind: str
    scope: str
    creative: bool
    director_engine: str
    director_model: str
    director_effort: str
    director_agent: str
    comp_generator_engine: str
    comp_generator_model: str
    comp_generator_effort: str
    comp_policy: str
    comp_enabled: bool
    comp_required: bool
    image_generation_available: bool
    image_generation_model: str
    image_edit_model: str
    comp_outputs: list[dict]
    blocked: bool
    blocker: str | None
    builder_engine: str
    builder_model: str
    builder_effort: str
    reviewer_engine: str
    reviewer_model: str
    reviewer_effort: str
    reviewer_agent: str
    interaction_gate_required: bool
    creative_gate_required: bool
    preferred_director_capabilities: list[str]
    preferred_builder_capabilities: list[str]
    preferred_reviewer_capabilities: list[str]
    inspo_available: bool
    visual_evidence_available: bool
    rationale: str


def _keys(values: list[str]) -> set[str]:
    return {str(v).strip().casefold() for v in values if str(v).strip()}


def route(
    scope: str,
    claude_capabilities: list[str],
    codex_capabilities: list[str],
    *,
    comp_policy: str = "auto",
    image_generation_available: bool = False,
    image_generation_model: str = "gpt-image-2.5-flare",
    image_edit_model: str = "gpt-image-2.5-sunburst",
    creative: bool = False,
) -> Route:
    claude = _keys(claude_capabilities)
    codex = _keys(codex_capabilities)
    cfg = SCOPES[scope]
    browser_names = {"browser", "playwright", "chrome", "chromium"}
    visual_evidence = bool((claude | codex) & browser_names)

    comp_required = comp_policy == "require"
    auto_comp = True if creative else cfg["auto_comp"]
    if comp_policy == "skip":
        comp_enabled = False
    elif comp_required:
        comp_enabled = image_generation_available
    else:
        comp_enabled = bool(auto_comp and image_generation_available)

    blocked = bool(comp_required and not image_generation_available)
    blocker = "WEB_COMP_BLOCKED: required image-generation path unavailable" if blocked else None

    builder_effort = "high" if creative else cfg["builder_effort"]
    reviewer_model = "claude-opus-5-5" if creative else cfg["review_model"]
    reviewer_effort = "high" if creative else cfg["review_effort"]

    return Route(
        task_kind="creative-web" if creative else "web-design",
        scope=scope,
        creative=creative,
        director_engine="claude",
        director_model="claude-opus-5-5",
        director_effort="high",
        director_agent="creative-web-director" if creative else "web-design-director",
        comp_generator_engine="codex",
        comp_generator_model="gpt-6.1-sol",
        comp_generator_effort="high" if creative or scope == "redesign" else "medium",
        comp_policy=comp_policy,
        comp_enabled=comp_enabled,
        comp_required=comp_required,
        image_generation_available=image_generation_available,
        image_generation_model=image_generation_model,
        image_edit_model=image_edit_model,
        comp_outputs=[
            {"kind": "desktop", "size": "1536x1024"},
            {"kind": "mobile", "size": "1024x1536"},
        ],
        blocked=blocked,
        blocker=blocker,
        builder_engine="codex",
        builder_model="gpt-6.1-sol",
        builder_effort=builder_effort,
        reviewer_engine="claude",
        reviewer_model=reviewer_model,
        reviewer_effort=reviewer_effort,
        reviewer_agent="creative-web-reviewer" if creative else "web-design-reviewer",
        interaction_gate_required=True,
        creative_gate_required=creative,
        preferred_director_capabilities=["inspo"],
        preferred_builder_capabilities=["browser"],
        preferred_reviewer_capabilities=["browser"],
        inspo_available="inspo" in claude,
        visual_evidence_available=visual_evidence,
        rationale=(
            "Opus 5.5 owns visual/interaction direction; optional Codex Sol comp generation turns the "
            "approved system into desktop/mobile visual authority; Codex Sol builds; a fresh Claude "
            "reviewer judges rendered evidence. Creative mode additionally requires interaction and "
            "creative-tech gates. Inspo and comps are evidence, never product truth."
        ),
    )


def self_test() -> None:
    refine = route("refine", ["inspo"], ["browser"], image_generation_available=True)
    assert refine.director_agent == "web-design-director"
    assert refine.builder_model == "gpt-6.1-sol"
    assert refine.reviewer_model == "sonnet"
    assert refine.interaction_gate_required is True
    assert refine.creative_gate_required is False
    assert refine.comp_enabled is False

    surface = route("surface", [], ["browser"], image_generation_available=True)
    assert surface.comp_enabled is True
    assert surface.comp_generator_model == "gpt-6.1-sol"
    assert surface.image_generation_model == "gpt-image-2.5-flare"

    creative = route("surface", ["inspo"], ["browser"], creative=True, image_generation_available=True)
    assert creative.task_kind == "creative-web"
    assert creative.director_agent == "creative-web-director"
    assert creative.builder_effort == "high"
    assert creative.reviewer_model == "claude-opus-5-5"
    assert creative.reviewer_agent == "creative-web-reviewer"
    assert creative.creative_gate_required is True
    assert creative.comp_enabled is True

    required = route("surface", [], [], comp_policy="require", image_generation_available=False)
    assert required.blocked is True
    assert required.blocker and "WEB_COMP_BLOCKED" in required.blocker
    print("PASS: web-design-router self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic routing for Gearbox web-design lanes.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--scope", choices=sorted(SCOPES), default="surface")
    ap.add_argument("--creative", action="store_true")
    ap.add_argument("--claude-capability", action="append", default=[])
    ap.add_argument("--codex-capability", action="append", default=[])
    ap.add_argument("--comp", choices=("auto", "require", "skip"), default="auto")
    ap.add_argument("--image-generation-available", action="store_true")
    ap.add_argument("--image-model", default="gpt-image-2.5-flare")
    ap.add_argument("--image-edit-model", default="gpt-image-2.5-sunburst")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    result = route(
        args.scope,
        args.claude_capability,
        args.codex_capability,
        comp_policy=args.comp,
        image_generation_available=args.image_generation_available,
        image_generation_model=args.image_model,
        image_edit_model=args.image_edit_model,
        creative=args.creative,
    )
    payload = asdict(result)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"{result.task_kind}/{result.scope}: director={result.director_model} "
            f"comp={'on' if result.comp_enabled else 'off'} "
            f"builder={result.builder_model} reviewer={result.reviewer_model}"
        )
    return 7 if result.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
