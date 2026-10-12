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
    },
    "surface": {
        "builder_effort": "medium",
        "review_model": "sonnet",
        "review_effort": "high",
    },
    "redesign": {
        "builder_effort": "high",
        "review_model": "claude-opus-5-5",
        "review_effort": "high",
    },
}

@dataclass
class Route:
    task_kind: str
    scope: str
    director_engine: str
    director_model: str
    director_effort: str
    builder_engine: str
    builder_model: str
    builder_effort: str
    reviewer_engine: str
    reviewer_model: str
    reviewer_effort: str
    preferred_director_capabilities: list[str]
    preferred_builder_capabilities: list[str]
    preferred_reviewer_capabilities: list[str]
    inspo_available: bool
    visual_evidence_available: bool
    rationale: str


def _keys(values: list[str]) -> set[str]:
    return {str(v).strip().casefold() for v in values if str(v).strip()}


def route(scope: str, claude_capabilities: list[str], codex_capabilities: list[str]) -> Route:
    claude = _keys(claude_capabilities)
    codex = _keys(codex_capabilities)
    cfg = SCOPES[scope]
    browser_names = {"browser", "playwright", "chrome", "chromium"}
    visual_evidence = bool((claude | codex) & browser_names)
    return Route(
        task_kind="web-design",
        scope=scope,
        director_engine="claude",
        director_model="claude-opus-5-5",
        director_effort="high",
        builder_engine="codex",
        builder_model="gpt-6.1-sol",
        builder_effort=cfg["builder_effort"],
        reviewer_engine="claude",
        reviewer_model=cfg["review_model"],
        reviewer_effort=cfg["review_effort"],
        preferred_director_capabilities=["inspo"],
        preferred_builder_capabilities=["browser"],
        preferred_reviewer_capabilities=["browser"],
        inspo_available="inspo" in claude,
        visual_evidence_available=visual_evidence,
        rationale=(
            "Opus 5.5 owns visual direction and design decisions; Codex Sol implements the approved "
            "contract; a fresh Claude reviewer judges rendered evidence. Inspo is evidence, never authority."
        ),
    )


def self_test() -> None:
    refine = route("refine", ["inspo"], ["browser"])
    assert refine.director_model == "claude-opus-5-5"
    assert refine.builder_model == "gpt-6.1-sol"
    assert refine.reviewer_model == "sonnet"
    assert refine.inspo_available is True
    assert refine.visual_evidence_available is True

    redesign = route("redesign", [], [])
    assert redesign.builder_effort == "high"
    assert redesign.reviewer_model == "claude-opus-5-5"
    assert redesign.visual_evidence_available is False
    print("PASS: web-design-router self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic routing for Gearbox web-design lanes.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--scope", choices=sorted(SCOPES), default="surface")
    ap.add_argument("--claude-capability", action="append", default=[])
    ap.add_argument("--codex-capability", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    result = route(args.scope, args.claude_capability, args.codex_capability)
    payload = asdict(result)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"web-design/{result.scope}: director={result.director_model} "
            f"builder={result.builder_model} reviewer={result.reviewer_model}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
