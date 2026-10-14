"""Owned Unix source launcher for the reviewed dependency-free Ranger path."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
from adversarial_process import ROOT,DOC,run
from adversarial_owned_source import claim
from adversarial_fixture_directories import prepare


def source_identity(source):
    files={}
    for path in sorted(source.rglob('*.py')):
        if '.git' in path.relative_to(source).parts:continue
        if path.is_symlink() or path.stat().st_size>4*1024*1024:
            raise RuntimeError('Unsafe interpreted source identity input')
        files[path.relative_to(source).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        if len(files)>4096:raise RuntimeError('Interpreted source identity entry bound')
    return dict(files_sha256=files,digest=hashlib.sha256(
        json.dumps(files,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True,choices=['ranger'])
    parser.add_argument('--native-source',action='store_true')
    args=parser.parse_args();project=args.project
    if os.name=='nt':raise RuntimeError('The reviewed Ranger matrix requires native Unix curses')
    candidate=next(c for c in json.loads((DOC/'candidates.json').read_text(encoding='utf-8'))
                   if c['repo'].split('/')[-1]==project and c['disposition']=='selected')
    local_root=ROOT/'.cache/ten-new-project-apps'
    app=claim(Path('/var/tmp') if args.native_source else local_root,project,candidate['sha'],
              other_roots=[local_root,Path('/var/tmp')],
              prefix='playtestr-adversarial-' if args.native_source else '')
    source=app/'source'
    if not source.exists():
        run(['git','clone','--filter=blob:none','--no-checkout',candidate['url']+'.git',source],
            project,'source-acquisition',timeout=180)
        run(['git','-C',source,'checkout','--detach',candidate['sha']],project,'pinned-checkout',timeout=180)
    if subprocess.check_output(['git','-C',source,'rev-parse','HEAD'],text=True,timeout=15).strip()!=candidate['sha']:
        raise RuntimeError('Source identity differs from reviewed pin')
    if subprocess.check_output(['git','-C',source,'status','--porcelain','--untracked-files=no'],text=True,timeout=15).strip():
        raise RuntimeError('Pristine Python setup cannot adopt mutated source')
    package=DOC/project;package.mkdir(parents=True,exist_ok=True);prepare(package)
    license_data=subprocess.check_output(['git','-C',source,'show',candidate['sha']+':LICENSE'],timeout=15)
    (package/'UPSTREAM-LICENSE.txt').write_bytes(license_data)
    venv=app/'venv'
    if not venv.exists():
        run([sys.executable,'-m','venv','--without-pip',venv],project,'create-private-interpreter',timeout=120)
    python=venv/'bin/python'
    probe=run([python,'-c','import curses,sys; print(sys.version); print(curses.__file__)'],
              project,'native-python-curses-prerequisite',timeout=15)['output']
    bin_dir=app/'bin';bin_dir.mkdir(exist_ok=True)
    launcher=bin_dir/'ranger'
    # Transparent exec of the ordinary pinned launcher: no output processing,
    # target assertions, hidden inputs or manufactured readiness.
    launcher.write_text('#!/bin/sh\nexec '+shlex.quote(str(python))+' -O '+
                        shlex.quote(str(source/'ranger.py'))+' "$@"\n',encoding='utf-8')
    launcher.chmod(0o755)
    identity=dict(source=candidate['sha'],native_host=platform.platform(),app=str(app),
                  source_path=str(source),path=str(bin_dir),editable=True,
                  binary=str(launcher),binary_sha256=hashlib.sha256(launcher.read_bytes()).hexdigest(),
                  execution_identity=source_identity(source),python_probe=probe,
                  interpreter_sha256=hashlib.sha256(python.resolve(strict=True).read_bytes()).hexdigest(),
                  dependencies='No third-party packages installed; existing native Python curses required',
                  setup='Private --without-pip environment and transparent exec of pinned ranger.py with ordinary -O')
    (app/'runtime.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(identity,indent=2))


if __name__=='__main__':main()
