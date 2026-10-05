#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"contains","not_contains","regex","not_regex","max_chars","min_chars"}

def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")

def load(path: Path) -> dict:
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{path}: invalid JSON: {exc}")
    required=("name","context_files","prompt","assertions")
    for key in required:
        if key not in data:
            fail(f"{path}: missing {key}")
    if not isinstance(data["context_files"],list) or not all(isinstance(x,str) and x for x in data["context_files"]):
        fail(f"{path}: context_files must be non-empty strings")
    if not isinstance(data["prompt"],str) or not data["prompt"].strip():
        fail(f"{path}: prompt must be non-empty")
    if not isinstance(data["assertions"],list) or not data["assertions"]:
        fail(f"{path}: assertions must be a non-empty list")
    for item in data["assertions"]:
        if not isinstance(item,dict) or item.get("type") not in ALLOWED:
            fail(f"{path}: invalid assertion {item!r}")
        if item["type"] in {"contains","not_contains","regex","not_regex"} and not isinstance(item.get("value"),str):
            fail(f"{path}: string assertion needs value")
        if item["type"] in {"max_chars","min_chars"} and not isinstance(item.get("value"),int):
            fail(f"{path}: length assertion needs integer value")
    return data

def validate_context(root: Path, scenario: dict, source: Path) -> None:
    for raw in scenario["context_files"]:
        p=(root/raw).resolve()
        try: p.relative_to(root.resolve())
        except ValueError: fail(f"{source}: context path escapes root: {raw}")
        if not p.is_file():
            fail(f"{source}: missing context file: {raw}")

def build_prompt(root: Path, scenario: dict) -> str:
    chunks=[
        "You are evaluating the behavior of Gearbox prompt contracts. Follow the supplied contract as if it were loaded by the host. Do not modify files or call tools. Answer the evaluation request only.\n"
    ]
    for raw in scenario["context_files"]:
        text=(root/raw).read_text(encoding="utf-8")
        chunks.append(f"\n--- BEGIN CONTEXT {raw} ---\n{text}\n--- END CONTEXT {raw} ---\n")
    chunks.append("\n--- EVALUATION REQUEST ---\n"+scenario["prompt"].strip()+"\n")
    return "".join(chunks)

def grade(scenario: dict, output: str) -> list[str]:
    errors=[]
    for a in scenario["assertions"]:
        typ=a["type"]; val=a["value"]
        ignore=bool(a.get("ignore_case",True))
        hay=output.lower() if ignore and isinstance(val,str) else output
        needle=val.lower() if ignore and isinstance(val,str) else val
        if typ=="contains" and needle not in hay:
            errors.append(f"missing text: {val!r}")
        elif typ=="not_contains" and needle in hay:
            errors.append(f"forbidden text present: {val!r}")
        elif typ in {"regex","not_regex"}:
            flags=re.I if ignore else 0
            found=bool(re.search(val,output,flags))
            if typ=="regex" and not found: errors.append(f"regex did not match: {val!r}")
            if typ=="not_regex" and found: errors.append(f"forbidden regex matched: {val!r}")
        elif typ=="max_chars" and len(output)>val:
            errors.append(f"output has {len(output)} chars; max {val}")
        elif typ=="min_chars" and len(output)<val:
            errors.append(f"output has {len(output)} chars; min {val}")
    return errors

def scenario_paths(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.glob("*.json"))

def validate(target: Path, root: Path) -> int:
    paths=scenario_paths(target)
    if not paths:
        fail(f"no behavior scenarios found under {target}")
    for p in paths:
        sc=load(p); validate_context(root,sc,p)
    print(f"PASS: behavior eval schema ({len(paths)} scenario(s))")
    return 0

def run_one(path: Path, root: Path, provider: str, command: str, out_dir: Path) -> int:
    sc=load(path); validate_context(root,sc,path)
    prompt=build_prompt(root,sc)
    cmd=shlex.split(command)
    if not cmd: fail("empty runner command")
    started=time.time()
    proc=subprocess.run(cmd,input=prompt,text=True,capture_output=True,check=False)
    out_dir.mkdir(parents=True,exist_ok=True)
    stem=re.sub(r"[^a-zA-Z0-9_.-]+","-",sc["name"]).strip("-")
    output_path=out_dir/f"{stem}.{provider}.txt"
    output_path.write_text(proc.stdout,encoding="utf-8")
    meta={
        "scenario":sc["name"],"provider":provider,"command":cmd[0],
        "exit_code":proc.returncode,"duration_seconds":round(time.time()-started,3),
        "output":str(output_path)
    }
    (out_dir/f"{stem}.{provider}.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    if proc.returncode!=0:
        print(proc.stderr)
        fail(f"runner exited {proc.returncode}: {path}")
    errors=grade(sc,proc.stdout)
    for e in errors: print("FAIL:",e)
    if errors: return 1
    print(f"PASS: {sc['name']} [{provider}]")
    return 0

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        (root/"ctx.md").write_text("RULE: say READY, never BANANA\n",encoding="utf-8")
        p=root/"s.json"
        p.write_text(json.dumps({
            "name":"t","context_files":["ctx.md"],"prompt":"respond",
            "assertions":[{"type":"contains","value":"ready"},{"type":"not_contains","value":"banana"},{"type":"max_chars","value":20}]
        }),encoding="utf-8")
        sc=load(p); validate_context(root,sc,p)
        assert not grade(sc,"READY")
        assert grade(sc,"READY BANANA")
        assert "ctx.md" in build_prompt(root,sc)
    print("PASS: behavior-eval self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Validate/grade optional Gearbox behavioral evals without putting paid model calls in normal CI.")
    sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("validate"); a.add_argument("target",type=Path); a.add_argument("--root",type=Path,default=ROOT)
    a=sub.add_parser("grade"); a.add_argument("scenario",type=Path); a.add_argument("output",type=Path)
    a=sub.add_parser("run"); a.add_argument("scenario",type=Path); a.add_argument("--provider",choices=("claude","codex"),required=True); a.add_argument("--command"); a.add_argument("--out-dir",type=Path,default=Path(".gearbox/evals"))
    sub.add_parser("self-test")
    args=ap.parse_args()
    if args.cmd=="self-test": self_test(); return 0
    if args.cmd=="validate": return validate(args.target,args.root.resolve())
    if args.cmd=="grade":
        sc=load(args.scenario); errors=grade(sc,args.output.read_text(encoding="utf-8"))
        for e in errors: print("FAIL:",e)
        if errors: return 1
        print("PASS:",sc["name"]); return 0
    env_key=f"GEARBOX_EVAL_{args.provider.upper()}_CMD"
    command=args.command or os.environ.get(env_key)
    if not command:
        fail(f"set --command or {env_key}; normal CI intentionally does not call paid models")
    return run_one(args.scenario,ROOT,args.provider,command,args.out_dir)

if __name__=="__main__":
    raise SystemExit(main())
