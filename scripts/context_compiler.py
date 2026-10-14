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
    ("CRITICAL POINTERS","critical_pointers"),
    ("CRITICAL DEPENDENCIES","critical_dependencies"),
    ("CONTEXT POINTERS","pointers"),
    ("VERIFY","verify"),
    ("REVIEW FOCUS","review_focus"),
    ("OUTPUT CONTRACT","output_contract"),
]
COMPRESSIBLE={
    "pointers":{"initial_cap":12,"min_keep":4},
    "dependencies":{"initial_cap":8,"min_keep":3},
}
HARD_KEYS={"role","outcome","spec_slice","task","required_capabilities","ownership","verify","output_contract"}

PACKET_KINDS={"implementation", "review", "investigation"}

def validate_packet(data:dict,max_bytes:int)->set[str]:
    """Validate required content, not just the byte size of whatever was supplied."""
    if not isinstance(data,dict):
        raise ValueError("context descriptor must be an object")
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    kind=data.get("packet_kind","implementation")
    if not isinstance(kind,str) or kind not in PACKET_KINDS:
        raise ValueError("packet_kind must be implementation, review or investigation")
    required=HARD_KEYS-({"spec_slice"} if kind=="investigation" else set())
    for key in sorted(required-{"required_capabilities"}):
        value=data.get(key)
        if not isinstance(value,(str,list,dict)) or not value or not _lines(value):
            raise ValueError(f"{kind} context requires non-empty {key}")
        if isinstance(value,list) and any(x is None or isinstance(x,bool) for x in value):
            raise ValueError(f"{key} contains an invalid item")
    capabilities=data.get("required_capabilities")
    if not isinstance(capabilities,list) or not all(isinstance(x,str) and x.strip() for x in capabilities):
        raise ValueError("required_capabilities must be an explicit list of non-empty strings; [] is valid")
    for key in ("critical_pointers","critical_dependencies"):
        if key in data and (not isinstance(data[key],list) or not all(isinstance(x,str) and x.strip() for x in data[key])):
            raise ValueError(f"{key} must be a list of non-empty strings")
    return required

def _lines(value)->list[str]:
    if value is None:return []
    if isinstance(value,str):return [value.strip()] if value.strip() else []
    if isinstance(value,list):
        seen=set();out=[]
        for x in value:
            s=json.dumps(x,sort_keys=True,ensure_ascii=False) if isinstance(x,(dict,list)) else str(x).strip()
            if s and s not in seen:
                seen.add(s);out.append(s)
        return out
    if isinstance(value,dict):return [json.dumps(value,sort_keys=True,ensure_ascii=False)]
    return [str(value)]

def _section_lines(data:dict,key:str)->list[str]:
    if key=="required_capabilities" and key in data and data[key]==[]:return ["[]"]
    vals=_lines(data.get(key))
    if key=="review_focus": vals=vals[:5]
    return vals

def _render(section_values:dict[str,list[str]],omitted:dict[str,int])->str:
    blocks=[]
    for title,key in SECTIONS:
        vals=section_values.get(key,[])
        if not vals and not omitted.get(key): continue
        shown=list(vals)
        if omitted.get(key):
            shown.append(f"[{omitted[key]} additional {key.replace('_',' ')} omitted; consult structured context descriptor if needed]")
        if len(shown)==1 and key in {"role","outcome","task","output_contract"}:
            body=shown[0]
        else:
            body="\n".join(f"- {v}" for v in shown)
        blocks.append(f"{title}\n{body}")
    return "\n\n".join(blocks).rstrip()+"\n"

def compile_packet(data:dict,max_bytes:int)->tuple[str,dict]:
    required=validate_packet(data,max_bytes)
    values={key:_section_lines(data,key) for _title,key in SECTIONS}
    omitted={}
    for key,policy in COMPRESSIBLE.items():
        vals=values[key]
        cap=policy["initial_cap"]
        if len(vals)>cap:
            omitted[key]=len(vals)-cap
            values[key]=vals[:cap]

    packet=_render(values,omitted)
    order=["pointers","dependencies"]
    while len(packet.encode("utf-8"))>max_bytes:
        changed=False
        for key in order:
            min_keep=COMPRESSIBLE[key]["min_keep"]
            if len(values[key])>min_keep:
                values[key].pop()
                omitted[key]=omitted.get(key,0)+1
                changed=True
                packet=_render(values,omitted)
                break
        if not changed:
            hard_bytes=len(_render({k:v for k,v in values.items() if k not in COMPRESSIBLE},{}).encode("utf-8"))
            raise SystemExit(f"context packet exceeds budget after safe compression: {len(packet.encode('utf-8'))}>{max_bytes}; non-compressible bytes={hard_bytes}")

    b=packet.encode("utf-8")
    digest=hashlib.sha256(b).hexdigest()
    manifest={
        "schema_version":2,"sha256":digest,"bytes":len(b),"max_bytes":max_bytes,
        "sections":[title for title,key in SECTIONS if values.get(key) or omitted.get(key)],
        "pointer_count":len(values.get("pointers",[])),
        "compression":{"omitted":omitted,"compressed":bool(omitted)},
        "hard_keys":sorted(required),"packet_kind":data.get("packet_kind","implementation"),
    }
    return packet,manifest

def self_test():
    data={
        "role":"isolated worker","outcome":"ship x","spec_slice":["A","A","B"],"task":"implement",
        "required_capabilities":[],"ownership":["src/x.ts"],"verify":["pytest x"],
        "output_contract":"diff, evidence and remaining uncertainty",
        "pointers":[f"docs/{i}.md" for i in range(30)],
        "dependencies":[f"D{i}" for i in range(10)]
    }
    packet,manifest=compile_packet(data,1200)
    assert packet.count("- A")==1
    assert "REQUIRED CAPABILITIES\n- []" in packet
    assert "OWNERSHIP\n- src/x.ts" in packet and "VERIFY\n- pytest x" in packet
    assert manifest["compression"]["compressed"] is True and manifest["bytes"]<=1200
    try:
        compile_packet({**data,"task":"y"*1000},100)
        raise AssertionError("hard overflow should fail")
    except SystemExit:pass
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"task.json";p.write_text(json.dumps(data));assert json.loads(p.read_text())["task"]=="implement"
    print("PASS: context-compiler self-test")

def main():
    ap=argparse.ArgumentParser(description="Compile a bounded, hashable worker context packet with safe low-priority compression.")
    ap.add_argument("--self-test",action="store_true");ap.add_argument("--input");ap.add_argument("--output");ap.add_argument("--manifest");ap.add_argument("--max-bytes",type=int,default=12288)
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    if not args.input:ap.error("--input is required")
    data=json.loads(Path(args.input).read_text(encoding="utf-8"));packet,manifest=compile_packet(data,args.max_bytes)
    if args.output:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(packet,encoding="utf-8")
    if args.manifest:
        Path(args.manifest).parent.mkdir(parents=True,exist_ok=True);Path(args.manifest).write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2));return 0

if __name__=="__main__":
    raise SystemExit(main())