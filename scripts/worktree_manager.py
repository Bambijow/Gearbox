#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path


def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if p.returncode:
        print(p.stderr or p.stdout, file=sys.stderr)
        raise SystemExit(p.returncode)
    return p.stdout.strip()


def git_value(repo, *parts):
    p=subprocess.run(['git','-C',str(repo),*parts],capture_output=True,text=True,check=False)
    if p.returncode: raise ValueError(p.stderr.strip() or 'invalid git repository')
    return p.stdout.strip()

def verify_repo(repo, expected):
    actual=Path(git_value(repo,'rev-parse','--show-toplevel')).resolve()
    expected_root=Path(git_value(expected,'rev-parse','--show-toplevel')).resolve()
    actual_common=Path(git_value(repo,'rev-parse','--path-format=absolute','--git-common-dir')).resolve()
    expected_common=Path(git_value(expected,'rev-parse','--path-format=absolute','--git-common-dir')).resolve()
    if actual_common!=expected_common:
        raise ValueError(f'REPOSITORY_MISMATCH: {actual} != {expected_root}')
    return str(actual)

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    c=sp.add_parser('create'); c.add_argument('--repo',default='.'); c.add_argument('--path',required=True); c.add_argument('--branch',required=True); c.add_argument('--base',default='HEAD')
    r=sp.add_parser('remove'); r.add_argument('--repo',default='.'); r.add_argument('--path',required=True); r.add_argument('--force',action='store_true')
    l=sp.add_parser('list'); l.add_argument('--repo',default='.')
    for parser in (c,r): parser.add_argument('--expected-repo',required=True,help='Approved repository root recorded by the run')
    a=ap.parse_args(); repo=str(Path(a.repo).resolve())
    try:
        if a.cmd in ('create','remove'): repo=verify_repo(repo,a.expected_repo)
        else: repo=str(Path(git_value(repo,'rev-parse','--show-toplevel')).resolve())
    except ValueError as error:
        print(str(error),file=sys.stderr); raise SystemExit(7)
    if a.cmd=='create':
        path=Path(a.path).resolve(); path.parent.mkdir(parents=True,exist_ok=True)
        run(['git','-C',repo,'worktree','add','-b',a.branch,str(path),a.base])
        print(json.dumps({'path':str(path),'branch':a.branch,'base':a.base}))
    elif a.cmd=='remove':
        path=Path(a.path).resolve()
        try: verify_repo(path,a.expected_repo)
        except ValueError as error:
            print(str(error),file=sys.stderr); raise SystemExit(7)
        cmd=['git','-C',repo,'worktree','remove']
        if a.force: cmd.append('--force')
        cmd.append(str(Path(a.path).resolve())); run(cmd)
    else:
        print(run(['git','-C',repo,'worktree','list','--porcelain']))
if __name__=='__main__': main()
