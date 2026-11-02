#!/usr/bin/env python3
"""Load review policy only from immutable PR base SHA."""
import argparse,json,subprocess,re
def policy(repo,sha,path="REVIEW.md"):
    if not re.fullmatch(r"[0-9a-fA-F]{40}",sha): raise ValueError("base must be an immutable full commit SHA")
    if path.startswith("/") or ".." in path.split("/"): raise ValueError("invalid policy path")
    p=subprocess.run(["git","-C",repo,"show",f"{sha}:{path}"],capture_output=True,text=True)
    if p.returncode: return {"status":"absent","base_sha":sha,"policy":None}
    return {"status":"loaded","base_sha":sha,"policy":p.stdout}
def main():
    a=argparse.ArgumentParser();a.add_argument("--repo",default=".");a.add_argument("--base-sha",required=True);a.add_argument("--path",default="REVIEW.md");s=a.parse_args()
    try: print(json.dumps(policy(s.repo,s.base_sha,s.path)));return 0
    except ValueError as e: print(json.dumps({"error":str(e)}));return 6
if __name__=="__main__":raise SystemExit(main())
