"""Hosted native qualification of the one currently active application."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from adversarial_process import ROOT,DOC,RAW,run

def main():
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    binary=ROOT/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    run(['go','build','-trimpath','-ldflags',
         '-X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=source-'+source,
         '-o',binary,'./cmd/playtestr'],'core','native-build',timeout=180)
    run([sys.executable,ROOT/'scripts/acceptance/adversarial_setup_cookiecutter.py'],
        'cookiecutter','native-setup',timeout=1200)
    helper=ROOT/'scripts/acceptance/adversarial_journey.py'
    run([sys.executable,helper,'test','cookiecutter','--binary',binary],
        'cookiecutter','native-initial-all',timeout=300)
    run([sys.executable,helper,'state','cookiecutter','--binary',binary],
        'cookiecutter','native-independent-all',timeout=300)
    run([sys.executable,helper,'rerecord','cookiecutter','--case','normal-project','--binary',binary],
        'cookiecutter','native-rerecord',timeout=120)
    run([sys.executable,ROOT/'scripts/acceptance/adversarial_cookiecutter_mutations.py','--binary',binary],
        'cookiecutter','native-regressions-and-state-corruption',timeout=120)
    # These are development repetitions. Final campaign freeze remains separate.
    run([sys.executable,helper,'final','cookiecutter','--binary',binary],
        'cookiecutter','native-development-repetitions',timeout=900)
    report=dict(source=source,runner_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        actual_host=platform.platform(),project='cookiecutter',scenarios=10,
        terminal_repetitions=100,state_probe_repetitions=100,
        state_scope='Separate real recorder executions, exact reviewed screens and same-workspace files before teardown',
        phase='development qualification, final batch freeze still pending',
        run_id=os.environ.get('GITHUB_RUN_ID'),run_attempt=os.environ.get('GITHUB_RUN_ATTEMPT'))
    (RAW/('native-cookiecutter-'+platform.system()+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
