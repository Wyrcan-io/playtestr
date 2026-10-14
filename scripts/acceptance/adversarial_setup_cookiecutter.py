"""Reviewed source installation for one pinned target, without global installs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import urllib.request
from adversarial_process import ROOT,DOC,RAW,run

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--native-source',action='store_true')
    parser.add_argument('--project',default='cookiecutter')
    args=parser.parse_args()
    project=args.project
    if not project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in project):
        raise RuntimeError('Invalid owned project identity')
    candidate=next(c for c in json.loads((DOC/'candidates.json').read_text())
                   if c['repo'].split('/')[-1]==project and c['disposition']=='selected')
    from adversarial_owned_source import claim
    root=ROOT/'.cache/ten-new-project-apps'
    parents=[root,*([Path('/var/tmp')] if os.name!='nt' else [])]
    app=claim(Path('/var/tmp') if args.native_source else root,project,candidate['sha'],
              other_roots=parents,prefix='playtestr-adversarial-' if args.native_source else '')
    source=app/'source'
    if not source.exists():
        run(['git','clone','--filter=blob:none','--no-checkout',candidate['url']+'.git',source],
            project,'source-acquisition',timeout=180)
        run(['git','-C',source,'checkout','--detach',candidate['sha']],project,'pinned-checkout',timeout=180)
    if subprocess.check_output(['git','-C',source,'rev-parse','HEAD'],text=True).strip()!=candidate['sha']:
        raise RuntimeError('Source identity mismatch')
    if subprocess.check_output(['git','-C',source,'status','--porcelain','--untracked-files=no'],text=True,timeout=15).strip():
        raise RuntimeError('Pristine Python setup cannot adopt mutated source')
    package=DOC/project
    package.mkdir(parents=True,exist_ok=True)
    (package/'UPSTREAM-LICENSE.txt').write_bytes((source/'LICENSE').read_bytes())
    venv=app/'venv'
    ext='Scripts' if os.name=='nt' else 'bin'
    python=venv/ext/('python.exe' if os.name=='nt' else 'python')
    if not args.native_source:
        if not venv.exists():
            run([sys.executable,'-m','venv',venv],project,'create-native-venv',timeout=120)
        installer=[python,'-m','pip','install','--cache-dir',app/'pip-cache']
    else:
        tools=ROOT/'.tools/ten-new-project-runtime'
        tools.mkdir(parents=True,exist_ok=True)
        archive=tools/'uv-0.12.23-linux.tar.gz'
        expected='9167d72b3319674b6303c4cbe071854bba13ebdf3d76b1a7cbdc175471fb66d6'
        if not archive.exists():
            with urllib.request.urlopen('https://github.com/astral-sh/uv/releases/download/0.12.23/uv-x86_64-unknown-linux-gnu.tar.gz',timeout=60) as response, archive.open('xb') as output:
                total=0
                while block:=response.read(1024*1024):
                    total+=len(block)
                    if total>40*1024*1024:
                        raise RuntimeError('UV acquisition output bound')
                    output.write(block)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('UV digest differs from verified official toolchain')
        uv=tools/'uv-x86_64-unknown-linux-gnu/uv'
        if not uv.exists():
            with tarfile.open(archive) as tar:
                tar.extractall(tools,filter='data')
        if not venv.exists():
            run([uv,'venv','--python','/usr/bin/python3',venv],project,'create-native-venv',timeout=120)
        installer=[uv,'pip','install','--python',python,'--cache-dir',app/'pip-cache']
    constraints=package/'dependency-constraints.txt'
    if constraints.exists():
        installer+=['--constraint',constraints]
    run([*installer,'--editable',source],project,'install-reviewed-editable-source',timeout=1200)
    freeze_command=([python,'-m','pip','freeze'] if not args.native_source else
                    [uv,'pip','freeze','--python',python])
    freeze=run(freeze_command,project,'freeze-dependencies',timeout=30)['output']
    if not constraints.exists():
        constraints.write_text('\n'.join(line for line in freeze.splitlines()
            if '==' in line and not line.startswith('#'))+'\n')
    identity=dict(source=candidate['sha'],python=platform.python_version(),
                  native_host=platform.platform(),app=str(app),source_path=str(source),
                  path=str(venv/ext),dependencies=freeze,editable=True)
    (app/'runtime.json').write_text(json.dumps(identity,indent=2)+'\n')
    if os.environ.get('GITHUB_PATH'):
        with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as path_file:
            path_file.write(str(venv/ext)+'\n')
    print(json.dumps(identity,indent=2))

if __name__=='__main__':
    main()
