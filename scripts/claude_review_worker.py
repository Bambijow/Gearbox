#!/usr/bin/env python3
"""Read-only Claude Code review/research worker for Gemini-orchestrated Gearbox."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "references/codex-review-result.schema.json"
REQUIRED = {"status", "summary", "findings", "verification_gaps", "residual_risks"}


def fail(reason):
    print("claude-review-worker: " + reason, file=sys.stderr)
    raise SystemExit(7)


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if result.returncode:
        fail("git failure: " + result.stderr.strip())
    return result.stdout.strip()


def build_command(binary, prompt, model, schema):
    if not model:
        fail("Explicit Claude model required")
    return [binary, "-p", prompt, "--model", model,
            "--no-session-persistence", "--output-format", "json",
            "--permission-mode", "plan", "--tools", "Read,Glob,Grep",
            "--max-turns", "8", "--json-schema", schema.read_text(encoding="utf-8")]


def parse(raw):
    try:
        envelope = json.loads(raw)
    except ValueError:
        fail("Claude did not return a JSON envelope")
    if not isinstance(envelope, dict) or envelope.get("is_error") is True:
        fail("Claude returned an error")
    data = envelope.get("structured_output")
    if not isinstance(data, dict) or not REQUIRED <= data.keys():
        fail("Missing structured review fields")
    return envelope, data


def self_test():
    command = build_command("claude", "Review code", "sonnet", SCHEMA)
    assert "--permission-mode" in command and "plan" in command
    assert "--no-session-persistence" in command and "--tools" in command
    payload = {k: [] for k in REQUIRED}
    assert parse(json.dumps({"structured_output": payload}))[1] == payload
    try:
        parse('{"is_error":true}')
    except SystemExit:
        pass
    else:
        raise AssertionError("Accepted Claude error")
    print("PASS: read-only Claude reviewer self-test")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worktree", type=Path)
    p.add_argument("--prompt", type=Path)
    p.add_argument("--result", type=Path)
    p.add_argument("--meta", type=Path)
    p.add_argument("--model", default="sonnet")
    p.add_argument("--claude-bin", default="claude")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    if not (args.worktree and args.prompt and args.result):
        p.error("--worktree, --prompt and --result are required")
    repo = args.worktree.resolve()
    if not repo.is_dir() or not args.prompt.is_file():
        fail("Worktree or prompt missing")
    if not shutil.which(args.claude_bin):
        fail("Claude Code executable missing")
    base = git(repo, "rev-parse", "HEAD")
    if git(repo, "status", "--porcelain"):
        fail("Review worktree must start clean")
    prompt = args.prompt.read_text(encoding="utf-8")
    started = time.time()
    proc = subprocess.run(build_command(args.claude_bin, prompt, args.model, SCHEMA),
                          cwd=repo, capture_output=True, text=True)
    if proc.returncode:
        fail("Claude failed: " + proc.stderr[-800:])
    envelope, data = parse(proc.stdout)
    if git(repo, "rev-parse", "HEAD") != base or git(repo, "status", "--porcelain"):
        fail("Read-only Claude review changed worktree")
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    meta = args.meta or args.result.with_suffix(".meta.json")
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps({
        "provider":"claude", "model":args.model, "isolation":"fresh-print-plan-readonly",
        "base_sha":base, "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),
        "duration_seconds":round(time.time()-started, 3),
        "total_cost_usd":envelope.get("total_cost_usd"),
        "usage":envelope.get("usage", {}),
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
