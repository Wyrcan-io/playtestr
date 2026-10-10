#!/usr/bin/env python3
"""Explicit reviewed real-target mutations, never test-contract mutations."""
import argparse,json,subprocess,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('mode',choices=['apply','restore']);p.add_argument('slug');p.add_argument('name',nargs='?',default='target-regression');a=p.parse_args()
doc=ROOT/'docs/validation/ten-project-user-pass'/a.slug
m=json.loads((doc/(a.name+'.json')).read_text())
app=ROOT/'.cache/ten-project-apps'/m['application'];owner=json.loads((app/'task-owned.json').read_text())
if owner['project']!=a.slug:raise SystemExit('Unknown ownership')
source_root=Path(json.loads((app/'native-source.json').read_text())['path']) if (app/'native-source.json').exists() else app/'source'
source=source_root/m['file'];installed=Path(m['installed_file']);base=app/(a.name+'.original')
source.resolve().relative_to(source_root.resolve())
runtime=Path('/var/tmp')/('playtestr-user-pass-'+m['application'])
installed.resolve().relative_to((runtime/'venv').resolve())
if json.loads((runtime/'task-owned.json').read_text())!=dict(workspace=str(ROOT),application=m['application']):raise SystemExit('Unknown installed runtime ownership')
if a.mode=='apply':
 original=source.read_text();assert original.count(m['before'])==1
 assert installed.read_text()==original, 'Installed target differs from pinned source'
 base.write_text(original)
 changed=original.replace(m['before'],m['after']);source.write_text(changed);installed.write_text(changed)
 patch=subprocess.check_output(['git','-C',str(source_root),'diff','--',m['file']]);(doc/(a.name+'.patch')).write_bytes(patch)
else:
 original=base.read_text();source.write_text(original);installed.write_text(original)
identity=ROOT/'artifacts/ten-project-user-pass'/a.slug/'mutation-identities.json'
entries=json.loads(identity.read_text()) if identity.exists() else []
entries.append(dict(mutation=a.name,mode=a.mode,source_file_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),installed_file_sha256=hashlib.sha256(installed.read_bytes()).hexdigest()))
identity.write_text(json.dumps(entries,indent=2)+'\n')
print(a.slug,a.name,a.mode,'actual source and installed behavior',flush=True)
