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
parser.add_argument('--exploratory',action='store_true')
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
import subprocess
if args.exploratory:
    cleanup_source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=15).strip()
    cleanup_scope='Local exploratory teardown only; no native project qualification granted'
else:
    qualification=json.loads((args.qualification or RAW/('native-'+project+'-'+platform.system()+'.json')).read_text())
    if qualification.get('scenarios',0)<10 or qualification['terminal_repetitions']!=10*qualification['scenarios'] or qualification['project']!=project:
        raise RuntimeError('Native evidence incomplete')
    cleanup_source=qualification['source']
    cleanup_scope='Teardown following native development qualification'
if subprocess.check_output(['git','-C',target/'source','rev-parse','HEAD'],text=True).strip()!=owner['source_sha']:
    raise RuntimeError('Owned source revision mismatch')
if subprocess.check_output(['git','-C',target/'source','status','--porcelain','--untracked-files=no'],text=True).strip():
    raise RuntimeError('Source mutations not restored')
if platform.system()=='Linux':
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
    process_check='Linux visible /proc command and cwd references; runner separately confirms target termination'
elif platform.system()=='Darwin':
    from adversarial_process import run
    processes=run(['ps','-axo','pid=,command='],project,'cleanup-process-inventory',timeout=15)['output']
    for line in processes.splitlines():
        pid,command=line.strip().split(None,1)
        if int(pid)!=os.getpid() and str(target)+'/' in command:
            raise RuntimeError('Owned application command reference remains: '+pid)
    current_pid=None
    listing=run(['lsof','-n','-P','-a','-d','cwd','-F','pn'],project,
                'cleanup-cwd-inventory',timeout=15)['output']
    for line in listing.splitlines():
        if line.startswith('p'):
            current_pid=int(line[1:])
        elif line.startswith('n') and current_pid!=os.getpid() and (
                line[1:]==str(target) or line[1:].startswith(str(target)+'/')):
            raise RuntimeError('Owned application cwd reference remains: '+str(current_pid))
    process_check='macOS visible ps command and lsof cwd references; runner separately confirms target termination'
else:
    raise RuntimeError('Native process inspection is not implemented on this Unix host')
# Go module caches deliberately contain read-only directories. Grant owner
# write permission only to ordinary directories in the exact verified owned
# tree. Never follow a symlink or change permission on its destination.
for folder,dirs,_ in os.walk(target,followlinks=False):
    path=Path(folder)
    if path.is_symlink() or not path.resolve().is_relative_to(target):
        raise RuntimeError('Unsafe owned directory while preparing removal')
    os.chmod(path,0o700)
    dirs[:]=[name for name in dirs if not (path/name).is_symlink()]
shutil.rmtree(target)
if target.exists():
    raise RuntimeError('Owned deletion failed')
(RAW/('cleanup-'+platform.system()+'.json')).write_text(json.dumps(dict(project=project,
    removed=True,canonical_target=str(target),process_check=process_check,source=cleanup_source,scope=cleanup_scope),indent=2)+'\n')
print('Owned application removed after native evidence/process checks')
