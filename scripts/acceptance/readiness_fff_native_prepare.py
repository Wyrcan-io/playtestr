"""One native fff source/build and exact already-built Playtestr candidate."""
import argparse
import asyncio
import os
from pathlib import Path
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256

SOURCE=os.environ.get('SOURCE_REVISION','e7b5f29e575e44babe7fdaa2e83e55b62d318305')


async def main():
    if os.name=='nt':raise RuntimeError('native fff profile declares Linux/macOS only')
    parser=argparse.ArgumentParser();parser.add_argument('--target-only',action='store_true');args=parser.parse_args()
    if not args.target_only:
        candidate=ROOT/'.playtestr-bin/playtestr';binary=RAW/'bin/playtestr'
        binary.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate,binary);binary.chmod(0o755)
        immutable_json(RAW/'fff-native-runner.json',dict(source_revision=SOURCE,candidate_sha256=sha256(candidate),copied_sha256=sha256(binary)))
    immutable_json(RAW/'fff-runtime-baseline.json',await runtime_inventory('fff','runtime-baseline-before-acquisition'))
    await execute([sys.executable,'scripts/acceptance/readiness_acquire_fff.py'],'fff','native-pinned-profiled-source-acquisition',
        timeout=180,campaign=Campaign())
    await execute([sys.executable,'scripts/acceptance/readiness_build_fff.py'],'fff','native-reviewed-bash-runtime-parent',
        timeout=600,campaign=Campaign())
    with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as output:
        output.write(str(RAW/'active/fff/src')+'\n')
        output.write(str(Path('/bin/bash').resolve().parent)+'\n')
    if args.target_only:
        await execute([sys.executable,'scripts/acceptance/readiness_fff_native_contracts.py','--prepare-only'],
            'fff','prepare-reviewed-workflow-contracts',timeout=30,campaign=Campaign())
    print('Owned pinned native fff is available for its first public recorder route.')


if __name__=='__main__':asyncio.run(main())
