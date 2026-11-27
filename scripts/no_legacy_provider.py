#!/usr/bin/env python3
"""CI gate: no executable invocation, imported package or CLI arg may target legacy Codex."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=[
 "scripts/gemini_worker.py", "scripts/claude_review_worker.py",
 "scripts/model_router.py", "scripts/review_router.py", "scripts/route_task.py",
 "scripts/game_asset_router.py", "scripts/web_design_router.py", "scripts/capabilities.py",
 "scripts/run_state.py", "scripts/behavior_eval.py", "scripts/orchestrator_guard.py",
 "scripts/gemini_claude_router.py", "orchestration-registry.json",
]

def check(root):
    errors=[]
    if (root/"scripts"/"codex_worker.py").exists():
        errors.append("legacy provider runner still exists")
    for relative in RUNTIME:
        path=root/relative
        if not path.is_file():
            errors.append(f"missing runtime {relative}")
        elif "codex" in path.read_text(encoding="utf-8").lower():
            errors.append(f"legacy provider string in executable route {relative}")
    return errors

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    errors=check(ROOT)
    for error in errors: print("FAIL:",error)
    if errors:raise SystemExit(1)
    print("PASS: no legacy provider executable route")

if __name__=="__main__":
    main()
