#!/usr/bin/env python3
"""Read-only structural co-change diagnostic. Does not imply causality."""
from __future__ import annotations
import argparse
import json
import subprocess
from collections import Counter
from itertools import combinations
from pathlib import Path

def history(repo: str, limit: int) -> list[list[str]]:
    proc=subprocess.run(["git","-C",repo,"log","--format=COMMIT:%H","--name-only",f"-n{limit}"],
                        capture_output=True,text=True,check=False)
    if proc.returncode: raise ValueError(proc.stderr.strip() or "git log failed")
    commits=[]; current=[]
    for line in proc.stdout.splitlines():
        if line.startswith("COMMIT:"):
            if current: commits.append(sorted(set(current)))
            current=[]
        elif line.strip(): current.append(line.strip())
    if current: commits.append(sorted(set(current)))
    return commits

def analyze(commits: list[list[str]], minimum: int=3) -> list[dict]:
    files=Counter(); pairs=Counter()
    for paths in commits:
        unique=sorted(set(paths))
        files.update(unique)
        pairs.update(combinations(unique,2))
    result=[]
    for (left,right),count in pairs.items():
        if count < minimum: continue
        ratio=count/min(files[left],files[right])
        result.append({"files":[left,right],"cochanges":count,"conditional_overlap":round(ratio,3)})
    return sorted(result,key=lambda p:(-p["cochanges"],-p["conditional_overlap"],p["files"]))

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--repo",default=".");p.add_argument("--limit",type=int,default=100);p.add_argument("--minimum",type=int,default=3);a=p.parse_args()
    if a.limit<1 or a.minimum<1:p.error("limit and minimum must be positive")
    try: data=analyze(history(a.repo,a.limit),a.minimum)
    except ValueError as exc:print(json.dumps({"error":str(exc)}));return 7
    print(json.dumps({"pairs":data,"note":"Correlations only. Inspect imports and code paths before conclusions."},indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
