#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from capabilities import preflight, prune_overrides, run_codex_mcp_inventory, usable_names
from invocation_fingerprint import canonical_payload, fingerprint, sha256_file
import usage_ledger

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "implementation": ROOT / "references/codex-implementation-result.schema.json",
    "review": ROOT / "references/codex-review-result.schema.json",
}
REQUIRED = {
    "implementation": {
        "status",
        "summary",
        "integration_base_sha",
        "head_sha",
        "changed_files",
        "verification",
        "risks",
        "notes",
    },
    "review": {
        "status",
        "summary",
        "findings",
        "verification_gaps",
        "residual_risks",
    },
}

MEMORY_OVERRIDES = (
    "features.memories=false",
    "memories.use_memories=false",
    "memories.generate_memories=false",
    "memories.dedicated_tools=false",
)


def die(message: str, code: int = 2) -> None:
    print("codex-worker:", message, file=sys.stderr)
    raise SystemExit(code)


def command_output(argv: list[str], cwd: Path | None = None) -> str | None:
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def codex_version(codex_bin: str) -> str | None:
    return command_output([codex_bin, "--version"])


def git_head(worktree: Path) -> str | None:
    return command_output(["git", "rev-parse", "HEAD"], worktree)


# The Codex sandbox keeps a linked worktree's gitdir read-only even with --add-dir, so the wrapper commits.
NO_COMMIT_NOTE = "\n\nDo not run git add/commit: the sandbox cannot write git metadata. Leave changes in the worktree; the wrapper commits them after you finish.\n"


def commit_worktree(worktree: Path, message: str) -> str | None:
    if not command_output(["git", "status", "--porcelain"], worktree):
        return None
    for argv in (["git", "add", "-A"], ["git", "commit", "-q", "-m", message]):
        if subprocess.run(argv, cwd=worktree, check=False).returncode:
            return None
    return git_head(worktree)


def run_dir_for(result: Path) -> Path | None:
    for parent in result.parents:
        if parent.parent.name == "runs" and parent.parent.parent.name == ".gearbox":
            return parent
    return None


def reported_usage(events: Path) -> dict:
    usage: dict = {}
    for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "turn.completed":
            for k, v in (event.get("usage") or {}).items():
                if isinstance(v, int):
                    usage[k] = usage.get(k, 0) + v
    return usage


def changed_paths(worktree: Path, base_sha: str) -> list[str]:
    committed = command_output(["git", "diff", "--name-only", base_sha, "HEAD"], worktree) or ""
    status = command_output(["git", "status", "--porcelain", "--untracked-files=all"], worktree) or ""
    paths = set(committed.splitlines()) | {line[3:].split(" -> ")[-1] for line in status.splitlines()}
    return sorted(p for p in paths if p)


def outside_ownership(paths: list[str], owned: list[str]) -> list[str]:
    def inside(path: str, root: str) -> bool:
        root = root.rstrip("/")
        return path == root or path.startswith(root + "/")
    return [p for p in paths if not any(inside(p, o) for o in owned)]


def stable_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_command(
    *,
    codex_bin: str,
    worktree: Path,
    schema: Path,
    result: Path,
    sandbox: str,
    ignore_user_config: bool = False,
    model: str | None = None,
    effort: str | None = None,
    mcp_config_overrides: list[str] | None = None,
) -> list[str]:
    cmd = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--json",
        "--sandbox",
        sandbox,
        "-C",
        str(worktree),
        "--output-schema",
        str(schema),
        "--output-last-message",
        str(result),
    ]
    for override in MEMORY_OVERRIDES:
        cmd += ["--config", override]
    for override in mcp_config_overrides or []:
        cmd += ["--config", override]
    if ignore_user_config:
        cmd.append("--ignore-user-config")
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--config", f'model_reasoning_effort="{effort}"']
    cmd.append("-")
    return cmd


def validate_result(path: Path, kind: str) -> dict:
    if not path.is_file():
        die(f"Codex completed without writing result: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"result is not valid JSON: {exc}")
    missing = sorted(REQUIRED[kind].difference(payload))
    if missing:
        die(f"{kind} result missing required keys: {', '.join(missing)}")
    return payload


def self_test() -> None:
    cmd = build_command(
        codex_bin="codex",
        worktree=Path("/tmp/worktree"),
        schema=Path("/tmp/schema.json"),
        result=Path("/tmp/result.json"),
        sandbox="workspace-write",
        model="test-model",
        effort="high",
        mcp_config_overrides=[
            'mcp_servers.blender.enabled=false',
            'mcp_servers.context7.enabled=false',
        ],
    )
    assert "--ephemeral" in cmd
    assert "--ignore-user-config" not in cmd
    for override in MEMORY_OVERRIDES:
        assert override in cmd
    assert 'mcp_servers.blender.enabled=false' in cmd
    assert 'model_reasoning_effort="high"' in cmd

    isolated = build_command(
        codex_bin="codex",
        worktree=Path("/tmp/worktree"),
        schema=Path("/tmp/schema.json"),
        result=Path("/tmp/result.json"),
        sandbox="read-only",
        ignore_user_config=True,
    )
    assert "--ignore-user-config" in isolated
    assert "--ignore-user-config" not in cmd

    assert run_dir_for(Path("/r/.gearbox/runs/issue-8/tasks/T1/result.json")) == Path("/r/.gearbox/runs/issue-8")
    assert run_dir_for(Path("/tmp/result.json")) is None
    assert outside_ownership(
        ["engine/formats/src/env.rs", "engine/formats/src/envx.rs", "docs/port/CONVENTIONS.md"],
        ["engine/formats/src/env.rs", "engine/render/"],
    ) == ["engine/formats/src/envx.rs", "docs/port/CONVENTIONS.md"]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        ev = Path(td) / "events.jsonl"
        ev.write_text('{"type":"turn.started"}\nnot json\n{"type":"turn.completed","usage":{"input_tokens":7,"output_tokens":2}}\n', encoding="utf-8")
        assert reported_usage(ev) == {"input_tokens": 7, "output_tokens": 2}
        os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        repo = Path(td) / "repo"
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "--allow-empty", "-m", "init"], check=True)
        assert commit_worktree(repo, "noop") is None
        (repo / "a.txt").write_text("hi", encoding="utf-8")
        before = git_head(repo)
        head = commit_worktree(repo, "add a")
        assert head and head != before and changed_paths(repo, before) == ["a.txt"]

    dispatch = canonical_payload(
        base_sha="abc",
        prompt_sha256="p",
        provider="codex",
        model="sol",
        effort="medium",
        kind="implementation",
        capabilities=["godot"],
        environment={"sandbox": "workspace-write", "mcp_policy": "required-only"},
    )
    assert len(fingerprint(dispatch)) == 64
    assert len(stable_hash({"codex_version": "x", "active_mcp": ["godot"]})) == 64
    print("PASS: codex-worker isolation/capability self-test")


def main() -> int:
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        return 0

    parser = argparse.ArgumentParser(
        description="Run one stateless Codex worker with capability preflight and minimal MCP exposure."
    )
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--prompt", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--events", type=Path)
    parser.add_argument("--meta", type=Path)
    parser.add_argument("--kind", choices=("implementation", "review"), default="implementation")
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--sandbox", choices=("workspace-write", "read-only"))
    parser.add_argument("--model")
    parser.add_argument(
        "--effort",
        choices=("none", "minimal", "low", "medium", "high", "xhigh", "max"),
    )
    parser.add_argument("--required-capability", action="append", default=[])
    parser.add_argument(
        "--prune-mcp",
        action="store_true",
        help="Expose only required MCP servers for this worker. With no required capabilities, disable all configured MCP servers for this invocation.",
    )
    parser.add_argument(
        "--ignore-user-config",
        action="store_true",
        help="Explicit hard-isolation escape hatch. Not the default because it removes configured MCP capabilities.",
    )
    parser.add_argument("--allow-review-user-config", action="store_true", help="Explicit exception for reviews needing user-configured tools; independent isolation is not claimed.")
    parser.add_argument("--run-dir", type=Path, help="Gearbox run directory for budget/usage accounting; inferred from --result under .gearbox/runs/<run>/ when omitted.")
    parser.add_argument("--commit-message", help="Commit message for the wrapper's post-run commit of the worker's changes.")
    parser.add_argument("--owned-path", action="append", default=[], help="Task owns/touches path or directory prefix; changes outside them are reported in meta as ownership_violations.")
    args = parser.parse_args()
    if args.kind == "review" and args.required_capability and not args.allow_review_user_config:
        die("review requires user-configured capabilities; explicitly authorize --allow-review-user-config or use an isolated review", 7)
    effective_ignore_user_config = args.ignore_user_config or (args.kind == "review" and not args.allow_review_user_config)
    if effective_ignore_user_config and args.required_capability:
        die("isolated config cannot guarantee configured capabilities", 7)

    worktree = args.worktree.resolve()
    prompt = args.prompt.resolve()
    result = args.result.resolve()
    schema = (args.schema or SCHEMAS[args.kind]).resolve()
    events = (args.events or result.with_suffix(".events.jsonl")).resolve()
    meta = (args.meta or result.with_suffix(".meta.json")).resolve()
    sandbox = args.sandbox or ("read-only" if args.kind == "review" else "workspace-write")

    if not worktree.is_dir():
        die(f"worktree does not exist: {worktree}")
    if not prompt.is_file():
        die(f"prompt file does not exist: {prompt}")
    if not schema.is_file():
        die(f"schema file does not exist: {schema}")
    if shutil.which(args.codex_bin) is None:
        die(f"Codex CLI not found on PATH: {args.codex_bin}")

    result.parent.mkdir(parents=True, exist_ok=True)
    events.parent.mkdir(parents=True, exist_ok=True)
    meta.parent.mkdir(parents=True, exist_ok=True)

    version = codex_version(args.codex_bin)
    base_sha = git_head(worktree)
    if not base_sha:
        die("unable to resolve worker base SHA")

    inventory: list[dict] = []
    capability_check = {
        "ok": True,
        "required": sorted(set(args.required_capability), key=str.casefold),
        "resolved": [],
        "missing": [],
        "disabled": [],
        "auth_blocked": [],
        "available": [],
    }
    disabled_mcp: list[str] = []
    mcp_overrides: list[str] = []

    if args.required_capability or args.prune_mcp:
        inventory = run_codex_mcp_inventory(args.codex_bin, worktree)
        capability_check = preflight(inventory, args.required_capability)
        if capability_check["ok"] and args.prune_mcp:
            disabled_mcp, mcp_overrides = prune_overrides(
                inventory,
                capability_check["resolved"],
            )

    active_mcp = capability_check["resolved"] if args.prune_mcp else usable_names(inventory)
    mcp_policy = "required-only" if args.prune_mcp else "configured"
    memory_policy = {
        "ephemeral_session": True,
        "feature_enabled": False,
        "use_memories": False,
        "generate_memories": False,
        "dedicated_tools": False,
    }
    environment = {
        "review_plugin_isolation": "not-isolated-explicit-exception" if args.kind == "review" and args.allow_review_user_config else ("isolated-user-config" if args.kind == "review" else "not-applicable"),
        "sandbox": sandbox,
        "mcp_policy": mcp_policy,
        "memory_policy": memory_policy,
    }
    prompt_sha = sha256_file(prompt)
    dispatch_payload = canonical_payload(
        base_sha=base_sha,
        prompt_sha256=prompt_sha,
        provider="codex",
        model=args.model or "default",
        effort=args.effort or "default",
        kind=args.kind,
        capabilities=capability_check["resolved"] or args.required_capability,
        environment=environment,
    )
    dispatch_fingerprint = fingerprint(dispatch_payload)
    env_payload = {
        "codex_version": version,
        "active_mcp": sorted(active_mcp, key=str.casefold),
        "memory_policy": memory_policy,
        "sandbox": sandbox,
    }
    environment_fingerprint = stable_hash(env_payload)
    invocation_payload = dict(dispatch_payload)
    invocation_payload["provider_version"] = version
    invocation_payload["environment"] = {
        **environment,
        "active_mcp": sorted(active_mcp, key=str.casefold),
        "environment_fingerprint": environment_fingerprint,
    }
    invocation_fingerprint = fingerprint(invocation_payload)

    metadata = {
        "kind": args.kind,
        "requested_model": args.model or "default",
        "requested_effort": args.effort or "default",
        "sandbox": sandbox,
        "started_at": int(time.time()),
        "effective_effort_verified": False,
        "codex_version": version,
        "review_plugin_isolation": environment["review_plugin_isolation"],
        "base_sha": base_sha,
        "prompt_sha256": prompt_sha,
        "schema_sha256": sha256_file(schema),
        "codex_user_config_loaded": not effective_ignore_user_config,
        "configured_capabilities_preserved": not effective_ignore_user_config,
        "memory_policy": memory_policy,
        "capability_preflight": capability_check,
        "mcp_policy": mcp_policy,
        "mcp_inventory": inventory,
        "active_mcp": sorted(active_mcp, key=str.casefold),
        "disabled_mcp": disabled_mcp,
        "dispatch_fingerprint": dispatch_fingerprint,
        "environment_fingerprint": environment_fingerprint,
        "invocation_fingerprint": invocation_fingerprint,
    }

    if not capability_check["ok"]:
        metadata["status"] = "CAPABILITY_BLOCKED"
        metadata["finished_at"] = int(time.time())
        meta.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        die(
            "required Codex capabilities unavailable: "
            + json.dumps(
                {
                    "missing": capability_check["missing"],
                    "disabled": capability_check["disabled"],
                    "auth_blocked": capability_check["auth_blocked"],
                },
                ensure_ascii=False,
            ),
            7,
        )

    run_dir = args.run_dir.resolve() if args.run_dir else run_dir_for(result)
    if run_dir and (run_dir / "state.json").is_file():
        budget = "review" if args.kind == "review" else "codex"
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("run_state.py")), "consume", "--run-dir", str(run_dir), "--kind", budget],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode != 0:
            metadata["status"] = "BUDGET_BLOCKED"
            metadata["finished_at"] = int(time.time())
            meta.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            die(f"budget refused dispatch: {(proc.stderr or proc.stdout).strip()}", proc.returncode)

    meta.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cmd = build_command(
        codex_bin=args.codex_bin,
        worktree=worktree,
        schema=schema,
        result=result,
        sandbox=sandbox,
        ignore_user_config=effective_ignore_user_config,
        model=args.model,
        effort=args.effort,
        mcp_config_overrides=mcp_overrides,
    )

    with events.open("w", encoding="utf-8") as event_file:
        proc = subprocess.run(
            cmd,
            input=prompt.read_text(encoding="utf-8") + (NO_COMMIT_NOTE if args.kind == "implementation" else ""),
            text=True,
            stdout=event_file,
            stderr=subprocess.PIPE,
            cwd=worktree,
            check=False,
        )

    metadata["finished_at"] = int(time.time())
    metadata["exit_code"] = proc.returncode
    metadata["status"] = "COMPLETED" if proc.returncode == 0 else "FAILED"
    metadata["usage"] = reported_usage(events)
    if args.owned_path and args.kind == "implementation":
        metadata["ownership_violations"] = outside_ownership(changed_paths(worktree, base_sha), args.owned_path)
        if metadata["ownership_violations"]:
            print("codex-worker: changes outside ownership: " + ", ".join(metadata["ownership_violations"]), file=sys.stderr)
    meta.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if run_dir:
        ledger_path = run_dir / "usage.json"
        ledger = usage_ledger.load(ledger_path)
        item = {
            "dispatch_id": f"{result.relative_to(run_dir) if result.is_relative_to(run_dir) else result}@{metadata['started_at']}",
            "kind": args.kind,
            "provider": "codex",
            "model": args.model,
            "effort": args.effort,
            "outcome": "success" if proc.returncode == 0 else "failure",
            "recorded_at": int(time.time()),
            "estimated": False,
        }
        item.update({k: metadata["usage"][k] for k in ("input_tokens", "output_tokens", "cached_input_tokens") if k in metadata["usage"]})
        ledger["items"].append(item)
        usage_ledger.save(ledger_path, ledger)

    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        die(f"Codex exited with status {proc.returncode}", proc.returncode)

    payload = validate_result(result, args.kind)
    if args.kind == "implementation" and payload.get("status") != "failed":
        head = commit_worktree(worktree, args.commit_message or f"{result.parent.name}: Codex worker changes")
        if head:
            payload["head_sha"] = head
            result.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
