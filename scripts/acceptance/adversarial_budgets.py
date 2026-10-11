"""Measure owned storage budgets; this is an inventory, not an OS quota."""
import argparse
import json
import os
from pathlib import Path
import platform
import time
from adversarial_process import ROOT,DOC,RAW

def measure(root,limit):
    start=time.monotonic()
    total=files=links=0
    if not root.exists(): return dict(bytes=0,files=0,links=0,exists=False)
    for directory,folders,names in os.walk(root,followlinks=False):
        retained=[]
        for name in folders:
            path=Path(directory)/name
            if path.is_symlink() or getattr(path,'is_junction',lambda:False)(): links+=1
            else: retained.append(name)
        folders[:]=retained
        for name in names:
            if time.monotonic()-start>60: raise RuntimeError('Storage inventory deadline')
            path=Path(directory)/name
            if path.is_symlink(): links+=1; continue
            files+=1
            total+=path.stat().st_size
            if files>100000: raise RuntimeError('Storage inventory entry bound')
            if total>limit: raise RuntimeError('Owned storage budget exceeded: '+str(root))
    return dict(bytes=total,files=files,links=links,exists=True,seconds=round(time.monotonic()-start,3))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--runtime',type=Path)
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    if not args.project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.project):
        raise RuntimeError('Invalid project identity')
    app=args.runtime or ROOT/'.cache/ten-new-project-apps'/args.project
    owner=json.loads((app/'task-owned.json').read_text(encoding='utf-8'))
    if owner.get('workspace')!=str(ROOT) or owner.get('project')!=args.project:
        raise RuntimeError('Budget inventory refuses unowned application')
    fixtures={}
    config=json.loads((DOC/args.project/'scenarios.json').read_text(encoding='utf-8'))
    names={config.get('fixture','fixtures'),*[case.get('fixture',config.get('fixture','fixtures')) for case in config['cases']]}
    for name in names:
        path=(DOC/args.project/name).resolve()
        path.relative_to((DOC/args.project).resolve())
        fixtures[name]=measure(path,64*1024*1024)
    result=dict(project=args.project,label=args.label,host=platform.platform(),
        target=measure(app,4*1024*1024*1024),raw_evidence=measure(RAW/args.project,128*1024*1024),fixtures=fixtures,
        scope='Inventory at this checkpoint; symlinks not followed, not a disk quota or peak resource measurement')
    output=RAW/args.project/('budget-'+args.label+'-'+platform.system()+'.json')
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
