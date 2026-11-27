#!/usr/bin/env python3
"""Sanitized Gemini MCP configuration inventory and provider eligibility.

Antigravity does not expose Codex-style live JSON inventory. A configured
server is NOT proof that its tools are connected or authenticated.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

BLOCKING_AUTH_MARKERS = ("not_authenticated", "unauthenticated", "expired", "invalid", "failed", "error")


def die(message: str, code: int = 2) -> None:
    print("capabilities:", message, file=sys.stderr)
    raise SystemExit(code)


def sanitize_entry(raw: dict) -> dict:
    return {
        "name": str(raw.get("name", "")),
        "enabled": bool(raw.get("enabled", not raw.get("disabled", False))),
        "disabled_reason": raw.get("disabled_reason"),
        "auth_status": raw.get("auth_status"),
        "transport_type": raw.get("transport_type") or (
            "stdio" if raw.get("command") else "streamable_http" if raw.get("serverUrl") or raw.get("url") else None
        ),
    }


def sanitize_inventory(raw: object) -> list[dict]:
    if isinstance(raw, dict) and isinstance(raw.get("mcpServers"), dict):
        raw = [{"name": name, **cfg} for name, cfg in raw["mcpServers"].items() if isinstance(cfg, dict)]
    if not isinstance(raw, list):
        die("MCP inventory must be a list or an mcpServers mapping")
    return sorted((sanitize_entry(item) for item in raw if isinstance(item, dict) and item.get("name")), key=lambda x: x["name"].casefold())


def run_gemini_mcp_inventory(workspace: Path, home: Path | None = None) -> list[dict]:
    base = (home or Path.home()) / ".gemini" / "config" / "mcp_config.json"
    local = workspace.resolve() / ".agents" / "mcp_config.json"
    combined = {}
    for path in (base, local):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            die(f"invalid MCP config {path}: {exc}", 7)
        if not isinstance(data, dict) or not isinstance(data.get("mcpServers", {}), dict):
            die(f"invalid MCP config object: {path}", 7)
        for name, cfg in data.get("mcpServers", {}).items():
            if isinstance(cfg, dict):
                combined[name] = cfg
    return sanitize_inventory({"mcpServers": combined})


def canonical_required(values: list[str] | None) -> list[str]:
    return sorted({str(v).strip() for v in values or [] if str(v).strip()}, key=str.casefold)


def auth_blocked(status: object) -> bool:
    if status is None:
        return False
    v = str(status).lower().replace("-", "_").replace(" ", "_")
    if v in {"", "unsupported", "authenticated", "ok", "none"}:
        return False
    return any(marker in v for marker in BLOCKING_AUTH_MARKERS)


def usable(entry: dict) -> bool:
    return bool(entry.get("enabled")) and not auth_blocked(entry.get("auth_status"))


def usable_names(entries: list[dict]) -> list[str]:
    return sorted({str(x["name"]) for x in entries if usable(x)}, key=str.casefold)


def preflight(entries: list[dict], required: list[str]) -> dict:
    req = canonical_required(required)
    mapping = {x["name"].casefold(): x for x in entries}
    missing, disabled, auth, resolved = [], [], [], []
    for name in req:
        entry = mapping.get(name.casefold())
        if not entry:
            missing.append(name)
        elif not entry["enabled"]:
            disabled.append(entry["name"])
        elif auth_blocked(entry.get("auth_status")):
            auth.append(entry["name"])
        else:
            resolved.append(entry["name"])
    return {
        "ok": not (missing or disabled or auth),
        "required": req, "resolved": resolved, "missing": missing,
        "disabled": disabled, "auth_blocked": auth,
        "available": usable_names(entries), "verification": "configured-only",
        "live_verified": False,
    }


def provider_gate(required: list[str], claude_capabilities: list[str],
                  gemini_capabilities: list[str], prefer: str | None = None) -> dict:
    req = {x.casefold(): x for x in canonical_required(required)}
    available = {"claude": {x.casefold() for x in claude_capabilities},
                 "gemini": {x.casefold() for x in gemini_capabilities}}
    missing = {p: sorted(v for k, v in req.items() if k not in caps)
               for p, caps in available.items()}
    eligible = [p for p in ("claude", "gemini") if not missing[p]]
    selected = eligible[0] if len(eligible) == 1 else prefer if prefer in eligible else None
    return {"required": sorted(req.values()), "eligible": eligible,
            "selected": selected, "blocked": not eligible, "missing": missing}


def self_test():
    import tempfile
    raw = {"mcpServers": {"godot": {"command": "godot", "env": {"TOKEN": "secret"}},
                          "blender": {"command": "blender", "disabled": True}}}
    inv = sanitize_inventory(raw)
    assert usable_names(inv) == ["godot"]
    assert "TOKEN" not in json.dumps(inv)
    assert preflight(inv, ["godot"])["ok"]
    assert not preflight(inv, ["godot"])["live_verified"]
    assert preflight(inv, ["blender"])["disabled"] == ["blender"]
    gate = provider_gate(["godot"], ["browser"], ["godot"])
    assert gate["selected"] == "gemini"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = root / ".agents" / "mcp_config.json"
        cfg.parent.mkdir()
        cfg.write_text(json.dumps(raw))
        assert run_gemini_mcp_inventory(root, root) == inv
    print("PASS: Gemini capability configuration self-test")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="cmd")
    inv = sub.add_parser("inventory")
    inv.add_argument("--cwd", type=Path, default=Path("."))
    inv.add_argument("--write", type=Path)
    check = sub.add_parser("check")
    check.add_argument("--cwd", type=Path, default=Path("."))
    check.add_argument("--required-capability", action="append", default=[])
    route = sub.add_parser("route")
    route.add_argument("--required-capability", action="append", default=[])
    route.add_argument("--claude-capability", action="append", default=[])
    route.add_argument("--gemini-capability", action="append", default=[])
    route.add_argument("--prefer", choices=("claude", "gemini"))
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.cmd == "route":
        result = provider_gate(args.required_capability, args.claude_capability,
                               args.gemini_capability, args.prefer)
    elif args.cmd in ("check", "inventory"):
        inv_data = run_gemini_mcp_inventory(args.cwd)
        result = preflight(inv_data, args.required_capability) if args.cmd == "check" else {
            "schema_version": 1, "provider": "gemini", "capabilities": inv_data,
            "available": usable_names(inv_data), "verification": "configured-only", "live_verified": False}
    else:
        parser.error("command required")
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.cmd == "inventory" and args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(output, encoding="utf-8")
    print(output, end="")
    if args.cmd == "check":
        # Configuration alone never establishes live MCP availability.
        return 7 if args.required_capability or not result["ok"] else 0
    return 7 if result.get("blocked") else 0


if __name__ == "__main__":
    raise SystemExit(main())
