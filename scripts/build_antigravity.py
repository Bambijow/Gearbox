#!/usr/bin/env python3
"""Build a clean Antigravity distribution without importing Claude-only agent metadata."""
from __future__ import annotations
import argparse
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRS = ("skills", "scripts", "references", "schemas", "rules")
FILES = ("GEMINI.md", "hooks.json", "orchestration-registry.json", "prompt-budgets.json")


def copytree(src, dest):
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def build(destination: Path):
    destination = destination.resolve()
    if destination == ROOT or ROOT in destination.parents and destination.name in DIRS:
        raise ValueError("refusing to overwrite a source tree")
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    manifest = json.loads((ROOT / ".antigravity-plugin" / "plugin.json").read_text(encoding="utf-8"))
    (destination / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (destination / "README.md").write_text(
        (ROOT / ".antigravity-plugin" / "README.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    for folder in DIRS:
        if (ROOT / folder).is_dir():
            copytree(ROOT / folder, destination / folder)
    # Skill examples use Claude's plugin-root variable in the shared source.
    # Rewrite only the installed Gemini bundle, not the Claude Code source.
    for skill in (destination / "skills").glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        skill.write_text(text.replace("${CLAUDE_PLUGIN_ROOT}", "${PLUGIN_ROOT}"), encoding="utf-8")

    for name in FILES:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, destination / name)
    agents = destination / "agents"
    agents.mkdir()
    (agents / "gearbox-orchestrator.md").write_text(
        "---\nname: gearbox-orchestrator\ndescription: Orchestrate guarded Gearbox engineering tasks with Gemini.\n"
        "model: pro\nmainAgent: true\nsubagent: false\ncommandExecutionPolicy: sandbox\n---\n\n"
        "You are Gearbox's Gemini control plane. Follow rules/AGENTS.md and GEMINI.md. "
        "Do not author product code as the parent agent. Delegate bounded implementation to clean worktrees "
        "through supported worker helpers. Block unported Codex-only workflows rather than silently substituting.\n",
        encoding="utf-8",
    )
    (agents / "gearbox-inspector.md").write_text(
        "---\nname: gearbox-inspector\ndescription: Read-only repository and change inspection for Gearbox.\n"
        "model: inherit\nmainAgent: false\nsubagent: true\ncommandExecutionPolicy: off\n"
        "tools: [view_file, grep_search, find_by_name, send_message]\n---\n\n"
        "Inspect source, dependency edges and evidence. Do not mutate files. "
        "This is a Gemini inspection assistant, NOT an independent Claude review.\n",
        encoding="utf-8",
    )
    return destination


def self_test():
    with tempfile.TemporaryDirectory() as td:
        out = build(Path(td) / "gearbox")
        assert (out / "plugin.json").is_file()
        assert (out / "skills" / "issue" / "SKILL.md").is_file()
        assert (out / "scripts" / "gemini_worker.py").is_file()
        assert (out / "scripts" / "codex_worker.py").exists() is False
        assert len(list((out / "agents").glob("*.md"))) == 2
        assert "claude-opus" not in "\n".join(p.read_text() for p in (out / "agents").glob("*.md"))
        assert json.loads((out / "hooks.json").read_text())["gearbox-control-plane"]["enabled"]
    print("PASS: clean Antigravity bundle self-test")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("dist/gearbox-antigravity"))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    print(build(args.output))


if __name__ == "__main__":
    main()
