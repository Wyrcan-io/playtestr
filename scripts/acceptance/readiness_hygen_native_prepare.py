"""Prepare reviewed Hygen after extracting the already-frozen native archive."""
import asyncio
import os
from pathlib import Path
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, immutable_json


async def main():
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
    print('Reviewed pinned Hygen ready for exact-archive first-use recording.')


if __name__ == '__main__':
    asyncio.run(main())
