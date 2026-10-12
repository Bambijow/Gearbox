#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from collections import deque
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

def inspect_deps(path:Path,root:Path)->tuple[set[Path],list[str]]:
    """A conservative local-source scan, not a JS/TS build-system resolver."""
    text=path.read_text(encoding="utf-8",errors="replace")
    out=set(); unresolved=[]
    suffix=path.suffix.casefold()
    if suffix in JS_EXTS:
        specs={spec for pattern in JS_PATTERNS for spec in pattern.findall(text)}
        for spec in sorted(specs):
            matches=_candidate_files(path,spec,root) if spec.startswith(".") else []
            safe=[p.resolve() for p in matches if root in p.resolve().parents]
            if not safe:
                unresolved.append(spec)
            out.update(safe)
        calls=re.findall(r"\b(?:import|require)\s*\((.*?)\)",text,re.S)
        for arg in calls:
            if not re.fullmatch(r"\s*['\"][^'\"]+['\"]\s*",arg):
                unresolved.append("dynamic import/require expression")
        if re.search(r"import\.meta|require\.context|@(?:use|forward)\b|\burl\s*\(",text):
            unresolved.append("bundler or stylesheet dependency requires explicit resolution")
    elif suffix==".py":
        try:
            tree=ast.parse(text,filename=str(path))
        except SyntaxError:
            return set(),["Python source could not be parsed"]
        for node in ast.walk(tree):
            modules=[]
            if isinstance(node,ast.Import):
                modules=[alias.name for alias in node.names]
            elif isinstance(node,ast.ImportFrom):
                module="."*node.level+(node.module or "")
                if node.module:
                    modules=[module]
                    # Imported names may be submodules rather than attributes.
                    for alias in node.names:
                        if alias.name!="*":
                            out.update(resolve_python_module(path,module+"."+alias.name,root))
                else:
                    modules=[module+alias.name for alias in node.names if alias.name!="*"]
                    if any(alias.name=="*" for alias in node.names):
                        unresolved.append("relative wildcard import")
            elif isinstance(node,ast.Call):
                fn=node.func
                if (isinstance(fn,ast.Name) and fn.id in {"__import__","eval","exec"}) or (isinstance(fn,ast.Attribute) and fn.attr in {"import_module","spec_from_file_location"}):
                    unresolved.append("dynamic Python dependency")
            for module in modules:
                matches=resolve_python_module(path,module,root)
                if not matches:
                    unresolved.append(module)
                out.update(matches)
        # Importing a module also executes the package initializers on its path.
        for dep in list(out)+[path]:
            for parent in dep.parents:
                if parent==root or root not in parent.parents:
                    break
                init=parent/"__init__.py"
                if init.is_file():
                    out.add(init.resolve())
    else:
        unresolved.append("unsupported source type: "+(suffix or "<none>"))
    safe=set()
    for dep in out:
        if root in dep.resolve().parents:
            safe.add(dep.resolve())
        else:
            unresolved.append("dependency escapes repository")
    return safe,sorted(set(unresolved))


def dependency_closure(root:Path,entries:list[str],extras:list[str],max_depth:int)->dict:
    root=root.resolve()
    if not entries:
        raise SystemExit("at least one entry is required")
    if max_depth<0:
        raise SystemExit("max_depth must be non-negative")
    queue=deque(); entry_paths=[]
    for raw in sorted(set(entries)):
        p=(root/raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not p.is_file(): raise SystemExit(f"entry missing: {raw}")
        if root not in p.parents: raise SystemExit(f"entry escapes repo: {raw}")
        queue.append((p,0)); entry_paths.append(p)
    deps=set(entry_paths); edges=[]; seen=set(); unresolved=[]; truncated=[]
    while queue:
        path,depth=queue.popleft()
        if path in seen:
            continue
        seen.add(path)
        local,missing=inspect_deps(path,root)
        source=str(path.relative_to(root))
        unresolved.extend({"from":source,"import":name} for name in missing)
        for dep in sorted(local):
            edges.append({"from":source,"to":str(dep.relative_to(root))})
            if dep not in deps:
                if depth>=max_depth:
                    truncated.append({"from":source,"to":str(dep.relative_to(root))})
                else:
                    deps.add(dep); queue.append((dep,depth+1))
    missing_extras=[]
    for raw in sorted(set(extras)):
        p=(root/raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not p.is_file() or root not in p.parents:
            missing_extras.append(raw)
        else:
            deps.add(p)
    complete=not (unresolved or truncated or missing_extras)
    return {
        "schema_version":2,
        "entries":[str(p.relative_to(root)) for p in entry_paths],
        "dependencies":sorted(str(p.relative_to(root)) for p in deps),
        "edges":sorted(edges,key=lambda edge:(edge["from"],edge["to"])),
        "max_depth":max_depth,
        "complete":complete,
        "unresolved_imports":unresolved,
        "depth_limit_hit":bool(truncated),
        "truncated_edges":truncated,
        "missing_extras":missing_extras,
        "reuse_basis":"scope_fingerprint" if complete else "exact_sha",
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
