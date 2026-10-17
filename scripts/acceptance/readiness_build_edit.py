"""Build the reviewed ordinary stable editor with locked offline dependencies."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_edit_environment import build_environment
from readiness_evidence import Campaign,immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',default='initial');args=parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',args.label):raise RuntimeError('invalid editor build label')
    active,cargo,triple,env=build_environment();source=active/'src'
    dependencies=json.loads((active/'dependencies.json').read_text())
    if sha256(source/'Cargo.lock')!=dependencies['lock_sha256']:raise RuntimeError('reviewed dependency lock changed')
    for name,record in dependencies['files'].items():
        if sha256(active/name)!=record['sha256']:raise RuntimeError('reviewed dependency archive changed')
    env.update(CARGO_NET_OFFLINE='true',EDIT_CFG_LANGUAGES='en')
    resource={}
    if os.name=='nt':
        kits=Path(os.environ['ProgramFiles(x86)'])/'Windows Kits/10/bin'
        choices=sorted(kits.glob('10.*/x64/rc.exe'),key=lambda p:tuple(map(int,p.parents[1].name.split('.'))))
        if not choices:raise RuntimeError('installed Windows resource compiler missing; no installation attempted')
        compiler=choices[-1];env['RC_PATH']=str(compiler);resource=dict(path=str(compiler),sha256=sha256(compiler))
    hooks=[source/'crates/edit/build/main.rs',source/'crates/edit/build/i18n.rs',source/'crates/edit/build/helpers.rs',
        source/'crates/lsh/src/compiler/mod.rs',source/'crates/lsh/src/compiler/generator.rs']
    if os.name=='nt':hooks.extend((active/'cargo-home/registry/src').glob('*/winresource-0.1.31/lib.rs'))
    review=active/'build-review.json'
    if not review.exists():
        immutable_json(review,dict(reviewed_files={p.relative_to(active).as_posix():sha256(p) for p in hooks},
            policy='Generate pinned LSH/i18n in Cargo OUT_DIR; native resource compiler writes OUT_DIR; registry discovery reads only. No network build hooks. Fetched dev/test hooks excluded from release dependency graph.',
            dependencies_sha256=sha256(active/'dependencies.json'),stable_build=True,bootstrap=False,
            build_options=['--release','--locked','--offline','-p','edit','--bin','edit'],languages='en',resource_compiler=resource))
    reviewed=json.loads(review.read_text())
    if any(sha256(active/name)!=digest for name,digest in reviewed['reviewed_files'].items()):raise RuntimeError('reviewed build hook changed')
    operation=asyncio.create_task(execute([cargo,'build','--manifest-path',source/'Cargo.toml','--release','--locked','--offline',
        '--target',triple,'-p','edit','--bin','edit'],'edit',args.label+'-reviewed-stable-offline-build',
        cwd=source,env=env,timeout=900,campaign=Campaign()))
    sizes=[]
    try:
        while not operation.done():
            size=await asyncio.to_thread(usage,active);sizes.append(size)
            if size>3*1024**3:raise RuntimeError('editor build growth stopped below four-GiB ceiling')
            await asyncio.sleep(2)
        built=await operation
    finally:
        if not operation.done():
            operation.cancel()
            try:await operation
            except asyncio.CancelledError:pass
    binary=active/'target'/triple/'release'/('edit.exe' if os.name=='nt' else 'edit')
    if not binary.is_file():raise RuntimeError('reviewed build produced no editor')
    version=await execute([binary,'--version'],'edit',args.label+'-built-editor-version',cwd=source,env=env,
        timeout=30,campaign=Campaign())
    if '2.0.0' not in version['output']:raise RuntimeError('wrong pinned editor version')
    output=active/'build.json' if args.label=='initial' else active/'build-revisions'/(args.label+'-'+uuid.uuid4().hex+'.json')
    immutable_json(output,dict(pin='cb6de0a8966aecd01d19a3541dab1829d0e679ca',binary_relative_path=binary.relative_to(active).as_posix(),
        binary_sha256=sha256(binary),build_attempt=built['id'],version_attempt=version['id'],version=version['output'].strip(),
        native_triple=triple,dependencies_sha256=sha256(active/'dependencies.json'),review_sha256=sha256(review),
        lock_sha256=sha256(source/'Cargo.lock'),license_sha256=sha256(source/'LICENSE'),resource_compiler=resource,
        active_bytes_observed=sizes,stable_build=True,bootstrap=False,languages='en'))
    print('Built pinned editor with ordinary stable Rust and owned offline dependencies:',binary)


if __name__=='__main__':asyncio.run(main())
