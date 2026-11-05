#!/usr/bin/env python3
"""Generate deterministic repository indexes from native NEW1 artifacts."""
import argparse, datetime, hashlib, json, pathlib, struct, sys
from validate_repository import read_new

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--check',action='store_true'); a=ap.parse_args(); root=pathlib.Path(a.root).resolve(); changed=[]
 for channel in ('stable','testing'):
  for arch in ('x86_64',):
   base=root/'repository'/channel/arch; packages=[]
   for p in sorted((base/'packages').glob('*.new')):
    meta,raw=read_new(p)
    if meta.get('arch') not in (arch,'any'): raise ValueError(f'{p}: architecture mismatch')
    try: deps=[s.strip() for s in meta.get('depends','').split(',') if s.strip()]
    except Exception: deps=[]
    packages.append({'name':meta['name'],'version':meta['version'],'architecture':meta['arch'],'description':meta['desc'],'license':meta['license'],'author':meta['maintainer'],'depends':deps,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'location':'packages/'+p.name,'newos_min':meta['newos-min'],'format':'NEW1','integrity':'sha256','signature_status':'unsigned-testing-only' if channel=='testing' else 'unsigned'})
   idx=base/'index.json'; existing={}
   if idx.exists():
    try: existing=json.loads(idx.read_text())
    except json.JSONDecodeError: pass
   doc={'schema_version':1,'repository':'NEWOS '+channel,'channel':channel,'architecture':arch,'generated_at':existing.get('generated_at','2026-11-05T12:03:00-06:00'),'packages':packages}
   rendered=json.dumps(doc,indent=2,ensure_ascii=False)+'\n'
   if a.check:
    if not idx.exists() or idx.read_text()!=rendered: changed.append(str(idx))
   else: idx.parent.mkdir(parents=True,exist_ok=True); idx.write_text(rendered)
 if changed: print('index out of date: '+', '.join(changed),file=sys.stderr); return 1
 print('index generation: '+('PASS (indexes current)' if a.check else 'updated'))
 return 0
if __name__=='__main__':
 try: raise SystemExit(main())
 except Exception as e: print('index generation: FAIL: '+str(e),file=sys.stderr); raise SystemExit(1)
