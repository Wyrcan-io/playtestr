"""Bind Skim v9 to the current staged cross-platform final-series harness."""
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
    prior_path=package/'final-series-declaration-native-exit-v3.json'
    prior=json.loads(prior_path.read_text(encoding='utf-8'))
    declaration=dict(prior)
    declaration['replacement_plan_namespace']='final-series-plan-native-exit-v9'
    declaration['supersedes']=dict(path=prior_path.name,sha256=sha256(prior_path),reason=(
        'V8 remained zero-launch: Linux storage measurement rejected a FIFO/socket entry '
        'without a path diagnostic, while Windows source acquisition hit HTTP 504 and left '
        'an owner-only active directory that the ordinary source cleanup path could not '
        'validate. V9 adds explicit FIFO/socket metadata, a three-attempt cap for transient '
        'source failures, source download before active-target creation, and failure receipts. '
        'Earlier v6-v8 plans and hosted artifacts remain preserved and uncredited.'))
    harness=dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v4.py']='staged-self-hash'
    harness['scripts/acceptance/readiness_storage.py']='staged-storage-hash'
    harness['scripts/acceptance/test_next20_acquire.py']='staged-acquisition-test-hash'
    harness['scripts/acceptance/test_next20_storage.py']='staged-storage-test-hash'
    for name in harness:
        if name=='scripts/acceptance/next20_skim_final_declare_v4.py':
            continue
        if name in {'scripts/acceptance/readiness_storage.py','scripts/acceptance/test_next20_acquire.py','scripts/acceptance/test_next20_storage.py'}:
            harness[name]=hashlib.sha256(staged_bytes(name)).hexdigest()
            continue

        harness[name]=hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v4.py']=hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v4.py')).hexdigest()
    declaration['harness_files']=dict(sorted(harness.items()))
    immutable_json(package/'final-series-declaration-native-exit-v4.json',declaration)
    print('Declared Skim v9 against current staged harness; zero candidate launches or credit.')


if __name__=='__main__':
    main()
