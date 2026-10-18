"""Prepare the exact native runner and pinned local-only Frogmouth target."""
import asyncio
import argparse
import os
import shutil
import sys
from pathlib import Path

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_frogmouth_first_use import SOURCE


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target-only',action='store_true');args=parser.parse_args()
    if not args.target_only:
        candidate=ROOT/'.playtestr-bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
        binary=RAW/'bin'/candidate.name;binary.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate,binary)
        if os.name!='nt':binary.chmod(0o755)
        immutable_json(RAW/'frogmouth-native-runner.json',dict(source_revision=SOURCE,candidate_sha256=sha256(candidate),copied_sha256=sha256(binary)))
    if os.name!='nt':immutable_json(RAW/'frogmouth-runtime-baseline.json',await runtime_inventory('frogmouth','runtime-baseline-before-acquisition'))
    for script,label,timeout in [('readiness_acquire_frogmouth.py','native-pinned-source-acquisition',180),('readiness_build_frogmouth.py','native-owned-reviewed-build',1200)]:
        await execute([sys.executable,'scripts/acceptance/'+script],'frogmouth',label,timeout=timeout,campaign=Campaign())
    if args.target_only:
        await execute([sys.executable,'scripts/acceptance/readiness_frogmouth_native_contracts.py','--prepare-only'],'frogmouth','prepare-generated-contracts',timeout=30,campaign=Campaign())
        with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as output:
            output.write(str(RAW/'active/frogmouth/venv'/('Scripts' if os.name=='nt' else 'bin'))+'\n')
        with Path(os.environ['GITHUB_ENV']).open('a',encoding='utf-8') as output:
            output.write('FROGMOUTH_BOOTSTRAP_PYTHON='+sys.executable+'\n')


if __name__=='__main__':asyncio.run(main())
