#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import sys
import tempfile
import time
from pathlib import Path

GUARDED_COMMANDS = {
    "issue", "loop", "flow", "brainstorm", "resume", "continue-pr"
}
APPROVED_SCRIPTS = {
    "run_state.py", "model_router.py", "review_router.py", "codex_worker.py",
    "evidence.py", "worktree_manager.py", "orchestrator_guard.py", "migrate_legacy.py",
    "redact.py", "pr_report_guard.py", "pr_body_guard.py",
    "plan_guard.py", "repair_findings.py", "finding_registry.py", "solutions_audit.py", "retro_bundle.py",\n    "child_jobs.py", "usage_ledger.py"
}
READ_COMMANDS = {"pwd", "ls", "rg", "grep", "head", "tail", "cat", "wc", "stat", "realpath"}
SHELL_META = re.compile(r"(?:\n|\r|;|&&|\|\||(?<!\\)[|<>`]|\$\()")


def _event() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _scope(cwd: str) -> str:
    return hashlib.sha256(str(Path(cwd).resolve()).encode()).hexdigest()[:20]


def _marker(cwd: str, session_id: str) -> Path:
    root = Path(tempfile.gettempdir()) / "gearbox-control-plane" / _scope(cwd)
    root.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    return root / f"{safe}.json"


def _command_basename(name: str) -> str:
    if ":" in name:
        name = name.rsplit(":", 1)[-1]
    return name


def _load_simple_config(cwd: Path) -> dict[str, str]:
    p = cwd / ".gearbox" / "config.md"
    if not p.exists():
        return {}
    out: dict[str, str] = {}
    text = p.read_text(errors="replace")
    if not text.startswith("---"):
        return out
    try:
        block = text.split("---", 2)[1]
    except Exception:
        return out
    for line in block.splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip().strip('"').strip("'")
        if k.strip() in {"specs_dir", "plans_dir"} and v:
            out[k.strip()] = v
    return out


def _allowed_write_roots(cwd: Path) -> list[Path]:
    cfg = _load_simple_config(cwd)
    roots = [cwd / ".gearbox" / "runs"]
    roots.append(cwd / cfg.get("specs_dir", "docs/engineering/specs"))
    roots.append(cwd / cfg.get("plans_dir", "docs/engineering/plans"))
    return [p.resolve() for p in roots]


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _edit_allowed(event: dict) -> tuple[bool, str]:
    cwd = Path(event.get("cwd") or ".").resolve()
    ti = event.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("notebook_path") or ti.get("path")
    if not raw:
        return False, "main-thread file mutation has no resolvable path"
    p = Path(raw)
    if not p.is_absolute():
        p = cwd / p
    for root in _allowed_write_roots(cwd):
        if _inside(p, root):
            return True, "orchestration artifact/spec/plan"
    return False, f"product write denied for main orchestrator: {p}"


def _safe_git(tokens: list[str]) -> bool:
    # Accept optional `git -C <path>` then a narrow command set.
    i = 1
    if len(tokens) >= 4 and tokens[1] == "-C":
        i = 3
    if len(tokens) <= i:
        return False
    sub = tokens[i]
    args = tokens[i + 1:]
    if sub in {"status", "diff", "show", "log", "rev-parse", "ls-files", "merge-base", "check-ignore", "cat-file", "diff-tree", "name-rev"}:
        return True
    if sub == "remote":
        return args in [["-v"], ["get-url", "origin"]] or (len(args) >= 2 and args[0] == "get-url")
    if sub == "branch":
        return args == ["--show-current"]
    if sub == "worktree":
        # Worktree lifecycle is orchestration infrastructure, not product authorship.
        return bool(args) and args[0] == "list"
    return False


def _safe_gh(tokens: list[str]) -> bool:
    if len(tokens) < 3:
        return False
    area, action = tokens[1], tokens[2]
    return (area, action) in {
        ("issue", "view"), ("issue", "list"), ("issue", "create"),
        ("pr", "view"), ("pr", "checks"), ("pr", "diff"), ("pr", "list"),
        ("run", "view"), ("run", "list"),
    }


def _safe_python(tokens: list[str]) -> bool:
    if not tokens or Path(tokens[0]).name not in {"python", "python3"} or len(tokens) < 2:
        return False
    script = tokens[1].strip('"\'')
    return Path(script).name in APPROVED_SCRIPTS and "/scripts/" in script.replace("\\", "/")


def _safe_read_command(tokens: list[str]) -> bool:
    if not tokens or Path(tokens[0]).name not in READ_COMMANDS:
        return False
    cmd = Path(tokens[0]).name
    if cmd == "find" and any(t in {"-delete", "-exec", "-execdir", "-ok", "-okdir"} for t in tokens):
        return False
    return True


def _bash_allowed(command: str) -> tuple[bool, str]:
    if not command.strip():
        return False, "empty Bash command"
    if SHELL_META.search(command):
        return False, "shell composition/redirection is disabled for the main orchestrator"
    try:
        tokens = shlex.split(command)
    except Exception:
        return False, "unable to parse Bash command safely"
    if not tokens:
        return False, "empty Bash command"
    first = Path(tokens[0]).name
    if first == "git" and _safe_git(tokens):
        return True, "read/worktree git operation"
    if first == "gh" and _safe_gh(tokens):
        return True, "read-only GitHub operation"
    if first in {"python", "python3"} and _safe_python(tokens):
        return True, "approved Gearbox orchestration script"
    if _safe_read_command(tokens):
        return True, "read-only shell inspection"
    return False, f"Bash command is not in the control-plane allowlist: {first}"


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason + ". Delegate product mutation to a Gearbox worker/role agent."
        }
    }))


def activate(event: dict) -> int:
    sid, cwd = event.get("session_id", ""), event.get("cwd", ".")
    name = _command_basename(event.get("command_name", ""))
    if name not in GUARDED_COMMANDS:
        return 0
    p = _marker(cwd, sid)
    p.write_text(json.dumps({"session_id": sid, "cwd": str(Path(cwd).resolve()), "command": name, "created_at": time.time()}, indent=2) + "\n")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptExpansion",
            "additionalContext": "GEARBOX CONTROL PLANE ACTIVE. The main thread may plan, inspect, route and adjudicate, but must not author product code/tests/migrations/config/public docs/solution notes. Delegate every product mutation, including tiny edits, to a worker or dedicated mutation-role agent."
        }
    }))
    return 0


def deactivate(event: dict) -> int:
    sid, cwd = event.get("session_id", ""), event.get("cwd", ".")
    if sid:
        _marker(cwd, sid).unlink(missing_ok=True)
    return 0


def check(event: dict) -> int:
    sid, cwd = event.get("session_id", ""), event.get("cwd", ".")
    if not sid or not _marker(cwd, sid).exists():
        return 0
    # Plugin hooks also fire inside subagents. The product-write ban is specifically for the parent control plane.
    if event.get("agent_id"):
        return 0
    tool = event.get("tool_name", "")
    if tool in {"Write", "Edit", "NotebookEdit"}:
        ok, why = _edit_allowed(event)
        if not ok:
            _deny(why)
        return 0
    if tool == "Bash":
        cmd = (event.get("tool_input") or {}).get("command", "")
        ok, why = _bash_allowed(cmd)
        if not ok:
            _deny(why)
        return 0
    return 0


def self_test() -> int:
    assert _bash_allowed("git status")[0]
    assert _bash_allowed("git diff --stat")[0]
    assert _bash_allowed("gh issue view 12 --json title,body")[0]
    assert _bash_allowed('python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_state.py" show --run-dir .gearbox/runs/x')[0]
    assert not _bash_allowed("npm test")[0]
    assert not _bash_allowed("git add .")[0]
    assert not _bash_allowed("git status && echo hacked > app.py")[0]
    assert not _bash_allowed("sed -i s/a/b/ app.py")[0]
    print("orchestrator-guard: PASS")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: orchestrator_guard.py activate|check|deactivate|self-test", file=sys.stderr)
        return 2
    action = sys.argv[1]
    if action == "self-test":
        return self_test()
    event = _event()
    if action == "activate":
        return activate(event)
    if action in {"deactivate", "reset"}:
        return deactivate(event)
    if action == "check":
        return check(event)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
