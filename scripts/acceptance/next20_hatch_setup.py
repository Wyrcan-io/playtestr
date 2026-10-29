"""Bounded Hatch setup stages; downloaded code is never imported for review."""
import asyncio
import json
import os
import zipfile

from adversarial_process import execute
from next20_check import RAW,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    target=RAW/'active/hatch';wheels=target/'wheels'
    marker=json.loads((target/'task-owned.json').read_text())
    if marker['slug']!='hatch' or marker['pin']!='ad6d66e7c5dba7deea7601e50072676defae8b3e':raise ValueError('unexpected Hatch source')
    original=json.loads((target/'dependency-fetch.json').read_text())['wheels']
    if set(p.name for p in wheels.iterdir())!=set(original):raise ValueError('preserve unknown/completed supplemental fetch')
    for name,row in original.items():
        if sha256(wheels/name)!=row['sha256']:raise ValueError('original wheel changed')
    backend=next(wheels.glob('hatchling-*.whl'))
    with zipfile.ZipFile(backend) as archive:
        source=archive.read('hatchling/builders/constants.py')
        if b'EDITABLES_REQUIREMENT = "editables~=0.3"' not in source:raise ValueError('backend editable requirement changed')
    immutable_json(target/'editable-fetch-declaration.json',dict(schema_version=1,
        backend_wheel_sha256=sha256(backend),backend_constants_sha256=__import__('hashlib').sha256(source).hexdigest(),
        original_fetch_sha256=sha256(target/'dependency-fetch.json'),requirement='editables~=0.3',
        approved_for_install=False,scope='One wheel-only backend-declared editable-build prerequisite; no imports or build execution.'))
    python=target/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    await execute([python,'-B','-m','pip','download','--only-binary=:all:','--dest',wheels,'editables~=0.3'],
        'hatch','wheel-only-editable-build-prerequisite',cwd=target,env=environment(target),timeout=180,campaign=NextCampaign())
    inventory={}
    for path in sorted(wheels.iterdir()):
        if path.suffix!='.whl' or path.stat().st_size>32*1024**2:raise ValueError('supplemental wheel bound')
        inventory[path.name]=dict(bytes=path.stat().st_size,sha256=sha256(path))
    if not set(original)<set(inventory) or len(inventory)!=len(original)+1 or any(inventory[n]!=r for n,r in original.items()):raise ValueError('unexpected additional wheel closure')
    immutable_json(target/'dependency-fetch-v2.json',dict(schema_version=1,wheels=inventory,
        original_fetch_sha256=sha256(target/'dependency-fetch.json'),editable_fetch_declaration_sha256=sha256(target/'editable-fetch-declaration.json'),
        approved_for_install=False,target_hooks_executed=False))
    print('Retained original42-wheel acquisition; added one backend-declared editable wheel for separate review.')


if __name__=='__main__':asyncio.run(main())
