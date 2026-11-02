#!/usr/bin/env python3
"""Check observed orchestration actions, not agent self-reported intentions."""
import json,argparse
from pathlib import Path
def check(contract,events):
    errors=[]
    if not isinstance(events,list) or any(not isinstance(e,dict) or not isinstance(e.get("action"),str) for e in events):return ["invalid action trace"]
    actions=[e["action"] for e in events]
    for wanted in contract.get("required_actions",[]):
        if wanted not in actions:errors.append("missing action: "+wanted)
    for forbidden in contract.get("forbidden_actions",[]):
        if forbidden in actions:errors.append("forbidden action: "+forbidden)
    for before,after in contract.get("required_order",[]):
        if before not in actions or after not in actions or actions.index(before)>=actions.index(after):errors.append(f"wrong order: {before} -> {after}")
    return errors
def main():
    p=argparse.ArgumentParser();p.add_argument("contract");p.add_argument("trace");a=p.parse_args()
    c=json.loads(Path(a.contract).read_text());events=json.loads(Path(a.trace).read_text())
    errors=check(c,events)
    print(json.dumps({"passed":not errors,"errors":errors}));return 1 if errors else 0
if __name__=="__main__":raise SystemExit(main())
