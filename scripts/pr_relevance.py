#!/usr/bin/env python3
"""Conservative decision helper for PR repair after target branch changes."""
import argparse,json,subprocess
def run(repo,*args):
    p=subprocess.run(["git","-C",repo,*args],capture_output=True,text=True)
    if p.returncode:raise ValueError(p.stderr.strip() or "git command failed")
    return p.stdout.strip()
def assess(repo,original_base,current_base,head):
    old=set(run(repo,"diff","--name-only",original_base,current_base).splitlines())
    pr=set(run(repo,"diff","--name-only",original_base,head).splitlines())
    overlap=sorted(old&pr)
    return {"status":"REASSESS" if overlap else "PROCEED","base_changed_paths":sorted(old),"overlapping_paths":overlap,"note":"Path disjointness does not prove semantic relevance; check acceptance criteria and current base before repair."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",default=".");p.add_argument("--original-base",required=True);p.add_argument("--current-base",required=True);p.add_argument("--head",required=True);a=p.parse_args()
    try:r=assess(a.repo,a.original_base,a.current_base,a.head)
    except ValueError as e: print(json.dumps({"status":"BLOCKED","reason":str(e)}));return 7
    print(json.dumps(r,indent=2));return 6 if r["status"]=="REASSESS" else 0
if __name__=="__main__":raise SystemExit(main())
