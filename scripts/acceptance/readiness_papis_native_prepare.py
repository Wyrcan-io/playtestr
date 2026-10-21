"""Prepare exact candidate and reviewed Papis solely inside a native checkout."""
import asyncio
import argparse
import os
import shutil
import sys
from pathlib import Path

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target-only',action='store_true')
    parser.add_argument('--no-path-export',action='store_true');args=parser.parse_args()
    if args.no_path_export and not args.target_only:parser.error('--no-path-export requires --target-only')
    if not args.target_only:
        candidate=ROOT/'.playtestr-bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
        binary=RAW/'bin'/candidate.name;binary.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(candidate,binary)
        if os.name!='nt':binary.chmod(0o755)
        immutable_json(RAW/'papis-native-runner.json',dict(source_revision=os.environ['SOURCE_REVISION'],
            candidate_sha256=sha256(candidate),copied_sha256=sha256(binary)))
    if os.name!='nt':
        immutable_json(RAW/'papis-runtime-baseline.json',await runtime_inventory('papis','runtime-baseline-before-acquisition'))
    for script,label,timeout in [('readiness_acquire_papis.py','native-pinned-source-acquisition',180),
            ('readiness_build_papis.py','native-owned-reviewed-build',1200)]:
        await execute([sys.executable,'scripts/acceptance/'+script],'papis',label,timeout=timeout,campaign=Campaign())
    # Each public journey sets the target PATH only in its child environment.
    # Keep workflow helpers on the installed bootstrap interpreter so the
    # additional owned-runtime observer cannot match a venv helper itself.
    if args.target_only:
        await execute([sys.executable,'scripts/acceptance/readiness_papis_native_contracts.py','--prepare-only'],
            'papis','prepare-exact-generated-workflow-contracts',timeout=30,campaign=Campaign())
        if not args.no_path_export:
            with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as output:
                output.write(str(RAW/'active/papis/venv'/('Scripts' if os.name=='nt' else 'bin'))+'\n')
        with Path(os.environ['GITHUB_ENV']).open('a',encoding='utf-8') as output:
            output.write('PAPIS_BOOTSTRAP_PYTHON='+sys.executable+'\n')


if __name__=='__main__':asyncio.run(main())
