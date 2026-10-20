"""Fetch original Unix Broot dependencies without building a Windows target."""
import asyncio
import os
from pathlib import Path

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, immutable_json
from readiness_old_helix_environment import environment
from readiness_old_helix_fetch_review import fetch


async def main():
    if os.name!='nt':raise RuntimeError('local source-only prerequisite route requires Windows')
    target=RAW/'active/old-broot'
    if not (target/'source-review.json').is_file() or (target/'build.json').exists():
        raise RuntimeError('reviewed unbuilt source required')
    tools=Path.home()/'.rustup/toolchains/stable-x86_64-pc-windows-msvc/bin'
    compiler=tools/'rustc.exe';cargo=tools/'cargo.exe'
    env=environment('broot');env.update(RUSTC=str(compiler),RUSTDOC=str(tools/'rustdoc.exe'))
    env['PATH']=str(tools)+os.pathsep+env['PATH']
    for tool in [compiler,cargo]:
        row=await execute([tool,'-Vv'],'old-broot','migration-read-only-fetch-tool-'+tool.stem,
            env=env,timeout=30,campaign=Campaign())
        if '1.97.1' not in row['output']:raise RuntimeError('original Rust tool version differs')
    receipt=await fetch(cargo,compiler,env,['x86_64-unknown-linux-gnu','aarch64-apple-darwin'],project='broot')
    immutable_json(target/'dependency-fetch-review.json',receipt)
    print('Fetched',len(receipt['files']),'locked archives;',len(receipt['build_hooks']),'hooks await review. No build/runtime credit.')


if __name__=='__main__':asyncio.run(main())
