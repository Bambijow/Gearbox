#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

SECTIONS=[
    ("ROLE","role"),
    ("ISSUE / OUTCOME","outcome"),
    ("SPEC SLICE","spec_slice"),
    ("GLOBAL CONSTRAINTS","global_constraints"),
    ("YOUR TASK","task"),
    ("DEPENDENCIES ALREADY TRUE","dependencies"),
    ("INTERFACES","interfaces"),
    ("REQUIRED CAPABILITIES","required_capabilities"),
    ("OWNERSHIP","ownership"),
    ("CONTEXT POINTERS","pointers"),
    ("VERIFY","verify"),
    ("REVIEW FOCUS","review_focus"),
    ("OUTPUT CONTRACT","output_contract"),
]

def _lines(value)->list[str]:
    if value is None:
        return []
    if isinstance(value,str):
        return [value.strip()] if value.strip() else []
    if isinstance(value,list):
        seen=set(); out=[]
        for x in value:
            s=json.dumps(x,sort_keys=True,ensure_ascii=False) if isinstance(x,(dict,list)) else str(x).strip()
            if s and s not in seen:
                seen.add(s); out.append(s)
        return out
    if isinstance(value,dict):
        return [json.dumps(value,sort_keys=True,ensure_ascii=False)]
    return [str(value)]

def _section_lines(data:dict,key:str)->list[str]:
    if key=="required_capabilities" and key in data and data[key]==[]:
        return ["[]"]
    return _lines(data.get(key))

def compile_packet(data:dict,max_bytes:int)->tuple[str,dict]:
    blocks=[]; included=[]
    for title,key in SECTIONS:
        vals=_section_lines(data,key)
        if not vals:
            continue
        included.append(title)
        if len(vals)==1 and key in {"role","outcome","task","output_contract"}:
            body=vals[0]
        else:
            body="\n".join(f"- {v}" for v in vals)
        blocks.append(f"{title}\n{body}")
    packet="\n\n".join(blocks).rstrip()+"\n"
    b=packet.encode("utf-8")
    if len(b)>max_bytes:
        raise SystemExit(f"context packet exceeds budget: {len(b)}>{max_bytes} bytes")
    digest=hashlib.sha256(b).hexdigest()
    manifest={
        "schema_version":1,
        "sha256":digest,
        "bytes":len(b),
        "max_bytes":max_bytes,
        "sections":included,
        "pointer_count":len(_lines(data.get("pointers"))),
    }
    return packet,manifest

def self_test()->None:
    data={
        "role":"isolated worker",
        "outcome":"ship x",
        "spec_slice":["A","A","B"],
        "task":"implement",
        "required_capabilities":[],
        "pointers":["src/x.ts","docs/adr.md"],
        "verify":["pytest x"],
    }
    packet,manifest=compile_packet(data,4096)
    assert packet.count("- A")==1
    assert "REQUIRED CAPABILITIES\n- []" in packet
    assert manifest["bytes"]<4096 and manifest["sha256"]
    try:
        compile_packet({"role":"x"*100},20)
        raise AssertionError("budget should fail")
    except SystemExit:
        pass
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"task.json"; p.write_text(json.dumps(data))
        assert json.loads(p.read_text())["task"]=="implement"
    print("PASS: context-compiler self-test")

def main()->int:
    ap=argparse.ArgumentParser(description="Compile a bounded, hashable worker context packet from structured task facts.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--input")
    ap.add_argument("--output")
    ap.add_argument("--manifest")
    ap.add_argument("--max-bytes",type=int,default=12288)
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.input:
        ap.error("--input is required")
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    packet,manifest=compile_packet(data,args.max_bytes)
    if args.output:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(packet,encoding="utf-8")
    if args.manifest:
        Path(args.manifest).parent.mkdir(parents=True,exist_ok=True)
        Path(args.manifest).write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
