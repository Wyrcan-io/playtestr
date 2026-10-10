"""Remove exactly one Unix owned application after qualification and process checks."""
import json
import argparse
import os
from pathlib import Path
import platform
import shutil
from adversarial_process import ROOT,RAW

parser=argparse.ArgumentParser()
parser.add_argument('--project',default='cookiecutter')
parser.add_argument('--target',type=Path)
parser.add_argument('--qualification',type=Path)
args=parser.parse_args()
project=args.project
if not project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in project):
    raise RuntimeError('Invalid owned project identity')
root=(ROOT/'.cache/ten-new-project-apps').resolve(strict=True)
target=root/project
if args.target:
    if str(args.target)!='/var/tmp/playtestr-adversarial-'+project:
        raise RuntimeError('Only the explicitly owned native exploratory root is admitted')
    root=Path('/var/tmp').resolve(strict=True)
    target=args.target
if target.is_symlink() or target.resolve(strict=True)!=target or target.parent!=root:
    raise RuntimeError('Unknown application path/link')
owner=json.loads((target/'task-owned.json').read_text())
if owner['campaign']!='ten-new-project-adversarial-pass' or owner['workspace']!=str(ROOT) or owner['project']!=project:
    raise RuntimeError('Unknown application ownership')
qualification=json.loads((args.qualification or RAW/('native-'+project+'-'+platform.system()+'.json')).read_text())
if qualification['terminal_repetitions']!=100 or qualification['project']!=project:
    raise RuntimeError('Native evidence incomplete')
import subprocess
if subprocess.check_output(['git','-C',target/'source','rev-parse','HEAD'],text=True).strip()!=owner['source_sha']:
    raise RuntimeError('Owned source revision mismatch')
if subprocess.check_output(['git','-C',target/'source','status','--porcelain','--untracked-files=no'],text=True).strip():
    raise RuntimeError('Source mutations not restored')
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit() or int(proc.name)==os.getpid():
        continue
    try:
        command=(proc/'cmdline').read_bytes().split(b'\0')
        cwd=str((proc/'cwd').resolve())
        if cwd.startswith(str(target)+'/') or any(p.decode(errors='replace').startswith(str(target)+'/') for p in command):
            raise RuntimeError('Owned application process still live: '+proc.name)
    except (OSError,PermissionError):
        pass
shutil.rmtree(target)
if target.exists():
    raise RuntimeError('Owned deletion failed')
(RAW/('cleanup-'+platform.system()+'.json')).write_text(json.dumps(dict(project=project,
    removed=True,canonical_target=str(target),process_check='no owned process references',source=qualification['source']),indent=2)+'\n')
print('Owned application removed after native evidence/process checks')
