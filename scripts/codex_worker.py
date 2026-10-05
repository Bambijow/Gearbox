#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

# Gearbox intentionally keeps the user's Codex config loaded so workers can use
# configured MCP servers and other capabilities. Only cross-run cognitive memory
# is disabled for every worker.
MEMORY_OVERRIDES = (
    "features.memories=false",
    "memories.use_memories=false",
    "memories.generate_memories=false",
    "memories.dedicated_tools=false",
)


def die(message: str, code: int = 2) -> None:
    print("codex-worker:", message, file=sys.stderr)
    raise SystemExit(code)


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
    if ignore_user_config:
        cmd.append("--ignore-user-config")
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--config", f'model_reasoning_effort="{effort}"']
    cmd.append("-")
    return cmd


def self_test() -> None:
    cmd = build_command(
        codex_bin="codex",
        worktree=Path("/tmp/worktree"),
        schema=Path("/tmp/schema.json"),
        result=Path("/tmp/result.json"),
        sandbox="workspace-write",
        model="test-model",
        effort="high",
    )
    assert "--ephemeral" in cmd
    assert "--ignore-user-config" not in cmd
    for override in MEMORY_OVERRIDES:
        assert override in cmd
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
    print("PASS: codex-worker memory isolation self-test")


def main() -> int:
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        return 0

    parser = argparse.ArgumentParser(
        description="Run one isolated stateless Codex worker while preserving configured capabilities/MCPs."
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
    parser.add_argument(
        "--ignore-user-config",
        action="store_true",
        help="Explicit hard-isolation escape hatch. Not the default because it also removes configured MCP capabilities.",
    )
    args = parser.parse_args()

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

    cmd = build_command(
        codex_bin=args.codex_bin,
        worktree=worktree,
        schema=schema,
        result=result,
        sandbox=sandbox,
        ignore_user_config=args.ignore_user_config,
        model=args.model,
        effort=args.effort,
    )

    metadata = {
        "kind": args.kind,
        "requested_model": args.model or "default",
        "requested_effort": args.effort or "default",
        "sandbox": sandbox,
        "started_at": int(time.time()),
        "effective_effort_verified": False,
        "codex_user_config_loaded": not args.ignore_user_config,
        "configured_capabilities_preserved": not args.ignore_user_config,
        "memory_policy": {
            "ephemeral_session": True,
            "feature_enabled": False,
            "use_memories": False,
            "generate_memories": False,
            "dedicated_tools": False,
        },
    }
    meta.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    with events.open("w", encoding="utf-8") as event_file:
        proc = subprocess.run(
            cmd,
            input=prompt.read_text(encoding="utf-8"),
            text=True,
            stdout=event_file,
            stderr=subprocess.PIPE,
            cwd=worktree,
            check=False,
        )

    metadata["finished_at"] = int(time.time())
    metadata["exit_code"] = proc.returncode
    meta.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        die(f"Codex exited with status {proc.returncode}", proc.returncode)
    if not result.is_file():
        die(f"Codex completed without writing result: {result}")

    try:
        payload = json.loads(result.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"result is not valid JSON: {exc}")

    missing = sorted(REQUIRED[args.kind].difference(payload))
    if missing:
        die(f"{args.kind} result missing required keys: {', '.join(missing)}")

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
