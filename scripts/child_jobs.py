#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import tempfile
import time
from pathlib import Path

TERMINAL = {"COMPLETED", "FAILED", "CANCELLED"}


def load(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 2, "children": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["schema_version"] = max(int(data.get("schema_version", 1)), 2)
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def path_for(run: Path) -> Path:
    return run / "children.json"


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def resolve_artifact(child: dict, base: Path) -> Path | None:
    artifact = child.get("artifact")
    if not artifact:
        return None
    path = Path(artifact)
    if not path.is_absolute():
        path = base / path
    return path


def artifact_ready(child: dict, base: Path) -> bool:
    path = resolve_artifact(child, base)
    return bool(path and path.is_file() and path.stat().st_size > 0)


def reconcile(data: dict, base: Path, now: int | None = None) -> dict:
    now = now or int(time.time())
    counts: dict[str, int] = {}
    for child in data.setdefault("children", {}).values():
        status = child.get("status", "RUNNING")
        if status in TERMINAL:
            counts[status] = counts.get(status, 0) + 1
            continue
        if artifact_ready(child, base):
            child["status"] = "ARTIFACT_READY"
            child["updated_at"] = now
            counts["ARTIFACT_READY"] = counts.get("ARTIFACT_READY", 0) + 1
            continue
        pid = child.get("pid")
        if isinstance(pid, int) and child.get("host") == socket.gethostname() and not alive(pid):
            child["status"] = "ORPHANED"
            child["updated_at"] = now
            counts["ORPHANED"] = counts.get("ORPHANED", 0) + 1
            continue
        timeout = int(child.get("timeout_seconds", 3600))
        if now - int(child.get("started_at", now)) > timeout:
            child["status"] = "STALE"
            child["updated_at"] = now
            counts["STALE"] = counts.get("STALE", 0) + 1
            continue
        child["status"] = "RUNNING"
        counts["RUNNING"] = counts.get("RUNNING", 0) + 1
    return counts


def fingerprint_matches(data: dict, fingerprint: str, base: Path) -> list[dict]:
    matches = []
    for child in data.setdefault("children", {}).values():
        if child.get("fingerprint") != fingerprint:
            continue
        status = child.get("status", "RUNNING")
        reusable = status == "RUNNING" or status == "ARTIFACT_READY" or (
            status == "COMPLETED" and artifact_ready(child, base)
        )
        matches.append(
            {
                "id": child.get("id"),
                "status": status,
                "artifact": child.get("artifact"),
                "workspace": child.get("workspace"),
                "base_sha": child.get("base_sha"),
                "reusable": reusable,
            }
        )
    return matches


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        run = Path(td)
        data = {"schema_version": 2, "children": {}}
        data["children"]["a"] = {
            "id": "a",
            "status": "RUNNING",
            "started_at": 1,
            "timeout_seconds": 2,
        }
        counts = reconcile(data, run, now=10)
        assert counts["STALE"] == 1

        artifact = run / "r.json"
        artifact.write_text("{}\n", encoding="utf-8")
        data["children"]["b"] = {
            "id": "b",
            "status": "RUNNING",
            "started_at": 9,
            "timeout_seconds": 20,
            "artifact": "r.json",
            "fingerprint": "fp1",
        }
        reconcile(data, run, now=10)
        assert data["children"]["b"]["status"] == "ARTIFACT_READY"
        matches = fingerprint_matches(data, "fp1", run)
        assert matches[0]["reusable"] is True
        assert fingerprint_matches(data, "missing", run) == []
    print("PASS: child-jobs self-test")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Track, deduplicate and reconcile Gearbox delegated child work without tight polling."
    )
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    reg = sub.add_parser("register")
    reg.add_argument("--run-dir", type=Path, required=True)
    reg.add_argument("--id", required=True)
    reg.add_argument("--kind", required=True)
    reg.add_argument("--provider", required=True)
    reg.add_argument("--artifact")
    reg.add_argument("--timeout-seconds", type=int, default=3600)
    reg.add_argument("--pid", type=int)
    reg.add_argument("--fingerprint")
    reg.add_argument("--workspace")
    reg.add_argument("--base-sha")

    for name in ("complete", "fail", "cancel"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--run-dir", type=Path, required=True)
        cmd.add_argument("--id", required=True)
        cmd.add_argument("--note")

    rec = sub.add_parser("reconcile")
    rec.add_argument("--run-dir", type=Path, required=True)

    show = sub.add_parser("show")
    show.add_argument("--run-dir", type=Path, required=True)

    find = sub.add_parser("find")
    find.add_argument("--run-dir", type=Path, required=True)
    find.add_argument("--fingerprint", required=True)

    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.cmd:
        ap.error("command required")

    path = path_for(args.run_dir)
    data = load(path)
    children = data.setdefault("children", {})
    now = int(time.time())

    if args.cmd == "register":
        reconcile(data, args.run_dir.resolve(), now)
        if args.fingerprint:
            matches = fingerprint_matches(data, args.fingerprint, args.run_dir.resolve())
            reusable = [item for item in matches if item["reusable"]]
            if reusable:
                payload = {
                    "dispatch_allowed": False,
                    "reason": "DUPLICATE_INVOCATION",
                    "fingerprint": args.fingerprint,
                    "matches": reusable,
                }
                save(path, data)
                print(json.dumps(payload, indent=2))
                return 8

        old = children.get(args.id)
        if old and old.get("status") not in TERMINAL | {"STALE", "ORPHANED"}:
            raise SystemExit(f"child id already active: {args.id}")

        children[args.id] = {
            "id": args.id,
            "kind": args.kind,
            "provider": args.provider,
            "artifact": args.artifact,
            "timeout_seconds": args.timeout_seconds,
            "pid": args.pid,
            "host": socket.gethostname(),
            "status": "RUNNING",
            "started_at": now,
            "updated_at": now,
            "fingerprint": args.fingerprint,
            "workspace": args.workspace,
            "base_sha": args.base_sha,
        }
        payload = {"dispatch_allowed": True, "child": children[args.id]}

    elif args.cmd in {"complete", "fail", "cancel"}:
        if args.id not in children:
            raise SystemExit(f"unknown child: {args.id}")
        status = {"complete": "COMPLETED", "fail": "FAILED", "cancel": "CANCELLED"}[args.cmd]
        children[args.id]["status"] = status
        children[args.id]["updated_at"] = now
        if args.note:
            children[args.id]["note"] = args.note
        payload = children[args.id]

    elif args.cmd == "reconcile":
        payload = {
            "counts": reconcile(data, args.run_dir.resolve(), now),
            "children": children,
        }

    elif args.cmd == "find":
        reconcile(data, args.run_dir.resolve(), now)
        matches = fingerprint_matches(data, args.fingerprint, args.run_dir.resolve())
        payload = {
            "fingerprint": args.fingerprint,
            "matches": matches,
            "dispatch_allowed": not any(item["reusable"] for item in matches),
        }

    else:
        payload = data

    save(path, data)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
