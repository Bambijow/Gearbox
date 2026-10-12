#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"orchestration-registry.json"

@dataclass
class Route:
    task_kind:str
    owner_engine:str
    owner_model:str
    owner_effort:str
    executor_engine:str|None
    executor_model:str|None
    executor_effort:str|None
    reviewer_engine:str|None
    reviewer_model:str|None
    reviewer_effort:str|None
    rationale:str

def _routes()->dict:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    return data["routing_defaults"]["product_quality"]

def route(task_kind:str)->Route:
    routes=_routes()
    if task_kind not in routes:
        raise SystemExit(f"unknown product-quality task kind: {task_kind}")
    cfg=routes[task_kind]
    rationale={
        "design-system":"Opus owns system semantics; Codex applies bounded migrations; fresh Claude reviews drift resolution",
        "a11y-audit":"fresh Claude reviews runtime accessibility; Codex may repair validated findings",
        "visual-regression":"fresh Claude adjudicates semantic before/after evidence rather than raw pixel distance",
        "content-design":"Claude owns language/state semantics; Codex may apply bounded copy/resource edits",
        "experience-perf":"Codex profiles and repairs the measured hot path; fresh Claude adjudicates evidence and trade-offs",
        "art-direction":"Opus owns cross-asset visual coherence; a fresh Claude reviewer checks drift",
        "audio-design":"Opus owns sonic direction; Codex may execute bounded engine/middleware wiring",
        "level-design":"Opus owns spatial/gameplay direction; Codex may execute blockout; fresh Opus reviews playtest evidence",
    }[task_kind]
    return Route(
        task_kind=task_kind,
        owner_engine=cfg["owner_engine"],owner_model=cfg["owner_model"],owner_effort=cfg["owner_effort"],
        executor_engine=cfg.get("executor_engine"),executor_model=cfg.get("executor_model"),executor_effort=cfg.get("executor_effort"),
        reviewer_engine=cfg.get("reviewer_engine"),reviewer_model=cfg.get("reviewer_model"),reviewer_effort=cfg.get("reviewer_effort"),
        rationale=rationale,
    )

def self_test()->None:
    ds=route("design-system")
    assert ds.owner_model=="claude-opus-5-5" and ds.executor_model=="gpt-6.1-sol"
    a11y=route("a11y-audit")
    assert a11y.owner_model=="sonnet" and a11y.owner_effort=="high"
    perf=route("experience-perf")
    assert perf.owner_engine=="codex" and perf.reviewer_model=="sonnet"
    level=route("level-design")
    assert level.owner_model=="claude-opus-5-5" and level.reviewer_model=="claude-opus-5-5"
    print("PASS: product-quality-router self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Deterministic specialist routing for Gearbox product/design quality lanes.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--task-kind",choices=sorted(_routes()))
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.task_kind:
        ap.error("--task-kind is required")
    result=route(args.task_kind)
    if args.json:
        print(json.dumps(asdict(result),indent=2,ensure_ascii=False))
    else:
        print(f"{result.task_kind}: {result.owner_engine}/{result.owner_model} effort={result.owner_effort}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
