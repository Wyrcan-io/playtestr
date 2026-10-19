"""Prepare the reviewed native Rclone target without rebuilding Playtestr."""
import asyncio
import os
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, immutable_json


async def main():
    if os.name != 'nt':
        immutable_json(RAW / 'rclone-runtime-baseline.json',
                       await runtime_inventory('rclone', 'owned-runtime-baseline-before-acquisition'))
    await execute([sys.executable, 'scripts/acceptance/readiness_acquire_rclone.py'],
                  'rclone', 'native-reserved-pinned-source-acquisition', timeout=180, campaign=Campaign())
    await execute([sys.executable, 'scripts/acceptance/readiness_build_rclone.py'],
                  'rclone', 'native-reviewed-owned-build', timeout=1140, campaign=Campaign())
    print('Reviewed native Rclone ready; runner remains exact frozen archive bytes.')


if __name__ == '__main__':
    asyncio.run(main())
