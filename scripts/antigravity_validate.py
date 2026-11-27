#!/usr/bin/env python3
"""Offline Antigravity manifest and hooks contract smoke checks."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(root):
    errors = []
    p = root / ".antigravity-plugin" / "plugin.json"
    hooks = root / "hooks.json"
    try:
        manifest = json.loads(p.read_text(encoding="utf-8"))
        hook_groups = json.loads(hooks.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [str(exc)]
    if manifest.get("name") != "gearbox":
        errors.append("Antigravity plugin name must be gearbox")
    if manifest.get("$schema") != "https://antigravity.google/schemas/v1/plugin.json":
        errors.append("Unexpected Antigravity schema")
    for name, group in hook_groups.items():
        if not isinstance(group, dict):
            errors.append("Invalid hook group: " + name)
            continue
        for event in ("PreInvocation", "Stop"):
            if not isinstance(group.get(event), list):
                errors.append("Missing flat hook list: " + event)
        if not isinstance(group.get("PreToolUse"), list):
            errors.append("Missing PreToolUse matcher list")
        for item in group.get("PreToolUse", []):
            if "matcher" not in item or not isinstance(item.get("hooks"), list):
                errors.append("Missing matcher/hooks in PreToolUse")
    for path in ("GEMINI.md", "rules/AGENTS.md", "scripts/gemini_worker.py",
                 "scripts/gemini_claude_router.py", "scripts/antigravity_guard.py"):
        if not (root / path).is_file():
            errors.append("Missing native component: " + path)
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        assert validate(ROOT) == [], validate(ROOT)
        print("PASS: Antigravity static manifest validation")
        return
    for issue in validate(ROOT):
        print("ERROR: " + issue)
    if validate(ROOT):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
