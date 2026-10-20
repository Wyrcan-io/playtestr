"""Fetch both original native dependency sets without executing build hooks."""
import asyncio
import os
from pathlib import Path
import tomllib

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_helix_environment import environment


async def fetch(cargo,compiler,env,targets,project='helix'):
    if project not in {'helix','broot'}:raise RuntimeError('undeclared original Rust dependency scope')
    target=RAW/'active'/('old-'+project);source=target/'src';lock=source/'Cargo.lock'
    before=sha256(lock);packages=tomllib.loads(lock.read_text())['package']
    expected={p['name']+'-'+p['version']+'.crate':p['checksum'] for p in packages if p.get('source')}
    if any(p.get('source') not in {None,'registry+https://github.com/rust-lang/crates.io-index'} for p in packages):
        raise RuntimeError('unreviewed Cargo dependency source')
    calls=[]
    for triple in targets:
        operation=asyncio.create_task(execute([cargo,'fetch','--manifest-path',source/'Cargo.toml','--locked','--target',triple],
            'old-'+project,'migration-owned-locked-fetch-'+triple,cwd=source,env=env,timeout=300,campaign=Campaign()))
        try:
            while not operation.done():
                if await asyncio.to_thread(usage,target)>3*1024**3:raise RuntimeError('owned Rust fetch storage stop')
                await asyncio.sleep(2)
            result=await operation
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
        calls.append(result['id'])
    if sha256(lock)!=before:raise RuntimeError('original locked dependencies changed')
    files={}
    for path in (target/'cargo-home/registry/cache').rglob('*.crate'):
        if path.stat().st_size>32*1024**2 or path.name not in expected or sha256(path)!=expected[path.name]:
            raise RuntimeError('fetched crate checksum/size differs from original lock')
        files[path.relative_to(target).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha256(path))
    if not files or sum(r['bytes'] for r in files.values())>512*1024**2:raise RuntimeError('dependency cache bound')
    hooks={}
    for manifest in (target/'cargo-home/registry/src').glob('*/*/Cargo.toml'):
        package=tomllib.loads(manifest.read_text(encoding='utf-8'))['package'];declared=package.get('build')
        hook=manifest.parent/(declared if isinstance(declared,str) else 'build.rs')
        if declared is False or not hook.is_file():continue
        hook.resolve(strict=True).relative_to(manifest.parent.resolve())
        if hook.stat().st_size>128*1024:raise RuntimeError('dependency hook review bound')
        hooks[manifest.parent.name+'/'+hook.relative_to(manifest.parent).as_posix()]=sha256(hook)
    return dict(lock_sha256=before,files=files,build_hooks=hooks,fetch_attempts=calls,
        cargo_path=str(cargo),cargo_sha256=sha256(cargo),rustc_path=str(compiler),rustc_sha256=sha256(compiler),
        targets=targets,build_hooks_executed=False)


async def main():
    if os.name!='nt':raise RuntimeError('local prerequisite review route is Windows; native setup uses explicit owned tools')
    target=RAW/'active/old-helix'
    if (target/'build.json').exists():raise RuntimeError('fetch review refuses an already built target')
    tools=Path.home()/'.rustup/toolchains/stable-x86_64-pc-windows-msvc/bin'
    compiler=tools/'rustc.exe';cargo=tools/'cargo.exe'
    if not compiler.is_file() or not cargo.is_file():raise RuntimeError('read-only installed Rust prerequisites missing')
    env=environment();env.update(RUSTC=str(compiler),RUSTDOC=str(tools/'rustdoc.exe'))
    env['PATH']=str(tools)+os.pathsep+env['PATH']
    for tool in [compiler,cargo]:
        await execute([tool,'-Vv'],'old-helix','migration-read-only-fetch-tool-'+tool.stem,
            env=env,timeout=30,campaign=Campaign())
    receipt=await fetch(cargo,compiler,env,['x86_64-pc-windows-msvc','x86_64-unknown-linux-gnu'])
    immutable_json(target/'dependency-fetch-review.json',receipt)
    print('Fetched',len(receipt['files']),'locked archives; review',len(receipt['build_hooks']),
        'dependency hooks before target compilation. No target build or runtime credit.')


if __name__=='__main__':asyncio.run(main())
