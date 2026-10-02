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
            return ReviewRoute(impl, "codex", "economy", args.luna_model, "low", None,
                               "hybrid cross-provider review: bounded Claude work is checked by Codex Luna/low")
        if tier == "normal":
            return ReviewRoute(impl, "codex", "standard", args.sol_model, "medium", None,
                               "hybrid cross-provider review: normal Claude work is checked by Codex Sol/medium")
        if tier == "deep":
            return ReviewRoute(impl, "codex", "standard", args.sol_model, "high", None,
                               "hybrid cross-provider review: deep Claude work is checked by Codex Sol/high")
        effort = "high" if risk == "critical" or args.escalated else "medium"
        return ReviewRoute(impl, "codex", "frontier", args.astra_model, effort, None,
                           "hybrid cross-provider review: exceptional Claude work receives an independent Codex Astra review")

    if impl == "codex":
        if tier == "bounded":
            return ReviewRoute(impl, "claude", "economy", args.haiku_model, "low", "task-reviewer-low",
                               "hybrid cross-provider review: bounded Codex work is checked by Claude Haiku/low")
        if tier == "normal":
            return ReviewRoute(impl, "claude", "standard", args.sonnet_model, "medium", "task-reviewer",
                               "hybrid cross-provider review: normal Codex work is checked by Claude Sonnet/medium")
        if tier == "deep":
            return ReviewRoute(impl, "claude", "deep", args.opus_model, "high", "task-reviewer-high",
                               "hybrid cross-provider review: deep Codex work is checked by Claude Opus/high")
        return ReviewRoute(impl, "claude", "deep", args.opus_model, "xhigh", "task-reviewer-xhigh",
                           "hybrid cross-provider review: exceptional Codex work is checked by Claude Opus/xhigh")

    raise ValueError(f"unsupported implementation engine: {impl}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Choose the opposite-provider task reviewer for Gearbox hybrid mode.")
    p.add_argument("--implementation-engine", default="codex", choices=["claude", "codex"])
    p.add_argument("--task-tier", default="normal", choices=sorted(TIERS))
    p.add_argument("--risk", default="medium", choices=sorted(RISKS))
    p.add_argument("--escalated", action="store_true")
    p.add_argument("--luna-model", default="gpt-6-luna")
    p.add_argument("--sol-model", default="gpt-6.1-sol")
    p.add_argument("--astra-model", default="gpt-6-astra")
    p.add_argument("--haiku-model", default="haiku")
    p.add_argument("--sonnet-model", default="sonnet")
    p.add_argument("--opus-model", default="opus")
    p.add_argument("--json", action="store_true")
    p.add_argument("--self-test", action="store_true")
    return p


def self_test() -> None:
    p = parser()
    cases = [
        (["--implementation-engine", "claude", "--task-tier", "bounded", "--risk", "low"], "codex", "gpt-6-luna", "low", None),
        (["--implementation-engine", "claude", "--task-tier", "normal", "--risk", "medium"], "codex", "gpt-6.1-sol", "medium", None),
        (["--implementation-engine", "claude", "--task-tier", "deep", "--risk", "high"], "codex", "gpt-6.1-sol", "high", None),
        (["--implementation-engine", "claude", "--task-tier", "exceptional", "--risk", "critical"], "codex", "gpt-6-astra", "high", None),
        (["--implementation-engine", "codex", "--task-tier", "bounded", "--risk", "low"], "claude", "haiku", "low", "task-reviewer-low"),
        (["--implementation-engine", "codex", "--task-tier", "normal", "--risk", "medium"], "claude", "sonnet", "medium", "task-reviewer"),
        (["--implementation-engine", "codex", "--task-tier", "deep", "--risk", "high"], "claude", "opus", "high", "task-reviewer-high"),
        (["--implementation-engine", "codex", "--task-tier", "exceptional", "--risk", "critical"], "claude", "opus", "xhigh", "task-reviewer-xhigh"),
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
