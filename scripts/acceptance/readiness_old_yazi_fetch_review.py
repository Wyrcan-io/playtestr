"""Fetch all original Yazi native inputs before reviewing dependency hooks."""
import asyncio
import os
from pathlib import Path

from readiness_evidence import RAW, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_helix_environment import environment
from readiness_old_helix_fetch_review import fetch


async def main():
    target=RAW/'active/old-yazi';tools=load(target/'toolchain.json')
    if (target/'build.json').exists():raise RuntimeError('fetch review refuses compiled target')
    compiler=Path(tools['rustc_path']);cargo=Path(tools['cargo_path'])
    if sha256(compiler)!=tools['rustc_sha256'] or sha256(cargo)!=tools['cargo_sha256']:
        raise RuntimeError('owned exact Rust prerequisites changed')
    env=environment('yazi');env.update(RUSTC=str(compiler),RUSTDOC=str(compiler.with_name('rustdoc.exe')))
    env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    receipt=await fetch(cargo,compiler,env,['x86_64-pc-windows-msvc','x86_64-unknown-linux-gnu','aarch64-apple-darwin'],project='yazi')
    immutable_json(target/'dependency-fetch-review.json',receipt)
    print('Fetched',len(receipt['files']),'checksum-locked crates,',len(receipt['git_dependency']['checkouts']),
          'exact Git checkout;',len(receipt['build_hooks']),'hooks await pre-build review. No target execution credit.')


if __name__=='__main__':asyncio.run(main())
