#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path

COST_RANK={"low":0,"medium":1,"high":2}
PROFILE_RANK={"dev":0,"standard":1,"release":2,"critical":3}

def matches_check(check:dict,paths:list[str],surfaces:set[str],profile:str)->bool:
    profiles=check.get("profiles")
    if profiles and profile not in profiles:
        return False
    if check.get("always"):
        return True
    if surfaces.intersection(check.get("surfaces",[])):
        return True
    for pattern in check.get("path_globs",[]):
        if any(fnmatch.fnmatch(p,pattern) for p in paths):
            return True
    return False

def compile_plan(catalog:dict,paths:list[str],surfaces:list[str],profile:str)->dict:
    selected=[]
    surface_set=set(surfaces)
    for check in catalog.get("checks",[]):
        if matches_check(check,paths,surface_set,profile):
            selected.append(dict(check))

    # Within one coverage_group, prefer the narrowest/cheapest passing candidate
    # unless a broader check explicitly requires release/critical.
    by_group={}
    ungroupped=[]
    for check in selected:
        group=check.get("coverage_group")
        if not group:
            ungroupped.append(check); continue
        by_group.setdefault(group,[]).append(check)

    collapsed=[]
    for group,items in sorted(by_group.items()):
        forced=[x for x in items if x.get("required_profiles") and profile in x["required_profiles"]]
        if forced:
            collapsed.extend(forced); continue
        items.sort(key=lambda x:(COST_RANK.get(x.get("cost","medium"),1),0 if x.get("scope")=="narrow" else 1,x.get("id","")))
        collapsed.append(items[0])
    final=ungroupped+collapsed
    final.sort(key=lambda x:(COST_RANK.get(x.get("cost","medium"),1),x.get("id","")))
    return {
        "schema_version":1,
        "profile":profile,
        "surfaces":sorted(surface_set),
        "paths":paths,
        "checks":[
            {
                "id":x.get("id"),
                "kind":x.get("kind"),
                "command":x.get("command"),
                "cost":x.get("cost","medium"),
                "coverage_group":x.get("coverage_group"),
                "reason":"trigger matched changed path/surface/profile"
            } for x in final
        ]
    }

def self_test():
    catalog={"checks":[
        {"id":"unit-ui","kind":"test","command":"pytest ui","cost":"low","surfaces":["user_ui"],"coverage_group":"ui-tests","scope":"narrow"},
        {"id":"all-tests","kind":"test","command":"pytest","cost":"high","surfaces":["user_ui"],"coverage_group":"ui-tests","scope":"broad","required_profiles":["critical"]},
        {"id":"typecheck","kind":"typecheck","command":"npm run typecheck","cost":"medium","path_globs":["src/*.ts","src/*.tsx","src/**/*.ts","src/**/*.tsx"]},
        {"id":"docs","kind":"lint","command":"markdownlint .","cost":"low","surfaces":["docs"]}
    ]}
    p=compile_plan(catalog,["src/x.ts"],["user_ui"],"standard")
    ids=[x["id"] for x in p["checks"]]
    assert "unit-ui" in ids and "all-tests" not in ids and "typecheck" in ids
    p2=compile_plan(catalog,["src/x.ts"],["user_ui"],"critical")
    ids2=[x["id"] for x in p2["checks"]]
    assert "all-tests" in ids2
    print("PASS: verification-plan self-test")

def main():
    ap=argparse.ArgumentParser(description="Compile targeted repository-native checks for changed Gearbox consequence surfaces.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--catalog")
    ap.add_argument("--path",action="append",default=[])
    ap.add_argument("--surface",action="append",default=[])
    ap.add_argument("--profile",choices=sorted(PROFILE_RANK),default="standard")
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.catalog: ap.error("--catalog is required")
    catalog=json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    result=compile_plan(catalog,args.path,args.surface,args.profile)
    text=json.dumps(result,indent=2)+"\n"
    if args.output: Path(args.output).write_text(text,encoding="utf-8")
    print(text,end=""); return 0

if __name__=="__main__":
    raise SystemExit(main())
