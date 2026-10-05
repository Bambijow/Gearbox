#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from redact import redact_text

TEXT_SUFFIXES={".json",".jsonl",".yaml",".yml",".md",".txt",".log",".diff",".patch"}
DEFAULT_NAMES={
    "state.json","dag.yaml","evidence.json","learning-candidates.md",
    "pr-technical-report.md","pr-body.md","spec.md","repo-facts.md"
}

def bundle(run: Path, out: Path, max_file: int=500_000, max_total: int=5_000_000, make_zip: bool=False) -> dict:
    run=run.resolve()
    out=out.resolve()
    if not run.exists():
        raise SystemExit(f"run directory missing: {run}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    copied=[]
    skipped=[]
    total=0
    candidates=[]
    for p in run.rglob("*"):
        if not p.is_file() or p.is_symlink():
            continue
        rel=p.relative_to(run)
        if p.name in DEFAULT_NAMES or "tasks" in rel.parts or "research" in rel.parts:
            if p.suffix.lower() in TEXT_SUFFIXES or p.name in DEFAULT_NAMES:
                candidates.append(p)
    for p in sorted(candidates):
        rel=p.relative_to(run)
        size=p.stat().st_size
        if size>max_file or total+size>max_total:
            skipped.append({"path":str(rel),"reason":"size-limit","bytes":size})
            continue
        raw=p.read_text(encoding="utf-8",errors="replace")
        clean=redact_text(raw)
        dest=out/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(clean,encoding="utf-8")
        total+=len(clean.encode("utf-8"))
        copied.append(str(rel))
    manifest={
        "source_run":run.name,
        "copied":copied,
        "skipped":skipped,
        "redacted":True,
        "bytes":total,
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    (out/"README.md").write_text(
        "# Gearbox forensic bundle\n\n"
        "Generated from a Gearbox run for retrospective/debugging. Text artifacts were passed through Gearbox secret redaction. "
        "Redaction is defense-in-depth: review this bundle before sharing it outside the repository boundary.\n",
        encoding="utf-8",
    )
    if make_zip:
        manifest["archive"]=shutil.make_archive(str(out),"zip",root_dir=out)
    return manifest

def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        run=root/"runs"/"issue-1"
        (run/"tasks"/"T1").mkdir(parents=True)
        (run/"state.json").write_text('{"token":"supersecretvalue"}\n',encoding="utf-8")
        (run/"tasks"/"T1"/"worker.log").write_text(
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz\n",encoding="utf-8"
        )
        out=root/"diagnostics"/"issue-1"
        manifest=bundle(run,out)
        if "supersecretvalue" in (out/"state.json").read_text(encoding="utf-8"):
            raise SystemExit("FAIL: bundle did not redact secret")
        if not manifest["copied"]:
            raise SystemExit("FAIL: bundle copied nothing")
    print("PASS: retro-bundle self-test")

def main() -> int:
    ap=argparse.ArgumentParser(description="Build a redacted Gearbox forensic bundle from one run.")
    ap.add_argument("--run-dir",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--zip",action="store_true")
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:
        self_test()
        return 0
    if not a.run_dir:
        ap.error("--run-dir is required")
    out=a.out or (a.run_dir.parent.parent/"diagnostics"/a.run_dir.name)
    gear=out.parent.parent if out.parent.name=="diagnostics" else None
    if gear and gear.name==".gearbox":
        gi=gear/".gitignore"
        old=gi.read_text(encoding="utf-8") if gi.exists() else ""
        if "diagnostics/" not in old.splitlines():
            gi.parent.mkdir(parents=True,exist_ok=True)
            gi.write_text(
                old + ("" if not old or old.endswith("\n") else "\n") + "diagnostics/\n",
                encoding="utf-8",
            )
    print(json.dumps(bundle(a.run_dir,out,make_zip=a.zip),indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
