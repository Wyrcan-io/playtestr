"""Bind Skim v8 to the current staged cross-platform final-series harness."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result=subprocess.run(['git','show',':'+name],cwd=ROOT,
        capture_output=True,check=False)
    if result.returncode:
        raise RuntimeError('v2 harness file is not staged: '+name)
    data=result.stdout
    if name.lower().endswith(('.py','.ps1','.yml','.yaml')):
        data=data.replace(b'\r\n',b'\n')
    return data


def main():
    package=DOC/'skim'
    prior_path=package/'final-series-declaration-native-exit-v2.json'
    prior=json.loads(prior_path.read_text(encoding='utf-8'))
    declaration=dict(prior)
    declaration['replacement_plan_namespace']='final-series-plan-native-exit-v8'
    declaration['supersedes']=dict(path=prior_path.name,sha256=sha256(prior_path),reason=(
        'The prior hosted retry preserved two distinct prelaunch failures: Linux storage '
        'measurement encountered a temporary special entry created by its command wrapper; '
        'Windows compared checkout line endings against normalized staged-byte hashes and '
        'refused before any candidate launch. Windows checked cleanup also encountered an '
        'in-target reparse directory. V8 additionally tests rejection of a junction that escapes the owned target. V7 uses direct bounded source acquisition, normalized '
        'harness hashing, and inventory of only reparse directories proven to resolve inside '
        'the owned target. V6 and both failed attempts remain immutable and uncredited.'))
    harness=dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v3.py']='staged-self-hash'
    for name in harness:
        if name=='scripts/acceptance/next20_skim_final_declare_v3.py':
            continue
        harness[name]=hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v3.py']=hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v3.py')).hexdigest()
    declaration['harness_files']=dict(sorted(harness.items()))
    immutable_json(package/'final-series-declaration-native-exit-v3.json',declaration)
    print('Declared Skim v8 against current staged harness; zero candidate launches or credit.')


if __name__=='__main__':
    main()
