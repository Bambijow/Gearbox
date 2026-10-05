#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path

REVIEW_HEADING = "## Review Focus"
FRONTIER_HEADING = "## Initial ready frontier"

def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")

def section(text: str, heading: str) -> str:
    pos = text.find(heading)
    if pos < 0:
        return ""
    tail = text[pos + len(heading):]
    m = re.search(r"(?m)^##\s+", tail)
    return tail[:m.start()] if m else tail

def fenced_chars(text: str) -> int:
    return sum(len(m.group(1)) for m in re.finditer(r"~~~[^\n]*\n(.*?)\n~~~", text, re.S))

def validate(plan: Path, spec: Path | None, require_dag: bool, max_ratio: float) -> None:
    text = plan.read_text(encoding="utf-8")
    if REVIEW_HEADING not in text:
        fail("missing ## Review Focus")
    focus = section(text, REVIEW_HEADING)
    items = [ln for ln in focus.splitlines() if re.match(r"^\s*[-*]\s+\S", ln)]
    if len(items) > 5:
        fail(f"Review Focus has {len(items)} items; maximum is 5")
    if require_dag and FRONTIER_HEADING not in text:
        fail("missing ## Initial ready frontier for executable DAG plan")
    if re.search(r"(?im)^\s*(?:[-*]\s*)?(?:TBD|TODO)(?:\s|:|$)", text):
        fail("plan contains an unresolved TBD/TODO placeholder")
    if spec and spec.exists():
        spec_text = spec.read_text(encoding="utf-8")
        base = max(len(spec_text), 1000)
        ratio = len(text) / base
        code_ratio = fenced_chars(text) / max(len(text), 1)
        if len(text) > 6000 and ratio > max_ratio:
            fail(f"plan/spec size ratio {ratio:.2f} exceeds {max_ratio:.2f}; compress implementation transcript")
        if len(text) > 4000 and ratio > 2.0 and code_ratio > 0.35:
            fail(f"code fences are {code_ratio:.0%} of an oversized plan; keep signatures/assertions, not bodies")
    print(f"PASS: lean plan contract ({len(items)} Review Focus item(s))")

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        spec=root/"spec.md"; spec.write_text("# Spec\n" + "x"*1800, encoding="utf-8")
        good=root/"good.md"
        good.write_text("# Plan\n\n## Review Focus\n- empty input -> reject\n\n## Initial ready frontier\n- T1\n", encoding="utf-8")
        validate(good,spec,True,4.0)
        bad=root/"bad.md"
        bad.write_text("# Plan\n\n## Review Focus\n" + "\n".join(f"- case {i}" for i in range(6)) + "\n\n## Initial ready frontier\n- T1\n", encoding="utf-8")
        try: validate(bad,spec,True,4.0)
        except SystemExit: pass
        else: fail("self-test expected >5 Review Focus items to fail")
    print("PASS: plan-guard self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Validate Gearbox lean implementation plans.")
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--spec", type=Path)
    ap.add_argument("--require-dag", action="store_true")
    ap.add_argument("--max-ratio", type=float, default=4.0)
    ap.add_argument("--self-test", action="store_true")
    a=ap.parse_args()
    if a.self_test:
        self_test(); return 0
    if not a.plan:
        ap.error("--plan is required unless --self-test is used")
    validate(a.plan,a.spec,a.require_dag,a.max_ratio)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
