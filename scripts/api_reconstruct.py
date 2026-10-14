#!/usr/bin/env python3
"""Offline, conservative HAR 1.2 -> observed API inventory / candidate scenarios.

Never sends requests, replays traffic, or copies credentials or body values into output.
The output is not an authoritative OpenAPI specification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, unquote

MAX_BYTES = 16 * 1024 * 1024
MAX_ENTRIES = 3000
MAX_DEPTH = 6
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)
SENSITIVE_SEGMENT = re.compile(r"@|(?:token|secret|password|auth|bearer|session|api[_-]?key)", re.I)
ALLOWED_METHOD = {"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"}


def shape(value, depth=0):
    """Structural observations only. Never return example values or infer requiredness."""
    if depth >= MAX_DEPTH:
        return {"type": "unknown", "limitations": ["max nesting depth"]}
    if isinstance(value, dict):
        return {"type": "object", "properties": {
            # Keys may be dynamic user values: avoid leaking obviously sensitive identifiers.
            (k if len(k) <= 80 and not SENSITIVE_SEGMENT.search(k) else "[redacted-key]"): shape(v, depth + 1)
            for k, v in sorted(value.items()) if isinstance(k, str)
        }}
    if isinstance(value, list):
        variants = []
        for item in value[:12]:
            variant = shape(item, depth + 1)
            if variant not in variants:
                variants.append(variant)
        return {"type": "array", "observed_item_shapes": variants,
                "limitations": ["sample of first 12 items"] if len(value) > 12 else []}
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    return {"type": "string"} if isinstance(value, str) else {"type": "unknown"}


def safe_path(url: str) -> tuple[str, list[str]]:
    if not isinstance(url, str) or len(url) > 8192:
        raise ValueError("invalid URL")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("only absolute HTTP(S) URLs supported")
    parts = parsed.path.split("/")
    result = []
    for raw in parts:
        seg = unquote(raw)
        if raw == "":
            result.append("")
        elif seg.isdecimal():
            result.append("{numeric}")
        elif UUID.fullmatch(seg):
            result.append("{uuid}")
        elif len(seg) > 48 or SENSITIVE_SEGMENT.search(seg) or not re.fullmatch(r"[A-Za-z0-9._~-]{1,48}", seg):
            result.append("{opaque}")
        else:
            result.append(seg)
    # Do not export query values. Names are intentionally omitted too.
    return "/".join(result) or "/", []


def extract_json_shape(payload: dict | None, content_type: str | None) -> dict:
    if not isinstance(payload, dict):
        return {"status": "unavailable"}
    # Only parse producer-declared JSON. Do not mistake opaque binary/base64 for JSON.
    if not isinstance(content_type, str) or "json" not in content_type.lower():
        return {"status": "non-json-or-unknown"}
    value = payload.get("text")
    if not isinstance(value, str) or len(value) > MAX_BYTES // 2:
        return {"status": "body-unavailable"}
    try:
        decoded = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return {"status": "unparseable-json"}
    return {"status": "observed", "shape": shape(decoded)}


def content_type(headers: list | None, fallback: str = "") -> str:
    if not isinstance(headers, list):
        return fallback
    for h in headers:
        if isinstance(h, dict) and str(h.get("name", "")).lower() == "content-type":
            return str(h.get("value", ""))[:160]
    return fallback


def inspect_har(data: dict, digest: str) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("log"), dict):
        raise ValueError("HAR must contain log")
    log = data["log"]
    if log.get("version") != "1.2" or not isinstance(log.get("entries"), list):
        raise ValueError("only HAR 1.2 with explicit entries is supported")
    entries = log["entries"]
    if len(entries) > MAX_ENTRIES:
        raise ValueError("HAR entry budget exceeded")
    routes = defaultdict(lambda: {"count": 0, "statuses": set(), "request_shapes": [],
                                "response_shapes": [], "ordinals": [], "content_types": set()})
    skipped = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("request"), dict) or not isinstance(entry.get("response"), dict):
            skipped.append({"ordinal": i, "reason": "incomplete entry"})
            continue
        req, resp = entry["request"], entry["response"]
        method = req.get("method")
        if method not in ALLOWED_METHOD:
            skipped.append({"ordinal": i, "reason": "unsupported method"})
            continue
        try:
            path, _ = safe_path(req.get("url"))
        except ValueError:
            skipped.append({"ordinal": i, "reason": "unparseable URL"})
            continue
        status = resp.get("status")
        if type(status) is not int or not 100 <= status <= 599:
            skipped.append({"ordinal": i, "reason": "unknown response status"})
            continue
        record = routes[(path, method)]
        record["count"] += 1
        record["statuses"].add(status)
        record["ordinals"].append(i)
        req_shape = extract_json_shape(req.get("postData"), content_type(req.get("headers"), req.get("postData", {}).get("mimeType", "") if isinstance(req.get("postData"), dict) else ""))
        content = resp.get("content")
        resp_shape = extract_json_shape(content, content_type(resp.get("headers"), content.get("mimeType", "") if isinstance(content, dict) else ""))
        for key, value in (("request_shapes", req_shape), ("response_shapes", {"status_code": status, **resp_shape})):
            if value not in record[key]:
                record[key].append(value)
        if isinstance(content, dict) and isinstance(content.get("mimeType"), str):
            record["content_types"].add(content["mimeType"].split(";")[0].strip()[:120].lower())
    operations = []
    openapi_paths = {}
    for (path, method), rec in sorted(routes.items()):
        op_id = "op-" + hashlib.sha256((method + " " + path).encode()).hexdigest()[:12]
        entry = {"id": op_id, "method": method, "path_template": path,
                 "source_ordinals": rec["ordinals"], "observed_count": rec["count"],
                 "statuses": sorted(rec["statuses"]), "content_types": sorted(rec["content_types"]),
                 "request_shapes": rec["request_shapes"], "response_shapes": rec["response_shapes"],
                 "limitations": ["Observed samples only; route templates are inferred",
                                 "Required fields, authentication rules, server side effects and idempotency are unknown"]}
        operations.append(entry)
        # A valid, deliberately incomplete OpenAPI candidate. No example payloads or required fields.
        responses = {str(status): {"description": "Observed HTTP status only"} for status in rec["statuses"]}
        openapi_paths.setdefault(path, {})[method.lower()] = {
            "operationId": op_id, "responses": responses,
            "x-gearbox-observation": {"source_ordinals": rec["ordinals"],
                                      "requires_human_verification": True}}
    return {"schema_version": 1, "source": {"format": "HAR-1.2", "sha256": digest,
                                                 "original_entries": len(entries)},
            "status": "OBSERVED_ONLY", "operations": operations, "skipped": skipped,
            "candidate_probes": [{"operation_id": o["id"], "kind": "human-reviewed",
                                  "suggestions": ["boundary values", "missing/optional fields", "repeated request/idempotency", "state read-after-write", "authorization variations"],
                                  "requires_authorization": True} for o in operations],
            "openapi_candidate": {"openapi": "3.1.0", "info": {"title": "Unverified observed API", "version": "0.0.0-observed"},
                                  "paths": openapi_paths},
            "limitations": ["Historical captures are not proof of deployed server identity or causality",
                            "No requests sent; no claim of API completeness or correct target implementation",
                            "No response/request values, hostnames, query values or authentication headers retained"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--har", type=Path, required=True, help="Existing HAR 1.2; no network calls")
    args = p.parse_args()
    try:
        if args.har.stat().st_size > MAX_BYTES:
            raise ValueError("HAR file budget exceeded")
        raw = args.har.read_bytes()
        result = inspect_har(json.loads(raw), hashlib.sha256(raw).hexdigest())
    except (ValueError, OSError) as error:
        p.error(str(error))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
