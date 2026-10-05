#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "prompt-budgets.json"

def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")

def load_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid prompt budget config: {exc}")
    if data.get("schema_version") != 1 or not isinstance(data.get("skills"), dict):
        fail("prompt-budgets.json must use schema_version 1 with a skills object")
    return data

def check(root: Path, config_path: Path) -> list[dict]:
    cfg = load_config(config_path)
    discovered = {p.parent.name: p for p in (root / "skills").glob("*/SKILL.md")}
    configured = set(cfg["skills"])
    missing = sorted(set(discovered) - configured)
    stale = sorted(configured - set(discovered))
    if missing or stale:
        fail(f"budget manifest drift; missing={missing}, stale={stale}")
    rows=[]
    errors=[]
    for name in sorted(discovered):
        entry=cfg["skills"][name]
        max_bytes=entry.get("max_bytes")
        if not isinstance(max_bytes, int) or max_bytes < 512:
            errors.append(f"{name}: invalid max_bytes {max_bytes!r}")
            continue
        size=len(discovered[name].read_bytes())
        headroom=max_bytes-size
        rows.append({"skill":name,"bytes":size,"max_bytes":max_bytes,"headroom":headroom,"class":entry.get("class","")})
        if headroom < 0:
            errors.append(f"{name}: {size} bytes exceeds {max_bytes} by {-headroom}")
    if errors:
        fail("; ".join(errors))
    return rows

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        (root/"skills"/"a").mkdir(parents=True)
        (root/"skills"/"a"/"SKILL.md").write_text("x"*10,encoding="utf-8")
        cfg=root/"prompt-budgets.json"
        cfg.write_text(json.dumps({"schema_version":1,"skills":{"a":{"max_bytes":512}}}),encoding="utf-8")
        rows=check(root,cfg)
        assert rows[0]["headroom"]==502
        cfg.write_text(json.dumps({"schema_version":1,"skills":{"a":{"max_bytes":5}}}),encoding="utf-8")
        try: check(root,cfg)
        except SystemExit: pass
        else: fail("self-test expected invalid budget to fail")
    print("PASS: prompt-budget self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Enforce Gearbox per-skill prompt byte ratchets.")
    ap.add_argument("--config",type=Path,default=DEFAULT_CONFIG)
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--check",action="store_true")
    ap.add_argument("--report",action="store_true")
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:
        self_test(); return 0
    rows=check(a.root.resolve(),a.config.resolve())
    if a.report:
        for r in rows:
            print(f"{r['skill']:18} {r['bytes']:5}/{r['max_bytes']:5}  headroom={r['headroom']:4}  {r['class']}")
    print(f"PASS: prompt budgets ({len(rows)} skills)")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
