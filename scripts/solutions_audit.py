#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import tempfile
from datetime import date
from pathlib import Path

REQUIRED=("title","tags","areas","verified_against","last_verified")
DATE_RE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA_RE=re.compile(r"^[0-9a-fA-F]{7,40}$")

def parse_fm(text: str) -> dict[str,str]:
    if not text.startswith("---\n"):
        return {}
    parts=text.split("---\n",2)
    if len(parts)<3:
        return {}
    out={}
    for line in parts[1].splitlines():
        if not line.strip() or line.startswith((" ","\t","#")) or ":" not in line:
            continue
        k,v=line.split(":",1)
        out[k.strip()]=v.strip().strip('"').strip("'")
    return out

def listish(v: str) -> bool:
    return v.startswith("[") and v.endswith("]") and bool(v[1:-1].strip())

def audit(root: Path, strict: bool, check_index: bool, allow_missing: bool) -> tuple[list[str],list[str]]:
    errors=[]
    warnings=[]
    if not root.exists():
        if allow_missing:
            return errors,warnings
        return [f"missing solutions directory: {root}"],warnings
    notes=[
        p for p in root.rglob("*.md")
        if p.name.lower() not in {"index.md","readme.md"}
    ]
    titles={}
    for p in notes:
        rel=p.relative_to(root)
        fm=parse_fm(p.read_text(encoding="utf-8",errors="replace"))
        if not fm:
            (errors if strict else warnings).append(f"{rel}: missing/invalid YAML frontmatter")
            continue
        for k in REQUIRED:
            if not fm.get(k):
                (errors if strict else warnings).append(f"{rel}: missing {k}")
        if fm.get("tags") and not listish(fm["tags"]):
            errors.append(f"{rel}: tags must be a non-empty inline list")
        if fm.get("areas") and not listish(fm["areas"]):
            errors.append(f"{rel}: areas must be a non-empty inline list")
        if fm.get("last_verified"):
            if not DATE_RE.match(fm["last_verified"]):
                errors.append(f"{rel}: last_verified must be YYYY-MM-DD")
            else:
                try:
                    date.fromisoformat(fm["last_verified"])
                except ValueError:
                    errors.append(f"{rel}: invalid last_verified date")
        if fm.get("verified_against") and not SHA_RE.match(fm["verified_against"]):
            warnings.append(f"{rel}: verified_against is not a git SHA")
        if "retire_when" in fm and not fm["retire_when"].strip():
            errors.append(f"{rel}: retire_when must be a non-empty scalar when present")
        title=fm.get("title")
        if title:
            if title in titles:
                errors.append(f"duplicate title: {title!r} in {titles[title]} and {rel}")
            titles[title]=str(rel)
    if check_index and notes:
        idx=root/"index.md"
        if not idx.exists():
            errors.append("index.md missing")
        else:
            body=idx.read_text(encoding="utf-8",errors="replace")
            linked={
                m.group(1).split("#",1)[0]
                for m in re.finditer(r"\]\(([^)]+\.md(?:#[^)]+)?)\)",body)
            }
            expected={p.relative_to(root).as_posix() for p in notes}
            missing=sorted(expected-linked)
            if missing:
                errors.append("index.md missing note(s): "+", ".join(missing))
    return errors,warnings

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"solutions"
        root.mkdir()
        (root/"good.md").write_text(
            "---\ntitle: Good\ntags: [a]\nareas: [src/**]\n"
            "verified_against: abcdef1\nlast_verified: 2026-10-05\n"
            "retire_when: upstream bug is fixed\n---\n# Good\n",
            encoding="utf-8",
        )
        (root/"index.md").write_text("# Solution index\n\n[Good](good.md)\n",encoding="utf-8")
        errors,_=audit(root,True,True,False)
        if errors:
            raise SystemExit("FAIL: "+str(errors))
        (root/"bad.md").write_text("# no frontmatter\n",encoding="utf-8")
        errors,_=audit(root,True,False,False)
        if not errors:
            raise SystemExit("FAIL: expected bad note to fail")
    print("PASS: solutions-audit self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Audit Gearbox docs/solutions metadata and index deterministically.")
    ap.add_argument("--dir",type=Path,default=Path("docs/solutions"))
    ap.add_argument("--strict",action="store_true")
    ap.add_argument("--check-index",action="store_true")
    ap.add_argument("--allow-missing",action="store_true")
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:
        self_test()
        return 0
    errors,warnings=audit(a.dir,a.strict,a.check_index,a.allow_missing)
    for w in warnings:
        print("WARN:",w)
    for e in errors:
        print("ERROR:",e)
    if errors:
        return 1
    print(f"PASS: solutions audit ({a.dir})")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
