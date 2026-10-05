#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path

def load(path: Path) -> dict:
    if not path.exists(): return {"schema_version":1,"items":[]}
    return json.loads(path.read_text(encoding="utf-8"))

def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp"); tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8"); os.replace(tmp,path)

def totals(data: dict) -> dict:
    out={"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"reported_cost_usd":0.0,"items":len(data.get("items",[]))}
    cost_known=False
    for item in data.get("items",[]):
        for k in ("input_tokens","output_tokens","cached_input_tokens"):
            if isinstance(item.get(k),int): out[k]+=item[k]
        if isinstance(item.get("reported_cost_usd"),(int,float)):
            out["reported_cost_usd"]+=float(item["reported_cost_usd"]); cost_known=True
    out["total_tokens"]=out["input_tokens"]+out["output_tokens"]
    out["reported_cost_usd"]=round(out["reported_cost_usd"],6) if cost_known else None
    return out

def read_budgets(run: Path) -> dict:
    p=run/"state.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8")).get("budgets",{})
    except Exception: return {}

def self_test() -> None:
    d={"schema_version":1,"items":[{"input_tokens":10,"output_tokens":3,"cached_input_tokens":4,"reported_cost_usd":0.1},{"input_tokens":5,"output_tokens":2}]}
    t=totals(d); assert t["total_tokens"]==20 and t["reported_cost_usd"]==0.1
    print("PASS: usage-ledger self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Record provider-reported Gearbox usage without hard-coded model pricing.")
    ap.add_argument("--self-test",action="store_true")
    sub=ap.add_subparsers(dest="cmd")
    a=sub.add_parser("add"); a.add_argument("--run-dir",type=Path,required=True); a.add_argument("--dispatch-id",required=True); a.add_argument("--kind",required=True); a.add_argument("--provider",required=True); a.add_argument("--model"); a.add_argument("--input-tokens",type=int); a.add_argument("--output-tokens",type=int); a.add_argument("--cached-input-tokens",type=int); a.add_argument("--reported-cost-usd",type=float); a.add_argument("--estimated",action="store_true")
    a=sub.add_parser("summary"); a.add_argument("--run-dir",type=Path,required=True)
    a=sub.add_parser("check"); a.add_argument("--run-dir",type=Path,required=True); a.add_argument("--next-tokens",type=int,default=0); a.add_argument("--next-reported-cost-usd",type=float,default=0.0)
    args=ap.parse_args()
    if args.self_test: self_test(); return 0
    if not args.cmd: ap.error("command required")
    p=args.run_dir/"usage.json"; data=load(p)
    if args.cmd=="add":
        if any(x.get("dispatch_id")==args.dispatch_id for x in data["items"]):
            raise SystemExit(f"dispatch already recorded: {args.dispatch_id}")
        item={"dispatch_id":args.dispatch_id,"kind":args.kind,"provider":args.provider,"model":args.model,"recorded_at":int(time.time()),"estimated":bool(args.estimated)}
        for k in ("input_tokens","output_tokens","cached_input_tokens","reported_cost_usd"):
            v=getattr(args,k)
            if v is not None:
                if v<0: raise SystemExit(f"{k} must be non-negative")
                item[k]=v
        data["items"].append(item); save(p,data); payload={"added":item,"totals":totals(data)}
    elif args.cmd=="summary":
        payload=totals(data)
    else:
        t=totals(data); budgets=read_budgets(args.run_dir)
        projected_tokens=t["total_tokens"]+args.next_tokens
        current_cost=t["reported_cost_usd"] or 0.0
        projected_cost=current_cost+args.next_reported_cost_usd
        reasons=[]
        mt=budgets.get("max_total_tokens")
        mc=budgets.get("max_reported_cost_usd")
        if isinstance(mt,int) and projected_tokens>mt: reasons.append(f"token budget {projected_tokens}>{mt}")
        if isinstance(mc,(int,float)) and projected_cost>float(mc): reasons.append(f"reported-cost budget {projected_cost:.6f}>{float(mc):.6f}")
        payload={"allowed":not reasons,"reasons":reasons,"current":t,"projected_total_tokens":projected_tokens,"projected_reported_cost_usd":round(projected_cost,6),"budgets":{"max_total_tokens":mt,"max_reported_cost_usd":mc}}
        print(json.dumps(payload,indent=2))
        return 0 if not reasons else 6
    print(json.dumps(payload,indent=2)); return 0

if __name__=="__main__":
    raise SystemExit(main())
