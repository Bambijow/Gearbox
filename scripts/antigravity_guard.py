#!/usr/bin/env python3
"""Antigravity PreToolUse adapter; Claude hook protocol is different."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shlex
import sys
import tempfile
from pathlib import Path

FRONT = {"issue", "loop", "flow", "resume", "continue-pr", "autopilot", "reverse"}
MUTATIONS = {"write_to_file", "replace_file_content", "multi_replace_file_content"}
READ = {"pwd", "ls", "rg", "grep", "head", "tail", "cat", "wc", "stat", "realpath"}
SCRIPTS = {"run_state.py", "route_task.py", "gemini_worker.py", "gemini_claude_router.py", "worktree_manager.py", "issue_preflight.py", "evidence.py", "child_jobs.py", "usage_ledger.py"}


def marker(event):
    roots = event.get("workspacePaths") or []
    sid = event.get("conversationId")
    if not isinstance(roots, list) or not roots or not isinstance(roots[0], str) or not isinstance(sid, str) or not sid:
        return None
    digest = hashlib.sha256((str(Path(roots[0]).resolve()) + "\n" + sid).encode()).hexdigest()
    return Path(tempfile.gettempdir()) / "gearbox-antigravity" / (digest + ".json")


def front_door(event):
    prompt = event.get("lastUserInput", "")
    if not isinstance(prompt, str):
        return None
    match = re.match(r"^\s*/(?:gearbox[:./-])?([a-z][a-z-]+)\b", prompt)
    return match.group(1) if match else None


def shell_allowed(command):
    if not isinstance(command, str) or not command.strip():
        return False
    if any(c in command for c in ("\n", "\r", ";", "|", "<", ">", chr(96))) or "&&" in command or "$(" in command:
        return False
    try:
        argv = shlex.split(command)
    except ValueError:
        return False
    if not argv:
        return False
    exe = Path(argv[0]).name
    if exe in READ:
        return True
    if exe == "git":
        offset = 3 if len(argv) > 3 and argv[1] == "-C" else 1
        return len(argv) > offset and argv[offset] in {"status", "diff", "show", "log", "rev-parse", "ls-files", "merge-base", "cat-file", "diff-tree", "check-ignore"}
    if exe in {"python", "python3"} and len(argv) > 1:
        return "/scripts/" in argv[1].replace("\\", "/") and Path(argv[1]).name in SCRIPTS
    return False


def evaluate(event, active):
    if not active:
        return {"decision": "allow", "reason": "No active Gearbox guarded run"}
    call = event.get("toolCall") or {}
    name = call.get("name")
    args = call.get("args") or {}
    if name in MUTATIONS:
        return {"decision": "deny", "reason": "Delegate product edits to a worker"}
    if name == "run_command" and (not isinstance(args, dict) or not shell_allowed(args.get("CommandLine", ""))):
        return {"decision": "deny", "reason": "Orchestrator shell command is not approved"}
    return {"decision": "allow", "reason": "Allowed by Gearbox"}


def run(mode, event):
    path = marker(event)
    if mode == "activate":
        if path and front_door(event) in FRONT:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"command": front_door(event)}), encoding="utf-8")
        return {}
    if mode == "deactivate":
        if path:
            path.unlink(missing_ok=True)
        return {}
    if mode == "check":
        return evaluate(event, bool(path and path.exists()))
    raise ValueError("invalid mode")


def self_test():
    event = {"conversationId": "s", "workspacePaths": ["/tmp/project"], "lastUserInput": "/gearbox:issue 7"}
    assert front_door(event) == "issue"
    assert shell_allowed("git status")
    assert shell_allowed("python3 /plugin/scripts/gemini_worker.py --self-test")
    for command in ("git add .", "rm -rf .", "python3 foo.py", "git status && touch a"):
        assert not shell_allowed(command)
    event["toolCall"] = {"name": "write_to_file", "args": {"TargetFile": "src/x"}}
    assert evaluate(event, True)["decision"] == "deny"
    assert evaluate(event, False)["decision"] == "allow"
    event["toolCall"] = {"name": "run_command", "args": {"CommandLine": "rm -rf src"}}
    assert evaluate(event, True)["decision"] == "deny"
    print("PASS: antigravity guard self-test")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["activate", "check", "deactivate", "self-test"])
    mode = p.parse_args().mode
    if mode == "self-test":
        self_test()
        return
    try:
        event = json.load(sys.stdin)
        output = run(mode, event if isinstance(event, dict) else {})
    except (ValueError, OSError, json.JSONDecodeError):
        output = {"decision": "deny", "reason": "Malformed hook input"} if mode == "check" else {}
    print(json.dumps(output))

if __name__ == "__main__":
    main()
