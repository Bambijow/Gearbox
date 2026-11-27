#!/usr/bin/env python3
"""Execute one Antigravity headless worker in a dedicated, clean Git worktree."""
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
SCHEMAS = {
    "implementation": ROOT / "references/codex-implementation-result.schema.json",
    "review": ROOT / "references/codex-review-result.schema.json",
}
REQUIRED = {
    "implementation": {"status", "summary", "integration_base_sha", "head_sha",
                       "changed_files", "verification", "risks", "notes"},
    "review": {"status", "summary", "findings", "verification_gaps", "residual_risks"},
}


def fail(message):
    print("gemini-worker: " + message, file=sys.stderr)
    raise SystemExit(7)


def git(repo, *args):
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True)
    if proc.returncode:
        fail("git failed: " + proc.stderr.strip())
    return proc.stdout.strip()


def command(bin_name, prompt, model, schema, mode):
    if not model or not model.strip():
        fail("Explicit model ID required (verify with agy models)")
    return [bin_name, "-p", prompt, "--model", model, "--mode", mode,
            "--output-format", "json", "--json-schema", str(schema)]


def parse_response(raw, kind):
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        fail("Antigravity did not return JSON")
    if not isinstance(envelope, dict) or envelope.get("status") != "SUCCESS":
        fail("Antigravity returned unsuccessful result")
    payload = envelope.get("structured_output")
    if not isinstance(payload, dict) or not REQUIRED[kind] <= payload.keys():
        fail("Missing structured result fields")
    return envelope, payload


def changed_paths(repo, base):
    names = set(git(repo, "diff", "--name-only", base, "HEAD").splitlines())
    porcelain = git(repo, "status", "--porcelain", "--untracked-files=all")
    names.update(line[3:].split(" -> ")[-1] for line in porcelain.splitlines())
    return sorted(p for p in names if p)


def outside_ownership(paths, owned):
    return [p for p in paths if not any(
        p == root.rstrip("/") or p.startswith(root.rstrip("/") + "/") for root in owned)]


def self_test():
    c = command("agy", "test", "gemini-4-neon-medium", Path("/tmp/schema.json"), "auto")
    assert c[:3] == ["agy", "-p", "test"] and "--json-schema" in c
    payload = {k: [] for k in REQUIRED["review"]}
    assert parse_response(json.dumps({"status":"SUCCESS","structured_output":payload}), "review")[1] == payload
    try:
        parse_response(json.dumps({"status":"ERROR"}), "review")
    except SystemExit:
        pass
    else:
        raise AssertionError("Accepted failed execution")
    assert outside_ownership(["src/a.py", "docs/readme.md"], ["src"]) == ["docs/readme.md"]
    print("PASS: gemini-worker self-test")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", type=Path)
    ap.add_argument("--prompt", type=Path)
    ap.add_argument("--result", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--kind", choices=tuple(REQUIRED), default="implementation")
    ap.add_argument("--model")
    ap.add_argument("--agy-bin", default="agy")
    ap.add_argument("--owned-path", action="append", default=[])
    ap.add_argument("--required-capability", action="append", default=[])
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not all([args.worktree, args.prompt, args.result, args.model]):
        ap.error("worktree, prompt, result and model are required")
    repo = args.worktree.resolve()
    if not repo.is_dir() or not args.prompt.is_file():
        fail("Missing worktree/prompt")
    if not shutil.which(args.agy_bin):
        fail("Antigravity CLI missing or not authenticated")
    if args.kind == "implementation" and not args.owned_path:
        fail("Explicit owned paths required")
    if args.required_capability:
        fail("MCP capability preflight not yet implemented for Antigravity workers")
    base = git(repo, "rev-parse", "HEAD")
    if git(repo, "status", "--porcelain"):
        fail("Worker worktree must be clean before execution")
    schema = SCHEMAS[args.kind]
    prompt = args.prompt.read_text(encoding="utf-8")
    mode = "plan" if args.kind == "review" else "auto"
    cmd = command(args.agy_bin, prompt, args.model, schema, mode)
    started = time.time()
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    if proc.returncode:
        fail("Antigravity exited " + str(proc.returncode) + ": " + proc.stderr[-800:])
    envelope, payload = parse_response(proc.stdout, args.kind)
    paths = changed_paths(repo, base)
    if args.kind == "review" and paths:
        fail("Review attempted to mutate the worktree")
    violating = outside_ownership(paths, args.owned_path) if args.kind == "implementation" else []
    if violating:
        fail("Ownership violations: " + ", ".join(violating))
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    metadata = args.meta or args.result.with_suffix(".meta.json")
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps({
        "provider":"gemini", "model":args.model, "mode":mode, "base_sha":base,
        "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),
        "result_sha256":hashlib.sha256(args.result.read_bytes()).hexdigest(),
        "usage":envelope.get("usage", {}), "duration_seconds":round(time.time()-started, 3),
        "changed_paths":paths, "review_isolation":"plan-mode-plus-clean-tree-gate" if args.kind == "review" else "not-applicable",
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
