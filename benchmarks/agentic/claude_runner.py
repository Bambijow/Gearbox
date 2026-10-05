#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

def num(value):
    return value if isinstance(value,(int,float)) else None

def main() -> int:
    req=json.load(sys.stdin)
    claude=shutil.which("claude")
    if not claude:
        print(json.dumps({"error":"claude CLI not found"}))
        return 2
    cmd=[
        claude,"-p",req["prompt"],
        "--model",req["model"],
        "--permission-mode","bypassPermissions",
        "--output-format","json",
        "--setting-sources","project,local",
        "--strict-mcp-config",
    ]
    plugin=req.get("plugin_dir")
    if plugin:
        cmd += ["--plugin-dir",plugin]
    append=req.get("append_system_prompt")
    if append:
        cmd += ["--append-system-prompt",append]
    env={
        **os.environ,
        "CLAUDE_CODE_DISABLE_CLAUDE_MDS":"1",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY":"1",
        "GEARBOX_AGENTIC_BENCH":"1",
    }
    started=time.time()
    proc=subprocess.run(
        cmd,cwd=req["workspace"],env=env,capture_output=True,text=True,
        timeout=int(req.get("timeout_seconds",600)),check=False
    )
    duration=time.time()-started
    try:
        payload=json.loads(proc.stdout)
    except Exception:
        payload={}
    usage=payload.get("usage") if isinstance(payload.get("usage"),dict) else {}
    out={
        "exit_code":proc.returncode,
        "duration_seconds":round(num(payload.get("duration_ms"))/1000,3) if num(payload.get("duration_ms")) is not None else round(duration,3),
        "turns":payload.get("num_turns") or payload.get("turns"),
        "reported_cost_usd":payload.get("total_cost_usd") or payload.get("cost_usd"),
        "input_tokens":usage.get("input_tokens") or payload.get("input_tokens"),
        "output_tokens":usage.get("output_tokens") or payload.get("output_tokens"),
        "cached_input_tokens":(
            (usage.get("cache_read_input_tokens") or 0)+(usage.get("cache_creation_input_tokens") or 0)
            if usage else payload.get("cached_input_tokens")
        ),
        "result":payload.get("result"),
        "stderr":proc.stderr[-2000:],
    }
    print(json.dumps(out))
    return 0 if proc.returncode==0 else proc.returncode

if __name__=="__main__":
    raise SystemExit(main())
