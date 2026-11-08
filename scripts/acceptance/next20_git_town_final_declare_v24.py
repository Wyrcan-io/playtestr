"""Bind Git Town v24 to the corrected shared native identity and journal helpers."""
import hashlib
import json
import subprocess

from next20_check import DOC,ROOT
from readiness_evidence import immutable_json,sha256


def staged_bytes(name):
    result=subprocess.run(['git','show',':'+name],cwd=ROOT,capture_output=True,check=False)
    if result.returncode:raise RuntimeError('v24 harness file is not staged: '+name)
    data=result.stdout
    if name.lower().endswith(('.py','.ps1','.yml','.yaml')):data=data.replace(b'\r\n',b'\n')
    return data


def main():
    package=DOC/'git-town';prior_path=package/'final-series-declaration-native-exit-v23.json'
    prior=json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision')!=23 or prior.get('candidate_series')!='native-exit-v1':
        raise ValueError('prior Git Town declaration is not preserved v23')
    declaration=dict(prior);declaration['revision']=24
    declaration['supersedes']=dict(path=prior_path.name,sha256=sha256(prior_path),reason=(
        'The supplemental V23 native workflow downloaded and built the pinned candidate/target on both hosts, '
        'then rejected before a case because its shared final harness hash predated the Taskell contract-source '
        'fallback. V24 binds the reviewed shared helper bytes; the prior zero-launch result remains preserved.'))
    harness=dict(prior['harness_files']);name='scripts/acceptance/next20_git_town_final_declare_v24.py'
    harness[name]='staged-self-hash'
    for path in tuple(harness):
        if path!=name:harness[path]=hashlib.sha256(staged_bytes(path)).hexdigest()
    harness[name]=hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files']=dict(sorted(harness.items()))
    immutable_json(package/'final-series-declaration-native-exit-v24.json',declaration)
    print('Declared Git Town v24 against staged harness; supplemental rerun, zero admission credit.')


if __name__=='__main__':main()
