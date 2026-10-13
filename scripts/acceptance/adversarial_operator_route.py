"""Instrument the prepared public CLI walkthrough; disclose automation confounders."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from adversarial_process import ROOT, DOC, run
from adversarial_journey import recorder

parser=argparse.ArgumentParser()
parser.add_argument('project')
parser.add_argument('--runtime',type=Path)
parser.add_argument('--binary',type=Path)
args=parser.parse_args()
project=args.project
directory=DOC/project
if (directory/'ux-first-pass.json').exists():
    raise RuntimeError('Do not overwrite a retained onboarding assessment')
configuration=json.loads((directory/'scenarios.json').read_text(encoding='utf-8'))
primary=next(c for c in configuration['cases'] if c['name']=='normal-project')
case=dict(primary,name='ux-first-pass')
runtime=json.loads(((args.runtime or ROOT/'.cache/ten-new-project-apps'/project)/'runtime.json').read_text(encoding='utf-8'))
env=dict(os.environ,PATH=runtime['path']+os.pathsep+os.environ['PATH'])
binary=args.binary or (ROOT/'bin/playtestr.exe' if os.name=='nt' else ROOT/'bin/playtestr-linux')
started=time.monotonic()
version=run([binary,'version'],project,'ux-public-version',env=env)
help_result=run([binary,'record','--help'],project,'ux-public-recorder-help',env=env)
recorded=recorder(binary,project,case,env)
tested=run([binary,'test',directory/'ux-first-pass.json'],project,'ux-public-fresh-test',env=env)
elapsed=time.monotonic()-started
spec=json.loads((directory/'ux-first-pass.json').read_text(encoding='utf-8'))
result=dict(commands=4,recorder_controls=len(spec['steps'])+3,
    elapsed_prepared_route_seconds=elapsed,manual_json_edits=0,
    evidence_ids=[r['id'] for r in [version,help_result,recorded,tested]],
    runner_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
    provisional_command_gate_passed=4<=5,
    provisional_control_gate_passed=len(spec['steps'])+3<=20,
    provisional_elapsed_gate_passed=elapsed<=900,
    assessment='Prepared operator walkthrough using public commands; not an independent novice study',
    confounders=['Prepared reviewed synthetic fixture and control sequence','Warm build/dependency caches',
                 'Prior operator knowledge and corrected authoring attempts',
                 'Controls automated one public recorder response at a time'],
    excluded_time='Application acquisition, fixture engineering, prior exploratory authoring and correction; measured elapsed is not total setup or beginner authoring time',
    diagnosis='Separate intentional mismatch/report route retained in maintenance-result.json')
(directory/'ux-prepared-route.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
