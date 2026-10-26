#!/usr/bin/env python3
"""Guard against benchmark-only speedups with independent holdout measurements."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def adjudicate(doc: dict) -> dict:
    failures=[]
    budget=doc.get("budget",{})
    for k in ("attempts","seconds","usd"):
        if k in budget and (not isinstance(budget[k],(int,float)) or budget[k]<0):
            failures.append(f"invalid budget {k}")
    used=doc.get("usage",{})
    for k,cap in budget.items():
        if k in ("attempts","seconds","usd") and used.get(k,0)>cap:failures.append(f"budget exceeded: {k}")
    if doc.get("holdout_disclosed_before_variant") is not False:
        failures.append("holdout not blind")
    if doc.get("holdout_mutated") is not False:
        failures.append("holdout changed")
    if doc.get("workload_equivalent") is not True:
        failures.append("workload not equivalent")
    if doc.get("required_work_skipped") is not False:
        failures.append("required work skipped")
    if doc.get("correctness_pass") is not True:
        failures.append("correctness checks failed")
    for label in ("baseline","candidate"):
        runs=doc.get(label,{})
        for split in ("training","holdout"):
            values=runs.get(split)
            if not isinstance(values,list) or len(values)<3 or any(not isinstance(v,(int,float)) or isinstance(v,bool) or v<=0 for v in values):
                failures.append(f"invalid {label}.{split} measurements (minimum 3 positive samples)")
    if failures:return {"decision":"REJECT","reasons":failures}
    def median(values):
        s=sorted(values);n=len(s);return s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2
    base=median(doc["baseline"]["holdout"])
    new=median(doc["candidate"]["holdout"])
    improvement=(base-new)/base
    threshold=doc.get("min_improvement",0.03)
    if not isinstance(threshold,(int,float)) or threshold<0:
        return {"decision":"REJECT","reasons":["invalid min_improvement"]}
    if improvement<threshold:
        return {"decision":"REJECT","reasons":["holdout improvement below threshold"],"holdout_improvement":round(improvement,5)}
    return {"decision":"KEEP","reasons":[],"holdout_improvement":round(improvement,5)}

def self_test():
    base={"holdout_disclosed_before_variant":False,"holdout_mutated":False,"workload_equivalent":True,"required_work_skipped":False,"correctness_pass":True,"budget":{"attempts":2},"usage":{"attempts":1},"baseline":{"training":[100,100,101],"holdout":[100,101,100]},"candidate":{"training":[80,79,81],"holdout":[80,81,80]}}
    assert adjudicate(base)["decision"]=="KEEP"
    assert adjudicate({**base,"required_work_skipped":True})["decision"]=="REJECT"
    assert adjudicate({**base,"candidate":{"training":[40,40,40],"holdout":[100,101,100]}})["decision"]=="REJECT"
    assert adjudicate({**base,"usage":{"attempts":3}})["decision"]=="REJECT"
    assert adjudicate({**base,"holdout_disclosed_before_variant":True})["decision"]=="REJECT"
    print("PASS: optimization-holdout self-test")

def main():
    p=argparse.ArgumentParser();p.add_argument("report",nargs="?");p.add_argument("--self-test",action="store_true");a=p.parse_args()
    if a.self_test:self_test();return 0
    if not a.report:p.error("report is required")
    result=adjudicate(json.loads(Path(a.report).read_text()))
    print(json.dumps(result,indent=2));return 0 if result["decision"]=="KEEP" else 6
if __name__=="__main__":raise SystemExit(main())
