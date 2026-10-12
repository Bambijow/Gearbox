#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import tomllib
from pathlib import Path

from redact import redact_obj

def repo_cache_root()->Path:
    base=Path(os.environ.get("XDG_CACHE_HOME",Path.home()/".cache"))/"gearbox"
    proc=subprocess.run(["git","rev-parse","--git-common-dir"],capture_output=True,text=True,check=False)
    identity=(proc.stdout.strip() if proc.returncode==0 and proc.stdout.strip() else str(Path.cwd().resolve()))
    if proc.returncode==0 and identity:
        p=Path(identity)
        if not p.is_absolute():p=(Path.cwd()/p).resolve()
        identity=str(p)
    key=hashlib.sha256(identity.encode()).hexdigest()[:16]
    return base/key/"repo-facts"

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def kind_for(path:Path)->str:
    name=path.name
    low=str(path).replace("\\","/").casefold()
    if name=="package.json":return "package-json"
    if name.startswith("tsconfig") and name.endswith(".json"):return "tsconfig-json"
    if name=="pyproject.toml":return "pyproject-toml"
    if name=="Cargo.toml":return "cargo-toml"
    if name=="go.mod":return "go-mod"
    if name.startswith("requirements") and path.suffix==".txt":return "requirements"
    if "/.github/workflows/" in "/"+low and path.suffix.casefold() in {".yml",".yaml"}:return "workflow-yaml"
    return "generic"

def extract(path:Path)->dict:
    kind=kind_for(path)
    text=path.read_text(encoding="utf-8",errors="ignore")
    facts={"kind":kind,"path":str(path),"bytes":path.stat().st_size}
    if kind=="package-json":
        d=json.loads(text)
        facts.update({
            "name":d.get("name"),
            "package_manager":d.get("packageManager"),
            "engines":d.get("engines",{}),
            "scripts":d.get("scripts",{}),
            "workspaces":d.get("workspaces"),
            "dependencies":sorted((d.get("dependencies") or {}).keys()),
            "dev_dependencies":sorted((d.get("devDependencies") or {}).keys()),
        })
    elif kind=="tsconfig-json":
        # tsconfig comments are legal-ish in practice; keep deterministic best-effort extraction.
        cleaned=re.sub(r"/\*.*?\*/","",text,flags=re.S)
        cleaned=re.sub(r"(^|\s)//.*?$",r"\1",cleaned,flags=re.M)
        try:d=json.loads(cleaned)
        except json.JSONDecodeError:
            d={}
        co=d.get("compilerOptions") or {}
        facts.update({
            "extends":d.get("extends"),
            "references":d.get("references",[]),
            "include":d.get("include",[]),
            "exclude":d.get("exclude",[]),
            "compiler_options":{
                k:co.get(k) for k in ("baseUrl","paths","module","moduleResolution","target","jsx","strict","composite") if k in co
            },
        })
    elif kind in {"pyproject-toml","cargo-toml"}:
        d=tomllib.loads(text)
        if kind=="pyproject-toml":
            project=d.get("project") or {}
            facts.update({
                "project_name":project.get("name"),
                "requires_python":project.get("requires-python"),
                "dependencies":project.get("dependencies",[]),
                "scripts":project.get("scripts",{}),
                "build_system":d.get("build-system",{}),
                "tool_sections":sorted((d.get("tool") or {}).keys()),
            })
        else:
            facts.update({
                "package":d.get("package",{}),
                "workspace":d.get("workspace",{}),
                "dependencies":sorted((d.get("dependencies") or {}).keys()),
                "dev_dependencies":sorted((d.get("dev-dependencies") or {}).keys()),
            })
    elif kind=="go-mod":
        module=re.search(r"^module\s+(.+)$",text,re.M)
        gov=re.search(r"^go\s+(.+)$",text,re.M)
        requires=re.findall(r"^\s*([\w./-]+)\s+v[^\s]+",text,re.M)
        facts.update({"module":module.group(1).strip() if module else None,"go":gov.group(1).strip() if gov else None,"requires":sorted(set(requires))})
    elif kind=="requirements":
        reqs=[ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
        facts["requirements"]=reqs
    elif kind=="workflow-yaml":
        facts.update({
            "uses":sorted(set(re.findall(r"^\s*-?\s*uses:\s*([^#\n]+)",text,re.M))),
            "run_lines":[x.strip() for x in re.findall(r"^\s*run:\s*([^#\n]+)",text,re.M)][:50],
            "job_ids":sorted(set(re.findall(r"^\s{2}([A-Za-z0-9_.-]+):\s*$",text,re.M))),
        })
    else:
        facts["line_count"]=text.count("\n")+1
    return facts

def cached_extract(path:Path,cache_root:Path)->tuple[dict,bool]:
    digest=sha256_file(path)
    key=hashlib.sha256((kind_for(path)+"\0"+digest).encode()).hexdigest()
    cp=cache_root/(key+".json")
    if cp.is_file():
        data=json.loads(cp.read_text(encoding="utf-8"))
        return data,True
    facts=redact_obj(extract(path))
    data={"schema_version":1,"sha256":digest,"facts":facts}
    cache_root.mkdir(parents=True,exist_ok=True)
    tmp=cp.with_suffix(".tmp");tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8");os.replace(tmp,cp)
    return data,False

def discover(root:Path)->list[Path]:
    patterns=[
        "package.json","tsconfig*.json","pyproject.toml","Cargo.toml","go.mod","requirements*.txt",
        ".github/workflows/*.yml",".github/workflows/*.yaml"
    ]
    out=[]
    for pattern in patterns:
        out.extend(root.glob(pattern))
    return sorted({p.resolve() for p in out if p.is_file()})

def compile_facts(root:Path,paths:list[str],auto:bool,cache_root:Path)->dict:
    root=root.resolve()
    files=discover(root) if auto else []
    for raw in paths:
        p=(root/raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if p.is_file() and p not in files:files.append(p)
    items=[];hits=0;misses=0
    for p in sorted(files):
        if root not in p.parents and p!=root:continue
        data,hit=cached_extract(p,cache_root)
        hits+=int(hit);misses+=int(not hit)
        items.append({"path":str(p.relative_to(root)),"cache_hit":hit,**data})
    return {"schema_version":1,"files":items,"cache_hits":hits,"cache_misses":misses}

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);cache=root/"cache"
        (root/"package.json").write_text(json.dumps({"name":"x","scripts":{"test":"vitest"},"dependencies":{"react":"1"}}))
        (root/"tsconfig.json").write_text(json.dumps({"compilerOptions":{"strict":True,"paths":{"@/*":["src/*"]}}}))
        first=compile_facts(root,[],True,cache)
        second=compile_facts(root,[],True,cache)
        assert first["cache_misses"]==2 and second["cache_hits"]==2
        pkg=[x for x in second["files"] if x["path"]=="package.json"][0]
        assert pkg["facts"]["scripts"]["test"]=="vitest"
    print("PASS: repo-facts-cache self-test")

def main():
    ap=argparse.ArgumentParser(description="Extract deterministic repository structural facts with per-content incremental caching.")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--repo-root",type=Path,default=Path("."))
    ap.add_argument("--path",action="append",default=[])
    ap.add_argument("--auto",action="store_true")
    ap.add_argument("--cache-dir",type=Path)
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.self_test:self_test();return 0
    cache=args.cache_dir or repo_cache_root()
    result=compile_facts(args.repo_root,args.path,args.auto,cache);text=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if args.output:Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="");return 0

if __name__=="__main__":
    raise SystemExit(main())
