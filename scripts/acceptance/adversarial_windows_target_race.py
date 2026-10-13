"""Bounded real Windows Go target diagnostic; never substitutes for qualification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from adversarial_process import ROOT,DOC,RAW,run


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True,choices=['lf','superfile','glow'])
    parser.add_argument('--case',default='normal-project')
    parser.add_argument('--count',type=int,default=10)
    args=parser.parse_args()
    if os.name!='nt' or not 1<=args.count<=10:
        raise RuntimeError('Diagnostic requires native Windows and one to ten bounded repetitions')
    if not args.case or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.case):
        raise RuntimeError('Invalid diagnostic case name')
    app=ROOT/'.cache/ten-new-project-apps'/args.project
    owner=json.loads((app/'task-owned.json').read_text(encoding='utf-8'))
    if owner.get('project')!=args.project or owner.get('workspace')!=str(ROOT):
        raise RuntimeError('Unknown target ownership')
    identity=json.loads((app/'runtime.json').read_text(encoding='utf-8'))
    if app.is_symlink() or app.is_junction() or app.resolve()!=app:
        raise RuntimeError('Linked target ownership root')
    source_sha=subprocess.check_output(['git','-C',app/'source','rev-parse','HEAD'],text=True,timeout=15).strip()
    if source_sha!=owner['source_sha'] or subprocess.check_output(
            ['git','-C',app/'source','status','--porcelain','--untracked-files=no'],text=True,timeout=15).strip():
        raise RuntimeError('Race diagnostic requires the exact pristine selected target')
    pristine=Path(identity['binary'])
    original_sha=hashlib.sha256(pristine.read_bytes()).hexdigest()
    compiler=next((p for p in [ROOT/'.tools/winlibs/mingw64/bin/gcc.exe',
        Path('C:/msys64/mingw64/bin/gcc.exe'),Path('C:/msys64/ucrt64/bin/gcc.exe')] if p.is_file()),None)
    if compiler is None:
        raise RuntimeError('Native Go race prerequisite missing; no diagnostic success claimed')
    env=dict(os.environ,PATH=str(compiler.parent)+os.pathsep+os.environ['PATH'],
        CGO_ENABLED='1',CC=str(compiler),GOTOOLCHAIN='go1.27.0',GOSUMDB='sum.golang.org')
    for name,folder in [('GOCACHE','go-race-cache'),('GOMODCACHE','go-mod-cache'),
                        ('GOPATH','go-path'),('GOTMPDIR','go-tmp')]:
        destination=app/folder
        destination.mkdir(exist_ok=True)
        env[name]=str(destination)
    binary=app/'bin'/(args.project+'-race.exe')
    run([os.environ.get('PLAYTESTR_GO','go'),'build','-race','-trimpath','-o',binary,'.'],
        args.project,'instrument-pristine-target-race',env=env,cwd=app/'source',timeout=600)
    package=DOC/args.project
    diagnostic=app/('race-diagnostic-'+str(time.time_ns()))
    diagnostic.mkdir(exist_ok=False)
    shutil.copytree(package/'fixtures',diagnostic/'fixtures')
    shutil.copytree(package/'snapshots',diagnostic/'snapshots')
    spec=json.loads((package/(args.case+'.json')).read_text(encoding='utf-8'))
    spec['command'][0]=str(binary)
    spec.setdefault('env',{})['GORACE']='halt_on_error=0 exitcode=66 log_path=.owned-target-race'
    path=diagnostic/'case.json'
    path.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary=diagnostic/'temporary'
    temporary.mkdir()
    execution_env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'],
        TEMP=str(temporary),TMP=str(temporary))
    records=[]
    failed=False
    for repetition in range(args.count):
        report=RAW/args.project/(diagnostic.name+'-'+str(repetition)+'.json')
        try:
            result=run([ROOT/'bin/playtestr.exe','test','--keep-workspace-on-failure',
                '--report',report,'--artifacts-dir',report.with_suffix(''),path],
                args.project,'pristine-target-race-'+str(repetition),env=execution_env,load=True,timeout=30)
            records.append(dict(repetition=repetition,passed=True,evidence_id=result['id']))
        except RuntimeError as error:
            if not report.is_file():raise
            data=json.loads(report.read_text(encoding='utf-8'))['results'][0]
            if data['status']!='failed' or not data['cleanup']['confirmed_exited']:raise
            retained=Path(data['workspace']['retained_path']).resolve(strict=True)
            retained.relative_to(temporary.resolve())
            if retained.is_symlink() or retained.is_junction():
                raise RuntimeError('Linked diagnostic workspace')
            logs=[]
            for race in retained.rglob('.owned-target-race.*'):
                if race.is_symlink() or race.stat().st_size>4*1024*1024:
                    raise RuntimeError('Unsafe target race log')
                output=report.with_name(report.stem+'-'+race.name+'.txt')
                output.write_bytes(race.read_bytes())
                logs.append(dict(path=str(output.relative_to(ROOT)),
                    sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                    actual_race_warning=b'WARNING: DATA RACE' in output.read_bytes()))
            records.append(dict(repetition=repetition,passed=False,evidence_id=error.evidence_id,
                failure=data['failure'],report=str(report.relative_to(ROOT)),target_logs=logs,
                retained_workspace=str(retained)))
            failed=True
            break
    if hashlib.sha256(pristine.read_bytes()).hexdigest()!=original_sha:
        raise RuntimeError('Diagnostic altered pristine target executable')
    result=dict(phase='Diagnostic only; race-free behavior is not proved by absence in bounded runs',
        records=records,source_pin=source_sha,pristine_target_sha256=original_sha,
        diagnostic_target_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        completed_requested_repetitions=not failed,owned_diagnostic_root=str(diagnostic))
    output=RAW/args.project/(diagnostic.name+'-result.json')
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)
    if failed:
        raise RuntimeError('Pristine target race diagnostic failed; preserve actual cause before host admission')


if __name__=='__main__':main()
