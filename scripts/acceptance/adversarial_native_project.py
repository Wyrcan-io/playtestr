"""Native development qualification for the single declared active project."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from adversarial_process import ROOT,DOC,RAW,run

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True,choices=['cookiecutter','copier','lf','superfile','glow','helix','broot','yazi'])
    args=parser.parse_args()
    project=args.project
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    binary=ROOT/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    run(['go','build','-trimpath','-ldflags',
        '-X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=source-'+source,
        '-o',binary,'./cmd/playtestr'],'core','native-build',timeout=180)
    go_project=project in {'lf','superfile','glow'}
    rust_project=project in {'helix','broot','yazi'}
    setup=('adversarial_setup_go.py' if go_project else
        'adversarial_setup_rust.py' if rust_project else 'adversarial_setup_cookiecutter.py')
    run([sys.executable,ROOT/'scripts/acceptance'/setup,'--project',project],
        project,'native-setup',timeout=1200)
    if project=='copier':
        run([sys.executable,ROOT/'scripts/acceptance/adversarial_copier_git_fixture.py'],
            project,'native-synthetic-git-prerequisites',timeout=60)
    git_version=run(['git','--version'],project,'native-git-version',timeout=10)['output'].strip()
    budget=ROOT/'scripts/acceptance/adversarial_budgets.py'
    run([sys.executable,budget,project,'--label','before-native'],project,'native-budget-before',timeout=90)
    helper=ROOT/'scripts/acceptance/adversarial_journey.py'
    for mode,label in [('test','native-initial-all'),('state','native-independent-all')]:
        run([sys.executable,helper,mode,project,'--binary',binary],project,label,timeout=480)
    run([sys.executable,helper,'rerecord',project,'--case','normal-project','--binary',binary],
        project,'native-rerecord',timeout=120)
    mutation=[sys.executable,ROOT/'scripts/acceptance'/('adversarial_go_mutations.py' if go_project
        else 'adversarial_rust_mutations.py' if rust_project else 'adversarial_'+project+'_mutations.py'),'--binary',binary]
    if go_project or rust_project:
        mutation+=['--project',project]
    run(mutation,project,'native-regressions-and-state-corruption',timeout=1800 if rust_project else 600 if go_project else 180)
    run([sys.executable,helper,'final',project,'--binary',binary],
        project,'native-development-repetitions',timeout=1200)
    run([sys.executable,budget,project,'--label','after-native'],project,'native-budget-after',timeout=90)
    config=json.loads((DOC/project/'scenarios.json').read_text(encoding='utf-8'))
    diagnostic=config.get('windows_target_race_check')
    if os.name=='nt' and diagnostic:
        if not go_project:
            raise RuntimeError('Declared Go target race diagnostic requires a Go application')
        run([sys.executable,ROOT/'scripts/acceptance/adversarial_windows_target_race.py',
            '--project',project,'--case',diagnostic['case'],'--count',str(diagnostic['count'])],
            project,'native-pristine-target-race-diagnostic',timeout=1100)
        run([sys.executable,budget,project,'--label','after-target-race'],
            project,'native-budget-after-target-race',timeout=90)
    report=dict(source=source,runner_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        actual_host=platform.platform(),project=project,scenarios=len(config['cases']),
        git_version=git_version,
        terminal_repetitions=10*len(config['cases']),state_probe_repetitions=10*len(config['cases']),
        state_scope='Separate real recorder executions: exact reviewed screen and current managed workspace files before teardown',
        phase='Development qualification; final single-source batch freeze remains pending',
        run_id=os.environ.get('GITHUB_RUN_ID'),run_attempt=os.environ.get('GITHUB_RUN_ATTEMPT'))
    (RAW/('native-'+project+'-'+platform.system()+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
