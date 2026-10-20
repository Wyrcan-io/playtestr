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
        immutable_json(RAW/'old-superfile-runtime-baseline.json',
            await runtime_inventory('old-superfile','migration-owned-runtime-baseline'))
    await execute([sys.executable,'scripts/acceptance/readiness_acquire_old.py','--project','superfile'],
        'old-superfile','migration-original-pinned-source-acquisition',timeout=180,campaign=Campaign())
    try:
        await execute([sys.executable,'scripts/acceptance/readiness_old_go_prepare.py','--project','superfile'],
            'old-superfile','migration-reviewed-owned-build',timeout=900,campaign=Campaign())
    finally:
        target=RAW/'active/old-superfile';receipts=RAW/'old-superfile/build-receipts';receipts.mkdir(parents=True)
        files={}
        for name in ['task-owned.json','acquisition.json','runtime.json','build.json','wheels.json','toolchain/sdk.json']:
            source=target/name
            if not source.is_file():continue
            destination=receipts/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
            if sha256(source)!=sha256(destination):raise RuntimeError('actual setup receipt copy differs')
            files[name]=sha256(destination)
        archive=target/'source.tar.gz'
        if archive.is_file():immutable_json(receipts/'canonical-source-reference.json',dict(
            archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
            canonical_campaign_path='old-superfile/retained-source/source.tar.gz',
            scope='Canonical original archive retained once locally. Native upload excludes duplicate source archive bytes; actual acquisition and retained-source index must independently match this reference.'))
        immutable_json(receipts/'index.json',dict(files=files,scope='Actual owned setup receipts; no scenario credit.'))
    print('Original superfile native owned runtime prepared; Playtestr remains exact downloaded archive bytes.')


if __name__=='__main__':asyncio.run(main())
