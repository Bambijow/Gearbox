#!/usr/bin/env python3
"""Deterministic budgeted retro sampling; always prioritize troubled runs."""
import argparse,hashlib,json
from pathlib import Path
def select(run_id,state,sample_rate=0.2):
    if not 0<=sample_rate<=1:raise ValueError("sample rate must be 0..1")
    repairs=state.get("repair_cycles",state.get("usage",{}).get("repair_cycles",0))
    troubled=state.get("status") in ("BLOCKED","FAILED","PR_BLOCKED","PR_BUDGET_EXHAUSTED") or (isinstance(repairs,int) and repairs>=2) or bool(state.get("escalations"))
    bucket=int(hashlib.sha256(run_id.encode()).hexdigest()[:12],16)/float(16**12)
    return {"selected":troubled or bucket<sample_rate,"reason":"troubled-run" if troubled else ("sampled" if bucket<sample_rate else "not-sampled"),"automatic_mutation":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);p.add_argument("--state",type=Path,required=True);p.add_argument("--sample-rate",type=float,default=.2);a=p.parse_args()
    try: print(json.dumps(select(a.run_id,json.loads(a.state.read_text()),a.sample_rate)));return 0
    except (ValueError,OSError) as e: print(json.dumps({"error":str(e)}));return 6
if __name__=="__main__":raise SystemExit(main())
