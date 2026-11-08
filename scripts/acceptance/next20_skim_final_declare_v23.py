"""Bind Skim's V23 exact-candidate declaration to current staged harness bytes."""
import hashlib
import json
import subprocess

from next20_check import DOC,ROOT
from next20_skim_final_series import BATCHES
from readiness_evidence import immutable_json,sha256


def staged_bytes(name):
    result=subprocess.run(['git','show',':'+name],cwd=ROOT,capture_output=True,check=False)
    if result.returncode:raise RuntimeError('v23 harness file is not staged: '+name)
    data=result.stdout
    if name.lower().endswith(('.py','.ps1','.yml','.yaml')):data=data.replace(b'\r\n',b'\n')
    return data


def main():
    package=DOC/'skim';prior_path=package/'final-series-declaration-native-exit-v22.json'
    prior=json.loads(prior_path.read_text(encoding='utf-8'))
    declaration=dict(prior);declaration['batches']=BATCHES
    declaration['supersedes']=dict(path=prior_path.name,sha256=sha256(prior_path),reason=(
        'V22 failed both hosted native preflights before candidate launch because next20_acquire.py had changed '
        'after the declaration was frozen. V23 binds the current journal, source acquisition, shared identity '
        'and cleanup harness bytes, and explicitly permits checked no-case cleanup when the source freeze '
        'proves no case-evidence was created. Prior zero-launch results remain preserved.'))
    harness=dict(prior['harness_files']);name='scripts/acceptance/next20_skim_final_declare_v23.py'
    harness[name]='staged-self-hash'
    for path in tuple(harness):
        if path!=name:harness[path]=hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name]=hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files']=dict(sorted(harness.items()))
    immutable_json(package/'final-series-declaration-native-exit-v23.json',declaration)
    print('Declared Skim V23 against staged harness and zero-launch cleanup recovery; no admission inferred.')


if __name__=='__main__':main()
