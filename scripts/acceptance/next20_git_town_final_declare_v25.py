"""Bind Git Town v25 to the corrected shared native identity and journal helpers."""
import hashlib
import json
import subprocess

from next20_check import DOC,ROOT
from readiness_evidence import immutable_json,sha256


def staged_bytes(name):
    result=subprocess.run(['git','show',':'+name],cwd=ROOT,capture_output=True,check=False)
    if result.returncode:raise RuntimeError('v25 harness file is not staged: '+name)
    data=result.stdout
    if name.lower().endswith(('.py','.ps1','.yml','.yaml')):data=data.replace(b'\r\n',b'\n')
    return data


def main():
    package=DOC/'git-town';prior_path=package/'final-series-declaration-native-exit-v24.json'
    prior=json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision')!=24 or prior.get('candidate_series')!='native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v24')
    declaration=dict(prior);declaration['revision']=25
    declaration['supersedes']=dict(path=prior_path.name,sha256=sha256(prior_path),reason=(
        'V24 was prepared after the preserved V23 zero-launch run but was not dispatched; a later bounded '
        'Windows process-reaping fix and test scratch-root adjustment changed declaration-bound harness '
        'bytes. V25 binds the staged final harness and preserves the original zero-launch failure without '
        'claiming a rerun.'))
    harness=dict(prior['harness_files']);name='scripts/acceptance/next20_git_town_final_declare_v25.py'
    harness[name]='staged-self-hash'
    for path in tuple(harness):
        if path!=name:harness[path]=hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name]=hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files']=dict(sorted(harness.items()))
    immutable_json(package/'final-series-declaration-native-exit-v25.json',declaration)
    print('Declared Git Town v25 against staged harness; supplemental rerun, zero admission credit.')


if __name__=='__main__':main()
