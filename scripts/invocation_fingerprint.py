#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_payload(
    *,
    base_sha: str,
    prompt_sha256: str,
    provider: str,
    model: str,
    effort: str,
    kind: str,
    capabilities: list[str] | None = None,
    provider_version: str | None = None,
    environment: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "base_sha": str(base_sha),
        "prompt_sha256": str(prompt_sha256),
        "provider": str(provider),
        "model": str(model),
        "effort": str(effort),
        "kind": str(kind),
        "capabilities": sorted({str(x) for x in (capabilities or [])}, key=str.casefold),
        "provider_version": provider_version,
        "environment": environment or {},
    }


def fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(encoded)


def self_test() -> None:
    a = canonical_payload(
        base_sha="abc",
        prompt_sha256="def",
        provider="codex",
        model="sol",
        effort="medium",
        kind="implementation",
        capabilities=["godot", "blender"],
        environment={"memory": "off"},
    )
    b = canonical_payload(
        base_sha="abc",
        prompt_sha256="def",
        provider="codex",
        model="sol",
        effort="medium",
        kind="implementation",
        capabilities=["blender", "godot"],
        environment={"memory": "off"},
    )
    assert fingerprint(a) == fingerprint(b)
    b["effort"] = "high"
    assert fingerprint(a) != fingerprint(b)
    print("PASS: invocation-fingerprint self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a stable Gearbox dispatch fingerprint for deduplication.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--base-sha")
    ap.add_argument("--prompt", type=Path)
    ap.add_argument("--provider")
    ap.add_argument("--model", default="default")
    ap.add_argument("--effort", default="default")
    ap.add_argument("--kind", default="implementation")
    ap.add_argument("--capability", action="append", default=[])
    ap.add_argument("--provider-version")
    ap.add_argument("--environment-json")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    for field in ("base_sha", "prompt", "provider"):
        if getattr(args, field) in (None, ""):
            ap.error(f"--{field.replace('_', '-')} is required")
    env = json.loads(args.environment_json) if args.environment_json else {}
    payload = canonical_payload(
        base_sha=args.base_sha,
        prompt_sha256=sha256_file(args.prompt),
        provider=args.provider,
        model=args.model,
        effort=args.effort,
        kind=args.kind,
        capabilities=args.capability,
        provider_version=args.provider_version,
        environment=env,
    )
    fp = fingerprint(payload)
    if args.json:
        print(json.dumps({"fingerprint": fp, "payload": payload}, indent=2, ensure_ascii=False))
    else:
        print(fp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
