#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

TIERS = {"bounded", "normal", "deep", "exceptional"}
RISKS = {"low", "medium", "high", "critical"}


@dataclass
class ReviewRoute:
    implementation_engine: str
    review_engine: str
    model_class: str
    model: str
    effort: str
    agent: str | None
    rationale: str


def route(args: argparse.Namespace) -> ReviewRoute:
    impl = args.implementation_engine
    tier = args.task_tier
    risk = args.risk

    if impl == "claude":
        if tier == "bounded":
            return ReviewRoute(impl, "gemini", "economy", args.hydrogen_model, "low", None,
                               "hybrid cross-provider review: bounded Claude work is checked by Gemini Hydrogen/low")
        if tier == "normal":
            return ReviewRoute(impl, "gemini", "standard", args.neon_model, "medium", None,
                               "hybrid cross-provider review: normal Claude work is checked by Gemini Neon/medium")
        if tier == "deep":
            return ReviewRoute(impl, "gemini", "standard", args.neon_model, "high", None,
                               "hybrid cross-provider review: deep Claude work is checked by Gemini Neon/high")
        effort = "high" if risk == "critical" or args.escalated else "medium"
        return ReviewRoute(impl, "gemini", "frontier", args.carbon_model, effort, None,
                           "hybrid cross-provider review: exceptional Claude work receives an independent Gemini Carbon review")

    if impl == "gemini":
        if tier == "bounded":
            return ReviewRoute(impl, "claude", "economy", args.haiku_model, "low", "task-reviewer-low",
                               "hybrid cross-provider review: bounded Gemini work is checked by Claude Haiku/low")
        if tier == "normal":
            return ReviewRoute(impl, "claude", "standard", args.sonnet_model, "medium", "task-reviewer",
                               "hybrid cross-provider review: normal Gemini work is checked by Claude Sonnet/medium")
        if tier == "deep":
            return ReviewRoute(impl, "claude", "deep", args.opus_model, "high", "task-reviewer-high",
                               "hybrid cross-provider review: deep Gemini work is checked by Claude Opus/high")
        return ReviewRoute(impl, "claude", "deep", args.opus_model, "xhigh", "task-reviewer-xhigh",
                           "hybrid cross-provider review: exceptional Gemini work is checked by Claude Opus/xhigh")

    raise ValueError(f"unsupported implementation engine: {impl}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Choose the opposite-provider task reviewer for Gearbox hybrid mode.")
    p.add_argument("--implementation-engine", default="gemini", choices=["claude", "gemini"])
    p.add_argument("--task-tier", default="normal", choices=sorted(TIERS))
    p.add_argument("--risk", default="medium", choices=sorted(RISKS))
    p.add_argument("--escalated", action="store_true")
    p.add_argument("--hydrogen-model", default="gemini-4-hydrogen-low")
    p.add_argument("--neon-model", default="gemini-4-neon-medium")
    p.add_argument("--carbon-model", default="gemini-4-carbon-high")
    p.add_argument("--haiku-model", default="haiku")
    p.add_argument("--sonnet-model", default="sonnet")
    p.add_argument("--opus-model", default="opus")
    p.add_argument("--json", action="store_true")
    p.add_argument("--self-test", action="store_true")
    return p


def self_test() -> None:
    p = parser()
    cases = [
        (["--implementation-engine", "claude", "--task-tier", "bounded", "--risk", "low"], "gemini", "gemini-4-hydrogen-low", "low", None),
        (["--implementation-engine", "claude", "--task-tier", "normal", "--risk", "medium"], "gemini", "gemini-4-neon-medium", "medium", None),
        (["--implementation-engine", "claude", "--task-tier", "deep", "--risk", "high"], "gemini", "gemini-4-neon-medium", "high", None),
        (["--implementation-engine", "claude", "--task-tier", "exceptional", "--risk", "critical"], "gemini", "gemini-4-carbon-high", "high", None),
        (["--implementation-engine", "gemini", "--task-tier", "bounded", "--risk", "low"], "claude", "haiku", "low", "task-reviewer-low"),
        (["--implementation-engine", "gemini", "--task-tier", "normal", "--risk", "medium"], "claude", "sonnet", "medium", "task-reviewer"),
        (["--implementation-engine", "gemini", "--task-tier", "deep", "--risk", "high"], "claude", "opus", "high", "task-reviewer-high"),
        (["--implementation-engine", "gemini", "--task-tier", "exceptional", "--risk", "critical"], "claude", "opus", "xhigh", "task-reviewer-xhigh"),
    ]
    for argv, engine, model, effort, agent in cases:
        r = route(p.parse_args(argv))
        assert r.review_engine == engine, (argv, asdict(r))
        assert r.model == model, (argv, asdict(r))
        assert r.effort == effort, (argv, asdict(r))
        assert r.agent == agent, (argv, asdict(r))
    print("PASS: review-router")


def main() -> int:
    p = parser()
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    result = route(args)
    payload = asdict(result)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        agent = f" agent={result.agent}" if result.agent else ""
        print(f"{result.review_engine}:{result.model} effort={result.effort}{agent} :: {result.rationale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
