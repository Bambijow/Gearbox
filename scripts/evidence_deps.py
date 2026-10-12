#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

JS_EXTS=[".ts",".tsx",".js",".jsx",".mjs",".cjs",".css",".scss",".sass",".less"]
PY_EXTS=[".py"]

JS_PATTERNS=[
    re.compile(r"""(?:import|export)\s+(?:[^'"]*?\s+from\s+)?['"]([^'"]+)['"]"""),
    re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""import\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""@import\s+(?:url\()?['"]([^'"]+)['"]"""),
]
PY_FROM=re.compile(r"^\s*from\s+([.\w]+)\s+import\s+",re.M)
PY_IMPORT=re.compile(r"^\s*import\s+([.\w]+)",re.M)

def _candidate_files(base:Path,spec:str,root:Path)->list[Path]:
    out=[]
    if spec.startswith("."):
        target=(base.parent/spec).resolve()
        candidates=[target]
        if target.suffix=="":
            candidates += [Path(str(target)+ext) for ext in JS_EXTS+PY_EXTS]
            candidates += [target/("index"+ext) for ext in JS_EXTS]
            candidates += [target/"__init__.py"]
        out.extend(candidates)
    return [p for p in out if p.is_file() and (root in p.parents or p==root)]

def js_deps(path:Path,root:Path)->set[Path]:
    text=path.read_text(encoding="utf-8",errors="ignore")
    out=set()
    for pattern in JS_PATTERNS:
        for spec in pattern.findall(text):
            if not spec.startswith("."): continue
            for p in _candidate_files(path,spec,root):
                if p.exists(): out.add(p.resolve())
    return out

def resolve_python_module(path:Path,module:str,root:Path)->list[Path]:
    if module.startswith("."):
        dots=len(module)-len(module.lstrip("."))
        rest=module[dots:]
        base=path.parent
        for _ in range(max(0,dots-1)): base=base.parent
        target=base/Path(*([x for x in rest.split(".") if x]))
    else:
        target=root/Path(*module.split("."))
    candidates=[target.with_suffix(".py"),target/"__init__.py"]
    return [p.resolve() for p in candidates if p.is_file()]

def python_deps(path:Path,root:Path)->set[Path]:
    text=path.read_text(encoding="utf-8",errors="ignore")
    out=set()
    for mod in PY_FROM.findall(text):
        out.update(resolve_python_module(path,mod,root))
    for mod in PY_IMPORT.findall(text):
        out.update(resolve_python_module(path,mod,root))
    return out

def direct_deps(path:Path,root:Path)->set[Path]:
    if path.suffix.casefold() in JS_EXTS:
        return js_deps(path,root)
    if path.suffix.casefold()==".py":
        return python_deps(path,root)
    return set()

def dependency_closure(root:Path,entries:list[str],extras:list[str],max_depth:int)->dict:
    root=root.resolve()
    queue=[]
    entry_paths=[]
    for raw in entries:
        p=(root/raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not p.is_file(): raise SystemExit(f"entry missing: {raw}")
        if root not in p.parents and p!=root: raise SystemExit(f"entry escapes repo: {raw}")
        queue.append((p,0)); entry_paths.append(p)
    deps=set(entry_paths)
    edges=[]
    seen=set()
    while queue:
        path,depth=queue.pop(0)
        if path in seen or depth>=max_depth: continue
        seen.add(path)
        for dep in sorted(direct_deps(path,root)):
            if root not in dep.parents and dep!=root: continue
            edges.append({"from":str(path.relative_to(root)),"to":str(dep.relative_to(root))})
            if dep not in deps:
                deps.add(dep); queue.append((dep,depth+1))
    for raw in extras:
        p=(root/raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if p.is_file() and (root in p.parents or p==root): deps.add(p)
    return {
        "schema_version":1,
        "entries":[str(p.relative_to(root)) for p in entry_paths],
        "dependencies":sorted(str(p.relative_to(root)) for p in deps),
        "edges":edges,
        "max_depth":max_depth,
    }

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        (root/"src").mkdir()
        (root/"src"/"tokens.ts").write_text("export const x=1")
        (root/"src"/"Button.tsx").write_text("import {x} from './tokens'\nexport const B=x")
        (root/"src"/"Page.tsx").write_text("import {B} from './Button'\nexport const P=B")
        r=dependency_closure(root,["src/Page.tsx"],[],5)
        assert set(r["dependencies"])=={"src/Page.tsx","src/Button.tsx","src/tokens.ts"}
        (root/"pkg").mkdir()
        (root/"pkg"/"util.py").write_text("X=1")
        (root/"pkg"/"main.py").write_text("from .util import X")
        r2=dependency_closure(root,["pkg/main.py"],[],5)
        assert "pkg/util.py" in r2["dependencies"]
    print("PASS: evidence-deps self-test")

def main():
    ap=argparse.ArgumentParser(description="Derive a bounded local dependency closure for scoped Gearbox evidence fingerprints.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--repo-root",default=".")
    ap.add_argument("--entry",action="append",default=[])
    ap.add_argument("--extra",action="append",default=[])
    ap.add_argument("--max-depth",type=int,default=8)
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.entry: ap.error("at least one --entry is required")
    result=dependency_closure(Path(args.repo_root),args.entry,args.extra,args.max_depth)
    text=json.dumps(result,indent=2)+"\n"
    if args.output: Path(args.output).write_text(text,encoding="utf-8")
    print(text,end=""); return 0

if __name__=="__main__":
    raise SystemExit(main())
