#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

from redact import contains_secret_like

REQUIRED = ("## Summary", "## Evidence", "## Merge Danger")

def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)

def validate(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if contains_secret_like(text):
        fail("PR body contains obvious secret-like material")
    for heading in REQUIRED:
        if heading not in text:
            fail(f"missing required heading: {heading}")
    evidence = text.split("## Evidence", 1)[1].split("## Merge Danger", 1)[0]
    if not re.search(r"(?im)^\s*[-*]?\s*\*\*Before:\*\*", evidence):
        fail("Evidence must include **Before:**")
    if not re.search(r"(?im)^\s*[-*]?\s*\*\*After:\*\*", evidence):
        fail("Evidence must include **After:**")
    danger = text.split("## Merge Danger", 1)[1]
    door = re.search(r"(?im)\*\*Door:\*\*\s*(one-way|two-way)", danger)
    if not door:
        fail("Merge Danger must declare **Door:** one-way|two-way")
    if not re.search(r"(?im)\*\*Blast Radius:\*\*\s*\S+", danger):
        fail("Merge Danger must declare **Blast Radius:**")
    print(f"PASS: PR body contract ({door.group(1)} door)")
    return 0

def self_test() -> int:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"body.md"
        p.write_text(
            "## Summary\nAdds validation.\n\n"
            "## Evidence\n**Before:** invalid input passed.\n**After:** invalid input is rejected.\n\n"
            "## Merge Danger\n**Door:** two-way\n**Blast Radius:** API validation\n",
            encoding="utf-8",
        )
        validate(p)
    print("PASS: pr-body-guard self-test")
    return 0

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--body", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args=ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.body:
        ap.error("--body is required unless --self-test is used")
    return validate(args.body)

if __name__ == "__main__":
    raise SystemExit(main())
