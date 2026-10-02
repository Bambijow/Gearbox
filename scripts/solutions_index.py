#!/usr/bin/env python3
from __future__ import annotations
import argparse,re
from pathlib import Path

def fm(text):
 if not text.startswith('---\n'): return {}
 try: b=text.split('---\n',2)[1]
 except: return {}
 out={}
 for line in b.splitlines():
  if ':' not in line: continue
  k,v=line.split(':',1); v=v.strip()
  if v.startswith('[') and v.endswith(']'): out[k.strip()]=[x.strip().strip('"\'') for x in v[1:-1].split(',') if x.strip()]
  else: out[k.strip()]=v.strip('"\'')
 return out

def title(text,p):
 m=re.search(r'^#\s+(.+)$',text,re.M); return m.group(1).strip() if m else p.stem

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--dir',default='docs/solutions'); args=ap.parse_args(); d=Path(args.dir); d.mkdir(parents=True,exist_ok=True)
 rows=[]
 for p in sorted(d.glob('*.md')):
  if p.name.lower() in {'index.md','readme.md'}: continue
  t=p.read_text(encoding='utf-8'); f=fm(t); tags=f.get('tags',[]); areas=f.get('areas',[]); last=f.get('last_verified','')
  if isinstance(tags,str): tags=[tags]
  if isinstance(areas,str): areas=[areas]
  rows.append((str(f.get('title') or title(t,p)), ', '.join(tags), ', '.join(areas), p.name, str(last)))
 out=['# Solution index','','Current active engineering memory. Generated/maintained by Gearbox.','', '| Solution | Tags | Areas | Last verified |','|---|---|---|---|']
 for ttl,tags,areas,name,last in rows: out.append(f'| [{ttl}]({name}) | {tags} | {areas} | {last} |')
 (d/'index.md').write_text('\n'.join(out)+'\n',encoding='utf-8'); print(f'wrote {d/"index.md"} ({len(rows)} entries)')
if __name__=='__main__': main()
