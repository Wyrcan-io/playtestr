"""Acquire/build only this original application on its declared native host."""
import asyncio
import os
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, immutable_json, sha256


async def main():
    if os.name!='nt':
        immutable_json(RAW/'old-copier-runtime-baseline.json',
            await runtime_inventory('old-copier','migration-owned-runtime-baseline'))
    await execute([sys.executable,'scripts/acceptance/readiness_acquire_old.py','--project','copier'],
        'old-copier','migration-original-pinned-source-acquisition',timeout=180,campaign=Campaign())
    try:
        await execute([sys.executable,'scripts/acceptance/readiness_old_copier_prepare.py'],
            'old-copier','migration-reviewed-owned-build',timeout=900,campaign=Campaign())
    finally:
        target=RAW/'active/old-copier';receipts=RAW/'old-copier/build-receipts';receipts.mkdir(parents=True)
        files={}
        for name in ['task-owned.json','acquisition.json','runtime.json','build.json','wheels.json','source.tar.gz']:
            source=target/name
            if not source.is_file():continue
            destination=receipts/name;shutil.copyfile(source,destination)
            if sha256(source)!=sha256(destination):raise RuntimeError('actual setup receipt copy differs')
            files[name]=sha256(destination)
        immutable_json(receipts/'index.json',dict(files=files,scope='Actual owned setup receipts; no scenario credit.'))
    print('Original Copier native owned runtime prepared; Playtestr remains exact downloaded archive bytes.')


if __name__=='__main__':asyncio.run(main())
