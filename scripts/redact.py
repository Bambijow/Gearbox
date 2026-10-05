#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

REPLACEMENT = "<redacted>"
SENSITIVE_KEYS = (
    r"password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|"
    r"private[_-]?key|client[_-]?secret|cookie|session[_-]?(?:token|cookie)"
)
_SENSITIVE_KEY_RE = re.compile(rf"(?i)^(?:{SENSITIVE_KEYS})$")

_PATTERNS = [
    re.compile(r"(?i)\b(authorization\s*:\s*bearer\s+)([^\s]+)"),
    re.compile(r"(?i)\b(bearer\s+)([A-Za-z0-9._~+\-/=]{12,})"),
    re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
    re.compile(r"(?i)([?&](?:token|api[_-]?key|key|signature|sig|secret|access[_-]?token)=)([^&#\s]+)"),
    re.compile(rf"(?i)\b((?:{SENSITIVE_KEYS})\s*[:=]\s*)([^\s,;]+)"),
    re.compile(rf"""(?i)(["']?(?:{SENSITIVE_KEYS})["']?\s*:\s*["'])([^"'\r\n]+)(["'])"""),
    re.compile(r"(?i)(https?://[^\s:/]+:)([^@\s]+)(@)"),
]

_PRIVATE_KEY = re.compile(
    r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----.*?-----END(?: [A-Z0-9]+)? PRIVATE KEY-----",
    re.DOTALL,
)

def redact_text(text: str) -> str:
    text = _PRIVATE_KEY.sub(REPLACEMENT, text)
    for pattern in _PATTERNS:
        groups = pattern.groups
        if groups == 1:
            text = pattern.sub(REPLACEMENT, text)
        elif groups == 2:
            text = pattern.sub(lambda m: m.group(1) + REPLACEMENT, text)
        elif groups == 3:
            text = pattern.sub(lambda m: m.group(1) + REPLACEMENT + m.group(3), text)
    return text

def redact_obj(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_obj(v) for v in value]
    if isinstance(value, dict):
        return {
            k: (REPLACEMENT if _SENSITIVE_KEY_RE.match(str(k)) else redact_obj(v))
            for k, v in value.items()
        }
    return value

def contains_secret_like(text: str) -> bool:
    return redact_text(text) != text

def self_test() -> int:
    cases = {
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz": "Authorization: Bearer <redacted>",
        "token=supersecretvalue": "token=<redacted>",
        "https://user:pass123@example.com/x": "https://user:<redacted>@example.com/x",
        "github_pat_abcdefghijklmnopqrstuvwxyz0123456789": "<redacted>",
        '{"token":"supersecretvalue"}': '{"token":"<redacted>"}',
        '{"client_secret": "abc123xyz"}': '{"client_secret": "<redacted>"}',
    }
    for raw, expected in cases.items():
        got = redact_text(raw)
        if got != expected:
            raise SystemExit(f"redaction self-test failed: {raw!r} -> {got!r}")
    obj = redact_obj({"token": "abc", "nested": {"password": "xyz"}, "safe": "value"})
    if obj["token"] != REPLACEMENT or obj["nested"]["password"] != REPLACEMENT or obj["safe"] != "value":
        raise SystemExit(f"redaction object self-test failed: {obj!r}")
    print("PASS: redaction self-test")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser(description="Redact obvious secret-like values from Gearbox text/JSON.")
    ap.add_argument("--check", action="store_true", help="Exit 1 if obvious secret-like material remains.")
    ap.add_argument("--json", action="store_true", help="Redact JSON recursively.")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    raw = sys.stdin.read()
    if args.check:
        if contains_secret_like(raw):
            print("FAIL: secret-like material detected", file=sys.stderr)
            return 1
        print("PASS: no obvious secret-like material detected")
        return 0
    if args.json:
        obj = json.loads(raw)
        print(json.dumps(redact_obj(obj), indent=2))
    else:
        sys.stdout.write(redact_text(raw))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
