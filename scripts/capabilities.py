#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BLOCKING_AUTH_MARKERS = (
    "not_authenticated",
    "unauthenticated",
    "expired",
    "invalid",
    "failed",
    "error",
)


def die(message: str, code: int = 2) -> None:
    print("capabilities:", message, file=sys.stderr)
    raise SystemExit(code)


def sanitize_entry(raw: dict) -> dict:
    transport = raw.get("transport")
    transport_type = transport.get("type") if isinstance(transport, dict) else None
    return {
        "name": str(raw.get("name", "")),
        "enabled": bool(raw.get("enabled", False)),
        "disabled_reason": raw.get("disabled_reason"),
        "auth_status": raw.get("auth_status"),
        "transport_type": transport_type,
    }


def sanitize_inventory(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        die("codex mcp list --json did not return a JSON list")
    entries = []
    for item in raw:
        if isinstance(item, dict) and item.get("name"):
            entries.append(sanitize_entry(item))
    return sorted(entries, key=lambda item: item["name"].casefold())


def auth_blocked(status: object) -> bool:
    if status is None:
        return False
    value = str(status).strip().lower().replace("-", "_").replace(" ", "_")
    if value in {"", "unsupported", "authenticated", "ok", "none"}:
        return False
    return any(marker in value for marker in BLOCKING_AUTH_MARKERS)


def usable(entry: dict) -> bool:
    return bool(entry.get("enabled")) and not auth_blocked(entry.get("auth_status"))


def usable_names(entries: list[dict]) -> list[str]:
    return sorted({str(item["name"]) for item in entries if usable(item)}, key=str.casefold)


def run_codex_mcp_inventory(codex_bin: str = "codex", cwd: Path | None = None) -> list[dict]:
    proc = subprocess.run(
        [codex_bin, "mcp", "list", "--json"],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        die(f"codex mcp list --json failed ({proc.returncode}): {proc.stderr[-800:]}", 7)
    try:
        raw = json.loads(proc.stdout)
    except Exception as exc:
        die(f"invalid JSON from codex mcp list --json: {exc}", 7)
    return sanitize_inventory(raw)


def canonical_required(values: list[str] | None) -> list[str]:
    out = []
    seen = set()
    for raw in values or []:
        value = str(raw).strip()
        if not value:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return sorted(out, key=str.casefold)


def preflight(entries: list[dict], required: list[str]) -> dict:
    required = canonical_required(required)
    by_key = {item["name"].casefold(): item for item in entries}
    missing = []
    disabled = []
    auth = []
    resolved = []
    for requested in required:
        item = by_key.get(requested.casefold())
        if item is None:
            missing.append(requested)
            continue
        resolved.append(item["name"])
        if not item.get("enabled"):
            disabled.append(item["name"])
        elif auth_blocked(item.get("auth_status")):
            auth.append({"name": item["name"], "auth_status": item.get("auth_status")})
    ok = not missing and not disabled and not auth
    return {
        "ok": ok,
        "required": required,
        "resolved": sorted(set(resolved), key=str.casefold),
        "missing": missing,
        "disabled": disabled,
        "auth_blocked": auth,
        "available": usable_names(entries),
    }


def toml_key_segment(name: str) -> str:
    return json.dumps(str(name), ensure_ascii=False)


def prune_overrides(entries: list[dict], required: list[str]) -> tuple[list[str], list[str]]:
    required_keys = {value.casefold() for value in canonical_required(required)}
    disabled_names = []
    overrides = []
    for item in entries:
        name = item["name"]
        if item.get("enabled") and name.casefold() not in required_keys:
            disabled_names.append(name)
            overrides.append(f"mcp_servers.{toml_key_segment(name)}.enabled=false")
    return sorted(disabled_names, key=str.casefold), overrides


def provider_gate(
    required: list[str],
    claude_capabilities: list[str],
    codex_capabilities: list[str],
    prefer: str | None = None,
) -> dict:
    req = {value.casefold(): value for value in canonical_required(required)}
    claude = {str(value).casefold() for value in claude_capabilities}
    codex = {str(value).casefold() for value in codex_capabilities}
    missing = {
        "claude": sorted([original for key, original in req.items() if key not in claude], key=str.casefold),
        "codex": sorted([original for key, original in req.items() if key not in codex], key=str.casefold),
    }
    eligible = [provider for provider in ("claude", "codex") if not missing[provider]]
    selected = None
    if len(eligible) == 1:
        selected = eligible[0]
    elif len(eligible) == 2 and prefer in eligible:
        selected = prefer
    return {
        "required": canonical_required(required),
        "eligible": eligible,
        "selected": selected,
        "blocked": not eligible,
        "missing": missing,
    }


def self_test() -> None:
    raw = [
        {
            "name": "godot",
            "enabled": True,
            "disabled_reason": None,
            "transport": {"type": "stdio", "command": "godot-mcp", "env": {"TOKEN": "secret"}},
            "auth_status": "unsupported",
        },
        {
            "name": "cloud",
            "enabled": True,
            "disabled_reason": None,
            "transport": {"type": "streamable_http", "url": "https://secret.example"},
            "auth_status": "not_authenticated",
        },
        {
            "name": "blender.prod",
            "enabled": False,
            "disabled_reason": "config",
            "transport": {"type": "stdio", "command": "blender"},
            "auth_status": "unsupported",
        },
    ]
    inv = sanitize_inventory(raw)
    assert inv[0]["name"] == "blender.prod"
    assert "transport" not in inv[0]
    assert usable_names(inv) == ["godot"]
    ok = preflight(inv, ["godot"])
    assert ok["ok"] is True and ok["resolved"] == ["godot"]
    blocked = preflight(inv, ["cloud", "missing"])
    assert blocked["ok"] is False and blocked["missing"] == ["missing"]
    disabled_names, overrides = prune_overrides(inv, [])
    assert disabled_names == ["cloud", "godot"]
    assert 'mcp_servers."godot".enabled=false' in overrides
    assert toml_key_segment('a"b') == '"a\\\"b"'
    gate = provider_gate(["godot"], ["browser"], ["godot", "browser"])
    assert gate["selected"] == "codex" and gate["blocked"] is False
    both = provider_gate([], [], [], prefer="claude")
    assert both["eligible"] == ["claude", "codex"] and both["selected"] == "claude"
    print("PASS: capability routing self-test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory and gate Gearbox execution capabilities without persisting secrets.")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    inv = sub.add_parser("inventory")
    inv.add_argument("--codex-bin", default="codex")
    inv.add_argument("--cwd", type=Path)
    inv.add_argument("--write", type=Path)

    check = sub.add_parser("check")
    check.add_argument("--codex-bin", default="codex")
    check.add_argument("--cwd", type=Path)
    check.add_argument("--required-capability", action="append", default=[])
    check.add_argument("--prune-plan", action="store_true")

    route = sub.add_parser("route")
    route.add_argument("--required-capability", action="append", default=[])
    route.add_argument("--claude-capability", action="append", default=[])
    route.add_argument("--codex-capability", action="append", default=[])
    route.add_argument("--prefer", choices=("claude", "codex"))

    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.cmd:
        ap.error("command required")

    if args.cmd == "route":
        payload = provider_gate(
            args.required_capability,
            args.claude_capability,
            args.codex_capability,
            args.prefer,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if not payload["blocked"] else 7

    entries = run_codex_mcp_inventory(args.codex_bin, args.cwd.resolve() if args.cwd else None)
    if args.cmd == "inventory":
        payload = {
            "schema_version": 1,
            "provider": "codex",
            "capabilities": entries,
            "available": usable_names(entries),
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if args.write:
            args.write.parent.mkdir(parents=True, exist_ok=True)
            args.write.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0

    payload = preflight(entries, args.required_capability)
    if args.prune_plan:
        disabled, overrides = prune_overrides(entries, payload["resolved"])
        payload["prune"] = {"disabled": disabled, "config_overrides": overrides}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 7


if __name__ == "__main__":
    raise SystemExit(main())
