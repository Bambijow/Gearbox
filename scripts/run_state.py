#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, socket, subprocess, sys, time
from pathlib import Path

SCHEMA_VERSION=3
DEFAULT_BUDGETS={"max_cycles":3,"max_worker_dispatches":10,"max_codex_dispatches":12,"max_review_dispatches":14,"max_model_escalations":3,"max_pr_repair_cycles":3}

def load(p): return json.loads(p.read_text()) if p.exists() else None
def save(p,d): p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix('.tmp'); tmp.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); os.replace(tmp,p)
def state_path(run): return Path(run)/'state.json'
def die(msg,code=2): print('run-state:',msg,file=sys.stderr); raise SystemExit(code)

def normalize(d):
 changed=False
 if d.get('schema_version',1)<SCHEMA_VERSION: d['schema_version']=SCHEMA_VERSION; changed=True
 if 'clarification' not in d: d['clarification']={"status":"UNSET","round":0,"questions":[],"answers":{}}; changed=True
 if 'blocker' not in d: d['blocker']=None; changed=True
 if 'orchestration' not in d: d['orchestration']={'mode':'delegated-control-plane','product_writes':'workers-only'}; changed=True
 d.setdefault('budgets',{})
 for k,v in DEFAULT_BUDGETS.items():
  if k not in d['budgets']: d['budgets'][k]=v; changed=True
 d.setdefault('usage',{})
 for k in ['worker_dispatches','codex_dispatches','review_dispatches','model_escalations','pr_repair_cycles']:
  if k not in d['usage']: d['usage'][k]=0; changed=True
 return d,changed

def init(run, run_id):
 p=state_path(run)
 if p.exists():
  d=load(p); d,changed=normalize(d)
  if changed: d['updated_at']=int(time.time()); save(p,d)
  return d
 d={"schema_version":SCHEMA_VERSION,"run_id":run_id,"status":"ACTIVE","phase":"INTAKE","cycle":0,"source":{},"git":{"base_sha":None,"head_sha":None,"branch":None},"github":{"issue":None,"pr":None,"technical_comment_id":None},"completed":{},"pending":[],"worktrees":[],"budgets":DEFAULT_BUDGETS.copy(),"usage":{"worker_dispatches":0,"codex_dispatches":0,"review_dispatches":0,"model_escalations":0,"pr_repair_cycles":0},"model_policy":{},"model_assignments":{},"orchestration":{"mode":"delegated-control-plane","product_writes":"workers-only"},"clarification":{"status":"UNSET","round":0,"questions":[],"answers":{}},"blocker":None,"learning":{},"last_error":None,"updated_at":int(time.time())}
 save(p,d); return d

def read_json_file(path):
 try: return json.loads(Path(path).read_text())
 except Exception as e: die(f'cannot read JSON file {path}: {e}')

def main():
 ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
 a=sp.add_parser('init'); a.add_argument('--run-dir',required=True); a.add_argument('--run-id',required=True)
 a=sp.add_parser('show'); a.add_argument('--run-dir',required=True)
 a=sp.add_parser('transition'); a.add_argument('--run-dir',required=True); a.add_argument('--phase',required=True); a.add_argument('--status'); a.add_argument('--cycle',type=int)
 a=sp.add_parser('set'); a.add_argument('--run-dir',required=True); a.add_argument('--key',required=True); a.add_argument('--json',required=True)
 a=sp.add_parser('consume'); a.add_argument('--run-dir',required=True); a.add_argument('--kind',choices=['worker','codex','review','model-escalation','pr-repair'],required=True); a.add_argument('--count',type=int,default=1)
 a=sp.add_parser('lock'); a.add_argument('--run-dir',required=True); a.add_argument('--break-stale',action='store_true'); a.add_argument('--stale-seconds',type=int,default=21600)
 a=sp.add_parser('unlock'); a.add_argument('--run-dir',required=True)
 a=sp.add_parser('cleanup-worktrees'); a.add_argument('--run-dir',required=True); a.add_argument('--repo',default='.')
 a=sp.add_parser('spec-block'); a.add_argument('--run-dir',required=True); a.add_argument('--clarification-file',required=True); a.add_argument('--message',default='Material product decisions are required before planning')
 a=sp.add_parser('spec-resolve'); a.add_argument('--run-dir',required=True); a.add_argument('--answers-file',required=True)
 args=ap.parse_args(); run=Path(args.run_dir); p=state_path(run)
 if args.cmd=='init': d=init(run,args.run_id); print(json.dumps(d,indent=2)); return
 if not p.exists(): die('state.json missing; run init first')
 d=load(p); d,changed=normalize(d)
 if changed: d['updated_at']=int(time.time()); save(p,d)
 if args.cmd=='show': print(json.dumps(d,indent=2,sort_keys=True)); return
 if args.cmd=='lock':
  lp=run/'.lock'; run.mkdir(parents=True,exist_ok=True)
  if lp.exists():
   try: old=json.loads(lp.read_text()); age=time.time()-old.get('created_at',time.time())
   except Exception: old={}; age=0
   owner_alive=False
   if old.get('host')==socket.gethostname() and isinstance(old.get('pid'),int):
    try: os.kill(old['pid'],0); owner_alive=True
    except (ProcessLookupError,PermissionError): owner_alive=False
   if not (args.break_stale and age>args.stale_seconds and not owner_alive): die(f"lock exists: {old}",3)
   lp.unlink()
  fd=os.open(lp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600); meta={"pid":os.getpid(),"host":socket.gethostname(),"created_at":time.time()}; os.write(fd,json.dumps(meta).encode()); os.close(fd); print(json.dumps(meta)); return
 if args.cmd=='unlock':
  lp=run/'.lock'; lp.unlink(missing_ok=True); return
 if args.cmd=='cleanup-worktrees':
  repo=Path(args.repo).resolve(); kept=[]; removed=[]
  for wt in d.get('worktrees',[]):
   path=Path(wt.get('path',''))
   if not path.exists(): continue
   integrated=bool(wt.get('integrated'))
   clean=subprocess.run(['git','-C',str(path),'status','--porcelain'],capture_output=True,text=True,check=False).stdout.strip()==''
   if not (integrated or clean): kept.append(wt); continue
   proc=subprocess.run(['git','-C',str(repo),'worktree','remove','--force',str(path)],capture_output=True,text=True,check=False)
   if proc.returncode==0: removed.append(str(path))
   else: kept.append(wt)
  d['worktrees']=kept; d['updated_at']=int(time.time()); save(p,d); print(json.dumps({'removed':removed,'kept':kept},indent=2)); return
 if args.cmd=='spec-block':
  clarification=read_json_file(args.clarification_file)
  questions=clarification.get('questions',[])
  if not questions: die('spec-block requires at least one unresolved question')
  clarification['status']='NEEDS_INPUT'
  clarification['round']=max(int(clarification.get('round',0)), int(d.get('clarification',{}).get('round',0))+1)
  clarification.setdefault('answers',{})
  d['phase']='SPEC'; d['status']='BLOCKED'; d['clarification']=clarification
  d['blocker']={'code':'SPEC_BLOCKED','message':args.message}
  d['pending']=[f"clarification:{q.get('id','unknown')}" for q in questions]
 elif args.cmd=='spec-resolve':
  if not (d.get('blocker') or {}).get('code')=='SPEC_BLOCKED': die('run is not SPEC_BLOCKED')
  answers=read_json_file(args.answers_file)
  current=d.get('clarification',{})
  qids={q.get('id') for q in current.get('questions',[]) if q.get('id')}
  supplied=set(answers.keys())
  missing=sorted(qids-supplied)
  if missing: die(f'missing answers for: {missing}')
  current['answers']=answers; current['status']='ANSWERED'
  d['clarification']=current; d['blocker']=None; d['status']='ACTIVE'; d['phase']='SPEC'; d['pending']=[]
 elif args.cmd=='transition':
  d['phase']=args.phase
  if args.status: d['status']=args.status
  if args.cycle is not None: d['cycle']=args.cycle
 elif args.cmd=='set':
  cur=d; parts=args.key.split('.')
  for k in parts[:-1]: cur=cur.setdefault(k,{})
  cur[parts[-1]]=json.loads(args.json)
 elif args.cmd=='consume':
  if d.get('status')=='BLOCKED' and (d.get('blocker') or {}).get('code')=='SPEC_BLOCKED' and args.kind in ('worker','codex','review','model-escalation'):
   die('cannot consume implementation/model/review budget while SPEC_BLOCKED',5)
  mapping={'worker':('worker_dispatches','max_worker_dispatches'),'codex':('codex_dispatches','max_codex_dispatches'),'review':('review_dispatches','max_review_dispatches'),'model-escalation':('model_escalations','max_model_escalations'),'pr-repair':('pr_repair_cycles','max_pr_repair_cycles')}
  uk,bk=mapping[args.kind]; new=d['usage'].get(uk,0)+args.count; limit=d['budgets'].get(bk)
  if limit is not None and new>limit: die(f'budget exceeded: {uk} {new}>{limit}',4)
  d['usage'][uk]=new
 d['updated_at']=int(time.time()); save(p,d); print(json.dumps(d,indent=2))
if __name__=='__main__': main()
