#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def dotted(obj,path):
 cur=obj
 for part in path.split('.'):
  if not isinstance(cur,dict) or part not in cur: return None
  cur=cur[part]
 return cur

def main():
 ap=argparse.ArgumentParser(description='Check a Gearbox run against a scenario contract.'); ap.add_argument('scenario'); ap.add_argument('run_dir'); args=ap.parse_args()
 sc=json.loads(Path(args.scenario).read_text()); run=Path(args.run_dir); errors=[]
 st=json.loads((run/'state.json').read_text()) if (run/'state.json').exists() else None
 ev=json.loads((run/'evidence.json').read_text()) if (run/'evidence.json').exists() else {"items":[]}
 if not st: errors.append('missing state.json')
 else:
  allowed=sc.get('allowed_final_statuses')
  if allowed and st.get('status') not in allowed: errors.append(f"status {st.get('status')} not in {allowed}")
  for key,maxv in sc.get('usage_max',{}).items():
   if st.get('usage',{}).get(key,0)>maxv: errors.append(f'usage {key} exceeded {maxv}')
  for path,expected in sc.get('required_state',{}).items():
   actual=dotted(st,path)
   if actual!=expected: errors.append(f'state {path}={actual!r}, expected {expected!r}')
 kinds={i.get('kind') for i in ev.get('items',[]) if i.get('valid',True) and i.get('status') in ('PASS','passed','success','0')}
 for k in sc.get('required_evidence_kinds',[]):
  if k not in kinds: errors.append(f'missing passing evidence kind: {k}')
 # Caller-shaped evals must inspect the actual changed-path report, not just final status.
 # File format: JSON list of changed repository paths, or {"changed_paths": [...]}.
 if 'forbidden_changed_paths' in sc:
  manifest=run/sc.get('changed_paths_file','changed_paths.json')
  if not manifest.is_file(): errors.append(f'missing changed-path manifest: {manifest.name}')
  else:
   try:
    payload=json.loads(manifest.read_text())
    paths=payload.get('changed_paths') if isinstance(payload,dict) else payload
    if not isinstance(paths,list) or any(not isinstance(p,str) for p in paths):
     errors.append('invalid changed-path manifest: expected string path list')
    else:
     from fnmatch import fnmatchcase
     for pattern in sc['forbidden_changed_paths']:
      for path in paths:
       if fnmatchcase(path,pattern): errors.append(f'out-of-scope change: {path} matches {pattern}')
   except (OSError,ValueError) as exc: errors.append(f'cannot read changed-path manifest: {exc}')
 forbidden=sc.get('forbidden_product_paths',[])
 for p in forbidden:
  if (run/p).exists(): errors.append(f'forbidden run artifact exists: {p}')
 if errors:
  print('\n'.join('FAIL: '+e for e in errors)); return 1
 print('PASS:',sc.get('name',Path(args.scenario).parent.name)); return 0
if __name__=='__main__': raise SystemExit(main())
