#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
AGENT_MODELS = {"inherit", "sonnet", "opus", "haiku", "fable"}
AGENT_EFFORTS = {"", "low", "medium", "high", "xhigh", "max"}
AGENT_COLORS = {"blue", "cyan", "green", "yellow", "magenta", "red"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(f"missing YAML frontmatter in {path.relative_to(ROOT)}")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError:
        fail(f"unterminated frontmatter in {path.relative_to(ROOT)}")
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def validate_agents() -> int:
    count = 0
    agents_dir = ROOT / "agents"
    if not agents_dir.exists():
        return 0
    for path in sorted(agents_dir.glob("*.md")):
        fields = parse_frontmatter(path)
        name = fields.get("name", "")
        desc = fields.get("description", "")
        model = fields.get("model", "")
        color = fields.get("color", "")
        effort = fields.get("effort", "")
        if not NAME_RE.match(name) or not (3 <= len(name) <= 50):
            fail(f"invalid agent name in {path.relative_to(ROOT)}: {name!r}")
        if len(desc) < 10 or "<example>" not in desc:
            fail(f"agent description should include triggering examples in {path.relative_to(ROOT)}")
        if model not in AGENT_MODELS and not model.startswith("claude-"):
            fail(f"invalid agent model in {path.relative_to(ROOT)}: {model!r}")
        if effort not in AGENT_EFFORTS:
            fail(f"invalid agent effort in {path.relative_to(ROOT)}: {effort!r}")
        if color not in AGENT_COLORS:
            fail(f"invalid agent color in {path.relative_to(ROOT)}: {color!r}")
        count += 1
    return count



def validate_hooks() -> int:
    hooks_path = ROOT / "hooks" / "hooks.json"
    if not hooks_path.exists():
        fail("missing hooks/hooks.json control-plane guard")
    data = load_json(hooks_path)
    hooks = data.get("hooks", {})
    for event in ("UserPromptExpansion", "PreToolUse", "Stop", "SessionEnd"):
        if event not in hooks:
            fail(f"control-plane hook missing event: {event}")
    pre = hooks.get("PreToolUse", [])
    if not any("Write" in str(group.get("matcher", "")) and "Bash" in str(group.get("matcher", "")) for group in pre):
        fail("PreToolUse guard must cover product file tools and Bash")
    guard = ROOT / "scripts" / "orchestrator_guard.py"
    if not guard.exists():
        fail("missing scripts/orchestrator_guard.py")
    report_guard = ROOT / "scripts" / "pr_report_guard.py"
    if not report_guard.exists():
        fail("missing scripts/pr_report_guard.py")
    body_guard = ROOT / "scripts" / "pr_body_guard.py"
    if not body_guard.exists():
        fail("missing scripts/pr_body_guard.py")
    redactor = ROOT / "scripts" / "redact.py"
    if not redactor.exists():
        fail("missing scripts/redact.py")
    for helper in ("plan_guard.py", "repair_findings.py", "finding_registry.py", "solutions_audit.py", "retro_bundle.py", "prompt_budget.py", "behavior_eval.py", "child_jobs.py", "usage_ledger.py"):
        if not (ROOT / "scripts" / helper).exists():
            fail(f"missing scripts/{helper}")
    if not (ROOT / "prompt-budgets.json").exists():\n        fail("missing prompt-budgets.json")\n    if not (ROOT / "evals" / "behavior").exists():\n        fail("missing evals/behavior")\n    return sum(len(v) for v in hooks.values() if isinstance(v, list))\n
def main() -> int:
    plugin_path = ROOT / ".claude-plugin" / "plugin.json"
    market_path = ROOT / ".claude-plugin" / "marketplace.json"
    plugin = load_json(plugin_path)
    market = load_json(market_path)

    name = plugin.get("name", "")
    if not NAME_RE.match(name):
        fail(f"invalid plugin name: {name!r}")

    configured = plugin.get("skills")
    if not isinstance(configured, list) or not configured:
        fail("plugin.json must contain a non-empty skills array")

    skill_names: set[str] = set()
    configured_paths: set[str] = set()
    for raw in configured:
        path = (ROOT / raw).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError:
            fail(f"skill escapes plugin root: {raw}")
        skill_file = path / "SKILL.md"
        if not skill_file.exists():
            fail(f"missing {skill_file.relative_to(ROOT)}")
        fields = parse_frontmatter(skill_file)
        skill_name = fields.get("name", "")
        description = fields.get("description", "")
        if not NAME_RE.match(skill_name):
            fail(f"invalid skill name in {skill_file.relative_to(ROOT)}: {skill_name!r}")
        if not description:
            fail(f"missing description in {skill_file.relative_to(ROOT)}")
        if skill_name in skill_names:
            fail(f"duplicate skill name: {skill_name}")
        skill_names.add(skill_name)
        configured_paths.add(str(path.relative_to(ROOT)))

    discovered = {
        str(p.parent.relative_to(ROOT))
        for p in (ROOT / "skills").glob("*/SKILL.md")
    }
    if discovered != configured_paths:
        missing = sorted(discovered - configured_paths)
        stale = sorted(configured_paths - discovered)
        fail(f"skill manifest drift; missing={missing}, stale={stale}")

    entries = market.get("plugins", [])
    if not any(entry.get("name") == name and entry.get("source") == "./" for entry in entries):
        fail("marketplace.json must expose this plugin with source './'")

    agent_count = validate_agents()
    hook_groups = validate_hooks()
    print(f"OK: {name} ({len(skill_names)} skills, {agent_count} agents, {hook_groups} hook groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
