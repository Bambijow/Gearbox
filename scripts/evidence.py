#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,time
from pathlib import Path

def load(p): return json.loads(p.read_text()) if p.exists() else {"schema_version":1,"items":[]}
def save(p,d): p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix('.tmp'); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); os.replace(t,p)
def main():
 ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
 a=sp.add_parser('init'); a.add_argument('--file',required=True)
 a=sp.add_parser('add'); a.add_argument('--file',required=True); a.add_argument('--kind',required=True); a.add_argument('--sha'); a.add_argument('--status',required=True); a.add_argument('--summary',required=True); a.add_argument('--command'); a.add_argument('--exit-code',type=int); a.add_argument('--path'); a.add_argument('--meta-json',default='{}')
 a=sp.add_parser('invalidate'); a.add_argument('--file',required=True); a.add_argument('--sha',required=True); a.add_argument('--reason',required=True)
 a=sp.add_parser('show'); a.add_argument('--file',required=True)
 args=ap.parse_args(); p=Path(args.file); d=load(p)
 if args.cmd=='init': save(p,d); return
 if args.cmd=='show': print(json.dumps(d,indent=2)); return
 if args.cmd=='add':
  item={"id":len(d['items'])+1,"kind":args.kind,"sha":args.sha,"status":args.status,"summary":args.summary,"created_at":int(time.time()),"valid":True}
  if args.command: item['command']=args.command
  if args.exit_code is not None: item['exit_code']=args.exit_code
  if args.path: item['path']=args.path
  item.update(json.loads(args.meta_json)); d['items'].append(item)
 else:
  for i in d['items']:
   if i.get('sha')==args.sha and i.get('valid',True): i['valid']=False; i['invalidated_reason']=args.reason
 save(p,d); print(json.dumps(d,indent=2))
if __name__=='__main__': main()
