"""Native development qualification for the single declared active project."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from adversarial_process import ROOT,DOC,RAW,run


def stage(argv,project,label,**kwargs):
    print(label+' started',flush=True)
    result=run(argv,project,label,**kwargs)
    print(label+' passed '+result['id']+' ('+format(result['seconds'],'.3f')+'s)',flush=True)
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True,choices=['cookiecutter','copier','lf','superfile','glow','helix','broot','yazi','ranger','nnn'])
    parser.add_argument('--frozen-runner-manifest',type=Path)
    args=parser.parse_args()
    project=args.project
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    binary=ROOT/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    if args.frozen_runner_manifest:
        from adversarial_freeze_runner import verify
        binary,_=verify(args.frozen_runner_manifest)
    else:
        stage(['go','build','-trimpath','-ldflags',
            '-X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=source-'+source,
            '-o',binary,'./cmd/playtestr'],'core','native-build',timeout=180)
    go_project=project in {'lf','superfile','glow'}
    rust_project=project in {'helix','broot','yazi'}
    python_project=project=='ranger'
    c_project=project=='nnn'
    setup=('adversarial_setup_go.py' if go_project else
        'adversarial_setup_rust.py' if rust_project else
        'adversarial_setup_python.py' if python_project else
        'adversarial_setup_c.py' if c_project else 'adversarial_setup_cookiecutter.py')
    stage([sys.executable,ROOT/'scripts/acceptance'/setup,'--project',project],
        project,'native-setup',timeout=1200)
    external_state_cleanup=None
    file_prerequisite=None
    if os.name=='nt' and project=='yazi':
        git=Path(shutil.which('git') or '').resolve(strict=True)
        candidates=[git.parent.parent/'usr/bin/file.exe',Path('C:/msys64/usr/bin/file.exe')]
        executable=next((p for p in candidates if p.is_file()),None)
        if executable is None:raise RuntimeError('Reviewed existing file.exe prerequisite is missing')
        os.environ['PATH']=str(executable.parent)+os.pathsep+os.environ['PATH']
        version=stage([executable,'--version'],project,'native-file-prerequisite-version',timeout=15)['output'].strip()
        mime=stage([executable,'-bL','--mime-type','-f','-'],project,'native-file-prerequisite-actual-path',
                 input=str(DOC/project/'fixtures/protected.txt')+'\n',timeout=15)['output'].strip()
        if mime!='text/plain':raise RuntimeError('Existing Windows file cannot inspect the actual synthetic fixture path')
        file_prerequisite=dict(binary=str(executable),version=version,actual_fixture_mime=mime)
        from adversarial_windows_state import claim,release
        claim(project)
    if project=='copier':
        stage([sys.executable,ROOT/'scripts/acceptance/adversarial_copier_git_fixture.py'],
            project,'native-synthetic-git-prerequisites',timeout=60)
    git_version=stage(['git','--version'],project,'native-git-version',timeout=10)['output'].strip()
    budget=ROOT/'scripts/acceptance/adversarial_budgets.py'
    stage([sys.executable,budget,project,'--label','before-native'],project,'native-budget-before',timeout=90)
    helper=ROOT/'scripts/acceptance/adversarial_journey.py'
    for mode,label in [('test','native-initial-all'),('state','native-independent-all')]:
        stage([sys.executable,helper,mode,project,'--binary',binary],project,label,timeout=480)
    stage([sys.executable,helper,'rerecord',project,'--case','normal-project','--binary',binary],
        project,'native-rerecord',timeout=120)
    mutation=[sys.executable,ROOT/'scripts/acceptance'/('adversarial_go_mutations.py' if go_project
        else 'adversarial_rust_mutations.py' if rust_project
        else 'adversarial_python_mutations.py' if python_project
        else 'adversarial_c_mutations.py' if c_project else 'adversarial_'+project+'_mutations.py'),'--binary',binary]
    if go_project or rust_project or python_project or c_project:
        mutation+=['--project',project]
    stage(mutation,project,'native-regressions-and-state-corruption',timeout=1800 if rust_project else 600 if go_project or c_project else 180)
    repetition_config=json.loads((DOC/project/'scenarios.json').read_text(encoding='utf-8'))
    for case in repetition_config['cases']:
        stage([sys.executable,helper,'final',project,'--case',case['name'],'--binary',binary],
            project,'native-repetitions-'+case['name'],timeout=600)
    stage([sys.executable,budget,project,'--label','after-native'],project,'native-budget-after',timeout=90)
    config=json.loads((DOC/project/'scenarios.json').read_text(encoding='utf-8'))
    diagnostic=config.get('windows_target_race_check')
    if os.name=='nt' and diagnostic:
        if not go_project:
            raise RuntimeError('Declared Go target race diagnostic requires a Go application')
        stage([sys.executable,ROOT/'scripts/acceptance/adversarial_windows_target_race.py',
            '--project',project,'--case',diagnostic['case'],'--count',str(diagnostic['count'])],
            project,'native-pristine-target-race-diagnostic',timeout=1100)
        stage([sys.executable,budget,project,'--label','after-target-race'],
            project,'native-budget-after-target-race',timeout=90)
    if args.frozen_runner_manifest:
        verify(args.frozen_runner_manifest)
    if os.name=='nt' and project=='yazi':
        external_state_cleanup=release(project)
    report=dict(source=source,runner_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        actual_host=platform.platform(),project=project,scenarios=len(config['cases']),
        git_version=git_version,
        terminal_repetitions=10*len(config['cases']),state_probe_repetitions=10*len(config['cases']),
        state_scope='Separate real recorder executions: exact reviewed screen and current managed workspace files before teardown',
        phase='Final frozen-source qualification' if args.frozen_runner_manifest else 'Development qualification; final single-source batch freeze remains pending',
        frozen_manifest_sha256=hashlib.sha256(args.frozen_runner_manifest.read_bytes()).hexdigest() if args.frozen_runner_manifest else None,
        external_state_cleanup=external_state_cleanup,
        file_prerequisite=file_prerequisite,
        run_id=os.environ.get('GITHUB_RUN_ID'),run_attempt=os.environ.get('GITHUB_RUN_ATTEMPT'))
    (RAW/('native-'+project+'-'+platform.system()+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
