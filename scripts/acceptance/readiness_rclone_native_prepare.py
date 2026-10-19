"""Prepare the reviewed native Rclone target without rebuilding Playtestr."""
import asyncio
import os
import sys
import shutil

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, immutable_json, sha256


async def main():
    if os.name != 'nt':
        immutable_json(RAW / 'rclone-runtime-baseline.json',
                       await runtime_inventory('rclone', 'owned-runtime-baseline-before-acquisition'))
    await execute([sys.executable, 'scripts/acceptance/readiness_acquire_rclone.py'],
                  'rclone', 'native-reserved-pinned-source-acquisition', timeout=180, campaign=Campaign())
    try:
        await execute([sys.executable, 'scripts/acceptance/readiness_build_rclone.py'],
                      'rclone', 'native-reviewed-owned-build', timeout=1140, campaign=Campaign())
    finally:
        target=RAW/'active/rclone'
        retained=RAW/'rclone/build-receipts'
        retained.mkdir(parents=True)
        files=['task-owned.json','acquisition.json','runtime.json','build.json','toolchain/sdk.json']
        files += [p.name for p in target.glob('build-storage-*.json')]
        hashes={}
        for name in files:
            path=target/name
            if not path.is_file():continue
            copy=retained/name
            copy.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,copy)
            if sha256(copy)!=sha256(path):raise RuntimeError('native build receipt copy differs')
            hashes[name]=sha256(copy)
        immutable_json(retained/'index.json',dict(files=hashes,
            qualification='Actual setup receipts retained even if a later first-route or cleanup stage fails.')))
    print('Reviewed native Rclone ready; runner remains exact frozen archive bytes.')


if __name__ == '__main__':
    asyncio.run(main())
