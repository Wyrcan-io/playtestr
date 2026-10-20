"""Prepare exact Rust only inside the owned Yazi root; no target compilation."""
import asyncio
import os
from pathlib import Path
import shutil

from readiness_evidence import RAW, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_helix_environment import environment
from readiness_old_helix_build import run


async def main():
    if os.name!='nt':raise RuntimeError('this local prerequisite route is Windows only')
    target=RAW/'active/old-yazi';review=load(target/'source-review.json')
    if (target/'build.json').exists():raise RuntimeError('prerequisite preparation refuses built target')
    env=environment('yazi')
    if int(env['SOURCE_DATE_EPOCH'])!=review['source_date_epoch']:raise RuntimeError('reviewed reproducible epoch differs')
    rustup=shutil.which('rustup')
    if rustup is None:raise RuntimeError('read-only Rustup prerequisite missing')
    rustup=Path(rustup);rustup_before=sha256(rustup)
    installed=await run('migration-owned-exact-rust-toolchain',[rustup,'toolchain','install','1.99.0',
        '--profile','minimal','--no-self-update'],env,600,project='yazi')
    tools=target/'rustup-home/toolchains/1.99.0-x86_64-pc-windows-msvc/bin'
    compiler=tools/'rustc.exe';cargo=tools/'cargo.exe'
    for tool in [compiler,cargo]:
        row=await run('migration-owned-tool-identity-'+tool.stem,[tool,'-Vv'],env,30,project='yazi')
        if 'release: 1.99.0' not in row['output'] or 'host: x86_64-pc-windows-msvc' not in row['output']:
            raise RuntimeError('owned original Rust tool differs')
    if sha256(rustup)!=rustup_before:raise RuntimeError('global read-only Rustup changed')
    immutable_json(target/'toolchain.json',dict(rustc_path=str(compiler),rustc_sha256=sha256(compiler),
        cargo_path=str(cargo),cargo_sha256=sha256(cargo),rustup_sha256=rustup_before,
        native_triple='x86_64-pc-windows-msvc',rust_version='1.99.0',installation_attempt=installed['id'],
        installed_globally=False,source_date_epoch=review['source_date_epoch'],
        scope='Owned compiler/Cargo prerequisites only; no Yazi target build or runtime credit.'))
    print('Exact owned Rust 1.99.0 prerequisites prepared; global Rust installation unchanged.')


if __name__=='__main__':asyncio.run(main())
