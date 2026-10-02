#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

CHEAP_KINDS = {
    "docs", "changelog", "formatting", "metadata", "fixtures",
    "generated-mappings", "generated", "rename", "wiring", "simple-test",
}
NORMAL_KINDS = {"feature", "bugfix", "test", "ui", "api", "implementation"}
DEEP_KINDS = {
    "debug", "review", "research", "simplify", "migration", "auth",
    "security", "concurrency", "persistence", "architecture",
}
FRONTIER_ELIGIBLE_KINDS = {
    "debug", "migration", "auth", "security", "concurrency",
    "persistence", "architecture", "review",
}

BASE = {**{k: 0 for k in CHEAP_KINDS}, **{k: 2 for k in NORMAL_KINDS}, **{k: 4 for k in DEEP_KINDS}}
RISK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
AMBIGUITY = {"low": 0, "medium": 1, "high": 2}
BREADTH = {"narrow": 0, "moderate": 1, "broad": 2}
VERIFICATION = {"strong": -1, "medium": 0, "weak": 1}

@dataclass
class Route:
    tier: str
    model_class: str
    model: str
    effort: str
    score: int
    frontier: bool
    rationale: str


def route(args: argparse.Namespace) -> Route:
    kind = args.task_kind
    score = BASE.get(kind, 2)
    score += RISK[args.risk]
    score += AMBIGUITY[args.ambiguity]
    score += BREADTH[args.breadth]
    score += VERIFICATION[args.verification]
    score += min(args.failed_attempts, 2) * 2
    score = max(score, 0)

    # Hard ceiling: cheap work never burns the frontier model merely because a
    # noisy classifier marked it risky. Architecture decisions must be split
    # into an architecture task plus a separate cheap documentation task.
    if kind in CHEAP_KINDS:
        effort = "medium" if args.risk in {"high", "critical"} else "low"
        return Route(
            tier="bounded",
            model_class="economy",
            model=args.luna_model,
            effort=effort,
            score=score,
            frontier=False,
            rationale=f"{kind} is hard-capped to Luna-class work; expensive reasoning is not justified for the deliverable",
        )

    exceptional_shape = (
        kind in FRONTIER_ELIGIBLE_KINDS
        and args.risk == "critical"
        and args.ambiguity == "high"
        and args.breadth == "broad"
        and args.verification == "weak"
    )
    escalated = kind in FRONTIER_ELIGIBLE_KINDS and args.failed_attempts >= 2 and score >= 8
    frontier = bool(args.force_frontier or exceptional_shape or escalated)

    if frontier:
        effort = "high" if args.failed_attempts >= 3 or args.frontier_high else "medium"
        reason = "explicit frontier override" if args.force_frontier else (
            "exceptional critical shape" if exceptional_shape else "deep route failed repeatedly"
        )
        return Route(
            tier="exceptional",
            model_class="frontier",
            model=args.astra_model,
            effort=effort,
            score=score,
            frontier=True,
            rationale=f"{reason}; Astra is reserved for exceptional escalation only",
        )

    if score <= 2:
        return Route("bounded", "economy", args.luna_model, "low", score, False, "bounded deterministic work")
    if score <= 6:
        return Route("normal", "standard", args.sol_model, "medium", score, False, "ordinary engineering work; Sol is the default coding model")
    return Route("deep", "standard", args.sol_model, "high", score, False, "deep engineering task; stay on Sol and raise effort before considering Astra")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Deterministic Codex model/effort router for Gearbox.")
    p.add_argument("--task-kind", default="implementation", choices=sorted(CHEAP_KINDS | NORMAL_KINDS | DEEP_KINDS))
    p.add_argument("--risk", default="medium", choices=RISK)
    p.add_argument("--ambiguity", default="low", choices=AMBIGUITY)
    p.add_argument("--breadth", default="moderate", choices=BREADTH)
    p.add_argument("--verification", default="strong", choices=VERIFICATION)
    p.add_argument("--failed-attempts", type=int, default=0)
    p.add_argument("--luna-model", default="gpt-6-luna")
    p.add_argument("--sol-model", default="gpt-6.1-sol")
    p.add_argument("--astra-model", default="gpt-6-astra")
    p.add_argument("--force-frontier", action="store_true")
    p.add_argument("--frontier-high", action="store_true", help="Allow Astra/high on an already frontier-worthy task.")
    p.add_argument("--json", action="store_true")
    p.add_argument("--self-test", action="store_true")
    return p


def self_test() -> None:
    p = parser()
    cases = [
        (["--task-kind", "docs", "--risk", "critical", "--ambiguity", "high", "--breadth", "broad", "--verification", "weak"], "gpt-6-luna", "low_or_medium"),
        (["--task-kind", "feature", "--risk", "medium", "--ambiguity", "low", "--breadth", "moderate", "--verification", "strong"], "gpt-6.1-sol", "medium"),
        (["--task-kind", "migration", "--risk", "high", "--ambiguity", "medium", "--breadth", "broad", "--verification", "weak"], "gpt-6.1-sol", "high"),
        (["--task-kind", "debug", "--risk", "high", "--ambiguity", "high", "--breadth", "broad", "--verification", "weak", "--failed-attempts", "2"], "gpt-6-astra", "medium"),
    ]
    for argv, model, effort in cases:
        a = p.parse_args(argv)
        r = route(a)
        assert r.model == model, (argv, asdict(r))
        if effort != "low_or_medium":
            assert r.effort == effort, (argv, asdict(r))
        else:
            assert r.effort in {"low", "medium"}, (argv, asdict(r))
    print("PASS: model-router")


def main() -> int:
    p = parser()
    a = p.parse_args()
    if a.self_test:
        self_test()
        return 0
    r = route(a)
    payload = asdict(r)
    if a.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"{r.model} effort={r.effort} tier={r.tier} score={r.score} :: {r.rationale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
