#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

CURRENT = ".gearbox"
LEGACY = ".steelthread"
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt", ".toml"}


def rewrite_text_paths(root: Path) -> int:
    changed = 0
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        new = text.replace(".steelthread/", ".gearbox/").replace("/.steelthread/", "/.gearbox/")
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def migrate(repo: Path, dry_run: bool = False) -> dict:
    repo = repo.resolve()
    old = repo / LEGACY
    new = repo / CURRENT
    result = {
        "repo": str(repo),
        "legacy": str(old),
        "current": str(new),
        "status": "noop",
        "rewritten_files": 0,
    }

    if not old.exists():
        result["reason"] = "no legacy .steelthread directory"
        return result

    if new.exists():
        result["status"] = "blocked"
        result["reason"] = "both .steelthread and .gearbox exist; refusing automatic merge"
        return result

    locks = list((old / "runs").glob("*/.lock")) if (old / "runs").exists() else []
    if locks:
        result["status"] = "blocked"
        result["reason"] = "legacy run lock(s) present"
        result["locks"] = [str(x) for x in locks]
        return result

    if dry_run:
        result["status"] = "would-migrate"
        return result

    os.replace(old, new)
    result["rewritten_files"] = rewrite_text_paths(new)
    ignore = new / ".gitignore"
    existing = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    if "runs/" not in existing.splitlines():
        with ignore.open("a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("runs/\n")

    marker = new / "migration.json"
    marker.write_text(json.dumps({
        "from": LEGACY,
        "to": CURRENT,
        "note": "Automatically migrated by Gearbox. Git/branch/PR identifiers were preserved.",
    }, indent=2) + "\n", encoding="utf-8")
    result["status"] = "migrated"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate legacy .steelthread project state to .gearbox safely.")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--hook", action="store_true", help="Read Claude Code hook event JSON from stdin and use its cwd")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo)
    if args.hook:
        try:
            event = json.loads(sys.stdin.read() or "{}")
            repo = Path(event.get("cwd") or args.repo)
        except Exception:
            repo = Path(args.repo)
    result = migrate(repo, args.dry_run)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"gearbox-migration: {result['status']}: {result.get('reason','')}")
    return 2 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
