#!/usr/bin/env python3
"""Task-owned native Linux Python environments; no global installs."""
import argparse,json,subprocess,hashlib,shutil,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('mode',choices=['acquire','install','measure','remove']);p.add_argument('application');a=p.parse_args()
app=ROOT/'.cache/ten-project-apps'/a.application
owner=json.loads((app/'task-owned.json').read_text())
if owner['created_by']!='ten-project-user-pass':raise SystemExit('Unknown ownership')
runtime=Path('/var/tmp')/('playtestr-user-pass-'+a.application)
raw=ROOT/'artifacts/ten-project-user-pass'/owner['project'];raw.mkdir(parents=True,exist_ok=True)
uv=ROOT/'.tools/ten-project-runtime/uv-x86_64-unknown-linux-gnu/uv'
if a.mode in ('acquire','install'):
 if runtime.exists():
  if json.loads((runtime/'task-owned.json').read_text())!=dict(workspace=str(ROOT),application=a.application):raise SystemExit('Unknown runtime ownership')
 else:
  runtime.mkdir();(runtime/'task-owned.json').write_text(json.dumps(dict(workspace=str(ROOT),application=a.application)))
 if a.mode=='acquire':
  source=runtime/'source'
  if source.exists():raise SystemExit('Refuse existing native source')
  with (raw/'native-acquisition.log').open('w') as log:
   subprocess.run(['git','clone','--filter=blob:none','--no-checkout','https://github.com/'+owner['repo']+'.git',str(source)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
   subprocess.run(['git','-C',str(source),'checkout','--detach',owner['sha']],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
  (app/'native-source.json').write_text(json.dumps(dict(path=str(source))))
  print('Acquired pinned source on native Linux filesystem',source);raise SystemExit(0)
 if (runtime/'venv').exists():raise SystemExit('Refuse existing installed environment')
 source=Path(json.loads((app/'native-source.json').read_text())['path']) if (app/'native-source.json').exists() else app/'source'
 env=dict(os.environ,UV_CACHE_DIR=str(runtime/'cache'))
 constraints=ROOT/'docs/validation/ten-project-user-pass'/owner['project']/'dependency-constraints.txt'
 constraint_args=['--constraint',str(constraints)] if constraints.exists() else []
 with (raw/'native-python-install.log').open('w') as log:
  for command in [[str(uv),'venv','--python','/usr/bin/python3',str(runtime/'venv')],[str(uv),'pip','install','--python',str(runtime/'venv/bin/python'),*constraint_args,str(source)]]:
   subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
  subprocess.run([str(uv),'pip','freeze','--python',str(runtime/'venv/bin/python')],env=env,stdout=log,check=True,timeout=30)
 freeze=subprocess.check_output([str(uv),'pip','freeze','--python',str(runtime/'venv/bin/python')],env=env,text=True,timeout=30)
 if not constraints.exists():constraints.write_text('\n'.join(line for line in freeze.splitlines() if ' @ ' not in line)+'\n')
 digest=hashlib.sha256();count=0
 for file in sorted((runtime/'venv').rglob('*')):
  if not file.is_file() or file.is_symlink() or '__pycache__' in file.parts or file.suffix=='.pyc':continue
  digest.update(str(file.relative_to(runtime/'venv')).encode());digest.update(b'\0')
  with file.open('rb') as stream:
   for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
  count+=1
 (raw/'installed-target-identity.json').write_text(json.dumps(dict(source_sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),files=count,installed_tree_sha256=digest.hexdigest(),dependencies=freeze.splitlines()),indent=2)+'\n')
 (app/'native-runtime.json').write_text(json.dumps(dict(path=str(runtime),project=owner['project'],workspace=str(ROOT))))
 print('Installed actual source into owned native runtime',runtime,flush=True)
elif a.mode=='measure':
 start=time.monotonic();result=subprocess.run([str(app/'.venv/bin/vd'),'--version'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 (raw/'mounted-python-startup.json').write_text(json.dumps(dict(seconds=time.monotonic()-start,exit=result.returncode,output=result.stdout.decode('utf-8')),indent=2)+'\n')
 print('Measured mounted startup',time.monotonic()-start)
else:
 if runtime.resolve().parent!=Path('/var/tmp') or not runtime.name.startswith('playtestr-user-pass-'):raise SystemExit('Unsafe target')
 if json.loads((runtime/'task-owned.json').read_text())!=dict(workspace=str(ROOT),application=a.application):raise SystemExit('Ownership mismatch')
 for item in Path('/proc').iterdir():
  if not item.name.isdigit() or int(item.name)==os.getpid():continue
  try:
   args=(item/'cmdline').read_bytes().decode(errors='replace').split('\0')
   if any(v.startswith(str(runtime)+'/') for v in args) or str((item/'cwd').resolve()).startswith(str(runtime)+'/'):raise SystemExit('Live runtime process '+item.name)
  except (OSError,PermissionError):pass
 shutil.rmtree(runtime)
 print('Removed verified task-owned native runtime',runtime)
