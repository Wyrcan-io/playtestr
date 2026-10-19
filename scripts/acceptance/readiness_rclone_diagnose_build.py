"""Bounded single locked dependency diagnostic after the first cold-build timeout."""
import asyncio
import json
import os

from adversarial_process import execute
from readiness_build_rclone import environment
from readiness_evidence import Campaign, RAW, immutable_json


async def main():
    target = RAW/'active/rclone'
    go = target/'toolchain/go/bin'/('go.exe' if os.name == 'nt' else 'go')
    module, version = 'github.com/unknwon/goconfig', 'v1.0.0'
    result = await execute([go, 'mod', 'download', '-json', module+'@'+version],
        'rclone', 'single-locked-small-dependency-diagnostic', cwd=target/'src',
        env=environment(target), timeout=90, campaign=Campaign())
    record = json.loads(result['output'])
    line = module+' '+version+' '+record['Sum']
    if line not in (target/'src/go.sum').read_text().splitlines():
        raise RuntimeError('diagnostic dependency differs from original lock')
    immutable_json(target/'small-dependency-diagnostic.json', dict(module=module, version=version,
        checksum=record['Sum'], attempt=result['id'], elapsed_seconds=result.get('seconds'),
        qualification='Dependency transport/checksum diagnostic only; original full build timed out.'))
    print('Small locked dependency downloaded and verified; inspect original full-build failure separately.')


if __name__ == '__main__':
    asyncio.run(main())
