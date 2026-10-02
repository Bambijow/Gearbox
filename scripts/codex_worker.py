#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEMAS={"implementation":ROOT/'references/codex-implementation-result.schema.json',"review":ROOT/'references/codex-review-result.schema.json'}
REQUIRED={"implementation":{"status","summary","changed_files","verification","risks","notes"},"review":{"status","summary","findings","verification_gaps","residual_risks"}}
def die(m,c=2): print('codex-worker:',m,file=sys.stderr); raise SystemExit(c)
def main():
 p=argparse.ArgumentParser(description='Run one isolated stateless Codex worker.'); p.add_argument('--worktree',required=True,type=Path); p.add_argument('--prompt',required=True,type=Path); p.add_argument('--result',required=True,type=Path); p.add_argument('--events',type=Path); p.add_argument('--meta',type=Path); p.add_argument('--kind',choices=('implementation','review'),default='implementation'); p.add_argument('--schema',type=Path); p.add_argument('--codex-bin',default='codex'); p.add_argument('--sandbox',choices=('workspace-write','read-only')); p.add_argument('--model'); p.add_argument('--effort',choices=('none','minimal','low','medium','high','xhigh','max')); p.add_argument('--ignore-user-config',action='store_true'); a=p.parse_args()
 wt=a.worktree.resolve(); prompt=a.prompt.resolve(); result=a.result.resolve(); schema=(a.schema or SCHEMAS[a.kind]).resolve(); events=(a.events or result.with_suffix('.events.jsonl')).resolve(); meta=(a.meta or result.with_suffix('.meta.json')).resolve(); sandbox=a.sandbox or ('read-only' if a.kind=='review' else 'workspace-write')
 if not wt.is_dir(): die(f'worktree does not exist: {wt}')
 if not prompt.is_file(): die(f'prompt file does not exist: {prompt}')
 if not schema.is_file(): die(f'schema file does not exist: {schema}')
 if shutil.which(a.codex_bin) is None: die(f'Codex CLI not found on PATH: {a.codex_bin}')
 result.parent.mkdir(parents=True,exist_ok=True); events.parent.mkdir(parents=True,exist_ok=True); meta.parent.mkdir(parents=True,exist_ok=True)
 cmd=[a.codex_bin,'exec','--ephemeral','--json','--sandbox',sandbox,'-C',str(wt),'--output-schema',str(schema),'--output-last-message',str(result)]
 if a.ignore_user_config: cmd.append('--ignore-user-config')
 if a.model: cmd += ['--model',a.model]
 if a.effort: cmd += ['--config',f'model_reasoning_effort="{a.effort}"']
 cmd.append('-')
 metadata={"kind":a.kind,"requested_model":a.model or 'default',"requested_effort":a.effort or 'default',"sandbox":sandbox,"started_at":int(time.time()),"effective_effort_verified":False}
 meta.write_text(json.dumps(metadata,indent=2)+"\n")
 with events.open('w',encoding='utf-8') as ev:
  proc=subprocess.run(cmd,input=prompt.read_text(encoding='utf-8'),text=True,stdout=ev,stderr=subprocess.PIPE,cwd=wt,check=False)
 metadata['finished_at']=int(time.time()); metadata['exit_code']=proc.returncode; meta.write_text(json.dumps(metadata,indent=2)+"\n")
 if proc.stderr: sys.stderr.write(proc.stderr)
 if proc.returncode!=0: die(f'Codex exited with status {proc.returncode}',proc.returncode)
 if not result.is_file(): die(f'Codex completed without writing result: {result}')
 try: payload=json.loads(result.read_text(encoding='utf-8'))
 except Exception as e: die(f'result is not valid JSON: {e}')
 missing=sorted(REQUIRED[a.kind].difference(payload))
 if missing: die(f"{a.kind} result missing required keys: {', '.join(missing)}")
 print(json.dumps(payload,indent=2,ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
