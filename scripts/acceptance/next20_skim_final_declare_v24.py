"""Bind Skim's V24 exact-candidate declaration to current staged harness bytes."""
import hashlib
import json
import subprocess

from next20_check import DOC,ROOT
from next20_skim_final_series import BATCHES
from readiness_evidence import immutable_json,sha256


def staged_bytes(name):
    result=subprocess.run(['git','show',':'+name],cwd=ROOT,capture_output=True,check=False)
    if result.returncode:raise RuntimeError('v24 harness file is not staged: '+name)
    data=result.stdout
    if name.lower().endswith(('.py','.ps1','.yml','.yaml')):data=data.replace(b'\r\n',b'\n')
    return data


def main():
    package=DOC/'skim';prior_path=package/'final-series-declaration-native-exit-v23.json'
    prior=json.loads(prior_path.read_text(encoding='utf-8'))
    declaration=dict(prior);declaration['batches']=BATCHES
    declaration['supersedes']=dict(path=prior_path.name,sha256=sha256(prior_path),reason=(
        'V23 was prepared after the preserved V22 zero-launch run but was not dispatched; a later test '
        'scratch-root adjustment changed declaration-bound test harness bytes. V24 binds the staged final '
        'harness and retains the checked no-case cleanup path. The prior zero-launch failures remain preserved.'))
    harness=dict(prior['harness_files']);name='scripts/acceptance/next20_skim_final_declare_v24.py'
    harness[name]='staged-self-hash'
    for path in tuple(harness):
        if path!=name:harness[path]=hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name]=hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files']=dict(sorted(harness.items()))
    immutable_json(package/'final-series-declaration-native-exit-v24.json',declaration)
    print('Declared Skim V24 against staged harness and zero-launch cleanup recovery; no admission inferred.')


if __name__=='__main__':main()
