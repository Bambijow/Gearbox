#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

ROUTES = {
    "design-system": {
        "owner_engine": "claude", "owner_model": "claude-opus-5-5", "owner_effort": "high",
        "executor_engine": "codex", "executor_model": "gpt-6.1-sol", "executor_effort": "medium",
        "reviewer_engine": "claude", "reviewer_model": "sonnet", "reviewer_effort": "high",
    },
    "a11y-audit": {
        "owner_engine": "claude", "owner_model": "sonnet", "owner_effort": "high",
        "executor_engine": "codex", "executor_model": "gpt-6.1-sol", "executor_effort": "medium",
        "reviewer_engine": None, "reviewer_model": None, "reviewer_effort": None,
    },
    "visual-regression": {
        "owner_engine": "claude", "owner_model": "sonnet", "owner_effort": "high",
        "executor_engine": None, "executor_model": None, "executor_effort": None,
        "reviewer_engine": None, "reviewer_model": None, "reviewer_effort": None,
    },
    "content-design": {
        "owner_engine": "claude", "owner_model": "sonnet", "owner_effort": "high",
        "executor_engine": "codex", "executor_model": "gpt-6.1-sol", "executor_effort": "medium",
        "reviewer_engine": None, "reviewer_model": None, "reviewer_effort": None,
    },
    "experience-perf": {
        "owner_engine": "codex", "owner_model": "gpt-6.1-sol", "owner_effort": "high",
        "executor_engine": "codex", "executor_model": "gpt-6.1-sol", "executor_effort": "high",
        "reviewer_engine": "claude", "reviewer_model": "sonnet", "reviewer_effort": "high",
    },
    "art-direction": {
        "owner_engine": "claude", "owner_model": "claude-opus-5-5", "owner_effort": "high",
        "executor_engine": None, "executor_model": None, "executor_effort": None,
        "reviewer_engine": "claude", "reviewer_model": "sonnet", "reviewer_effort": "high",
    },
    "audio-design": {
        "owner_engine": "claude", "owner_model": "claude-opus-5-5", "owner_effort": "high",
        "executor_engine": "codex", "executor_model": "gpt-6.1-sol", "executor_effort": "high",
        "reviewer_engine": "claude", "reviewer_model": "sonnet", "reviewer_effort": "high",
    },
    "level-design": {
        "owner_engine": "claude", "owner_model": "claude-opus-5-5", "owner_effort": "high",
        "executor_engine": "codex", "executor_model": "gpt-6.1-sol", "executor_effort": "high",
        "reviewer_engine": "claude", "reviewer_model": "claude-opus-5-5", "reviewer_effort": "high",
    },
}

@dataclass
class Route:
    task_kind: str
    owner_engine: str
    owner_model: str
    owner_effort: str
    executor_engine: str | None
    executor_model: str | None
    executor_effort: str | None
    reviewer_engine: str | None
    reviewer_model: str | None
    reviewer_effort: str | None
    rationale: str


def route(task_kind: str) -> Route:
    cfg = ROUTES[task_kind]
    rationale = {
        "design-system": "Opus owns system semantics; Codex applies bounded migrations; fresh Claude reviews drift resolution",
        "a11y-audit": "fresh Claude reviews runtime accessibility; Codex may repair validated findings",
        "visual-regression": "fresh Claude adjudicates semantic before/after evidence rather than raw pixel distance",
        "content-design": "Claude owns language/state semantics; Codex may apply bounded copy/resource edits",
        "experience-perf": "Codex profiles and repairs the measured hot path; fresh Claude adjudicates evidence and trade-offs",
        "art-direction": "Opus owns cross-asset visual coherence; a fresh Claude reviewer checks drift",
        "audio-design": "Opus owns sonic direction; Codex may execute bounded engine/middleware wiring",
        "level-design": "Opus owns spatial/gameplay direction; Codex may execute blockout; fresh Opus reviews playtest evidence",
    }[task_kind]
    return Route(task_kind=task_kind, rationale=rationale, **cfg)


def self_test() -> None:
    ds = route("design-system")
    assert ds.owner_model == "claude-opus-5-5"
    assert ds.executor_model == "gpt-6.1-sol"
    a11y = route("a11y-audit")
    assert a11y.owner_model == "sonnet" and a11y.owner_effort == "high"
    perf = route("experience-perf")
    assert perf.owner_engine == "codex" and perf.reviewer_model == "sonnet"
    level = route("level-design")
    assert level.owner_model == "claude-opus-5-5"
    assert level.executor_model == "gpt-6.1-sol"
    assert level.reviewer_model == "claude-opus-5-5"
    print("PASS: product-quality-router self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic specialist routing for Gearbox product/design quality lanes.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--task-kind", choices=sorted(ROUTES))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.task_kind:
        ap.error("--task-kind is required")
    result = route(args.task_kind)
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(f"{result.task_kind}: {result.owner_engine}/{result.owner_model} effort={result.owner_effort}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
