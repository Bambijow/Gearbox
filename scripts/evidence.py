#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from redact import redact_obj, redact_text


def load(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 1, "items": []}
    return redact_obj(json.loads(path.read_text(encoding="utf-8")))


def save(path: Path, data: dict) -> None:
    data = redact_obj(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Maintain Gearbox's redacted evidence ledger.")
    sp = ap.add_subparsers(dest="cmd", required=True)

    a = sp.add_parser("init")
    a.add_argument("--file", required=True)

    a = sp.add_parser("add")
    a.add_argument("--file", required=True)
    a.add_argument("--kind", required=True)
    a.add_argument("--sha")
    a.add_argument("--status", required=True)
    a.add_argument("--summary", required=True)
    a.add_argument("--command")
    a.add_argument("--exit-code", type=int)
    a.add_argument("--path")
    a.add_argument("--meta-json", default="{}")

    a = sp.add_parser("invalidate")
    a.add_argument("--file", required=True)
    a.add_argument("--sha", required=True)
    a.add_argument("--reason", required=True)

    a = sp.add_parser("show")
    a.add_argument("--file", required=True)

    args = ap.parse_args()
    path = Path(args.file)
    data = load(path)

    if args.cmd == "init":
        save(path, data)
        return 0

    if args.cmd == "show":
        print(json.dumps(redact_obj(data), indent=2))
        return 0

    if args.cmd == "add":
        item = {
            "id": len(data["items"]) + 1,
            "kind": redact_text(args.kind),
            "sha": args.sha,
            "status": redact_text(args.status),
            "summary": redact_text(args.summary),
            "created_at": int(time.time()),
            "valid": True,
        }
        if args.command:
            item["command"] = redact_text(args.command)
        if args.exit_code is not None:
            item["exit_code"] = args.exit_code
        if args.path:
            item["path"] = redact_text(args.path)
        try:
            meta = json.loads(args.meta_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid --meta-json: {exc}")
        item.update(redact_obj(meta))
        data["items"].append(item)
    else:
        reason = redact_text(args.reason)
        for item in data["items"]:
            if item.get("sha") == args.sha and item.get("valid", True):
                item["valid"] = False
                item["invalidated_reason"] = reason

    save(path, data)
    print(json.dumps(redact_obj(data), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
