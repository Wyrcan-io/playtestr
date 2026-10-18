"""Prepare reviewed Hygen after extracting the already-frozen native archive."""
import argparse
import asyncio
import os
from pathlib import Path
import sys
import shutil

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, immutable_json


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--target-only',action='store_true')
    args=parser.parse_args()
    if os.name == 'nt':
        raise RuntimeError('Hygen native cells are declared Linux/macOS')
    immutable_json(RAW / 'hygen-runtime-baseline.json',
                   await runtime_inventory('hygen', 'owned-runtime-baseline-before-acquisition'))
    await execute([sys.executable, 'scripts/acceptance/readiness_acquire_hygen.py'],
                  'hygen', 'native-reserved-pinned-source-acquisition', timeout=180, campaign=Campaign())
    await execute([sys.executable, 'scripts/acceptance/readiness_build_hygen.py'],
                  'hygen', 'native-reviewed-frozen-production-setup', timeout=600, campaign=Campaign())
    with Path(os.environ['GITHUB_PATH']).open('a', encoding='utf-8') as output:
        output.write(str(RAW / 'active/hygen/bin') + '\n')
    if args.target_only:
        from readiness_evidence import ROOT,sha256
        from readiness_new_control_matrix import read_json as load
        import platform
        profile=ROOT/'docs/validation/runner-readiness-ten-project-pass/hygen'
        if platform.system()=='Darwin':profile=profile/'native-profiles/macos'
        frozen=load(profile/'reviewed-contract-freeze.json')
        if len(frozen['contracts'])!=20:raise RuntimeError('twenty reviewed native contracts required')
        for name,digest in frozen['all_package_inputs'].items():
            if sha256(profile/'contracts'/name)!=digest:raise RuntimeError('reviewed native contract inputs changed')
        shutil.copytree(profile/'contracts',RAW/'hygen/host-contracts')
    print('Reviewed pinned Hygen ready for exact-archive first-use recording.')


if __name__ == '__main__':
    asyncio.run(main())
