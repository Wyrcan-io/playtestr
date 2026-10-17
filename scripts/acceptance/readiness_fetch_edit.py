"""Fetch locked dependencies without executing target/dependency build hooks."""
import asyncio
import json
from pathlib import Path
import tomllib

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_edit_environment import build_environment
from readiness_evidence import Campaign,immutable_json,sha256


async def main():
    active,cargo,triple,env=build_environment();source=active/'src';lock=source/'Cargo.lock';before=sha256(lock)
    packages=tomllib.loads(lock.read_text())['package']
    expected={p['name']+'-'+p['version']+'.crate':p['checksum'] for p in packages if 'source' in p}
    if any(p.get('source') not in {None,'registry+https://github.com/rust-lang/crates.io-index'} for p in packages):
        raise RuntimeError('unreviewed Cargo dependency source')
    version=await execute([env['RUSTC'],'-Vv'],'edit','installed-stable-rust-identity',env=env,timeout=30,campaign=Campaign())
    cargo_version=await execute([cargo,'-Vv'],'edit','installed-stable-cargo-identity',env=env,timeout=30,campaign=Campaign())
    operation=asyncio.create_task(execute([cargo,'fetch','--manifest-path',source/'Cargo.toml','--locked','--target',triple],
        'edit','owned-locked-dependency-fetch-no-build-hooks',cwd=source,env=env,timeout=240,campaign=Campaign()))
    sizes=[]
    try:
        while not operation.done():
            size=await asyncio.to_thread(usage,active);sizes.append(size)
            if size>3*1024**3:raise RuntimeError('owned Cargo growth stopped below four-GiB ceiling')
            await asyncio.sleep(2)
        fetched=await operation
    finally:
        if not operation.done():
            operation.cancel()
            try:await operation
            except asyncio.CancelledError:pass
    if sha256(lock)!=before:raise RuntimeError('locked dependency input changed')
    files={}
    for path in (active/'cargo-home/registry/cache').rglob('*.crate'):
        if path.stat().st_size>32*1024**2 or path.name not in expected or sha256(path)!=expected[path.name]:
            raise RuntimeError('downloaded dependency checksum or size mismatch')
        files[path.relative_to(active).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha256(path))
    if not files or sum(p['bytes'] for p in files.values())>512*1024**2:raise RuntimeError('dependency cache bound')
    hooks=[]
    for path in (active/'cargo-home/registry/src').glob('*/*/Cargo.toml'):
        package=tomllib.loads(path.read_text())['package'];declared=package.get('build')
        build=path.parent/(declared if isinstance(declared,str) else 'build.rs')
        if declared is not False and build.is_file():hooks.append(dict(path=build.relative_to(active).as_posix(),sha256=sha256(build)))
    immutable_json(active/'dependencies.json',dict(lock_sha256=before,files=files,build_hooks=hooks,
        source_fetch_attempt=fetched['id'],rust_identity_attempt=version['id'],cargo_identity_attempt=cargo_version['id'],
        rustc_sha256=sha256(Path(env['RUSTC'])),cargo_sha256=sha256(cargo),native_triple=triple,
        active_bytes_observed=sizes,build_hooks_executed=False,source_acquisition_sha256=sha256(active/'acquisition.json')))
    print('Fetched and checksum-verified',len(files),'locked dependency archives; review',len(hooks),'hooks before building.')


if __name__=='__main__':asyncio.run(main())
