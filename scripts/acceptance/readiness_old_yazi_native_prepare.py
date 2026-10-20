"""Prepare the original Linux Rust prerequisites and reviewed dependency set."""
import asyncio
import os
import platform
from pathlib import Path
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_helix_build import run
from readiness_old_helix_environment import environment
from readiness_old_helix_fetch_review import fetch


async def main():
    if platform.system() not in {'Linux','Darwin'}:raise RuntimeError('this prerequisite helper declares native Linux/macOS only')
    immutable_json(RAW/'old-yazi-runtime-baseline.json',await runtime_inventory('old-yazi','migration-owned-runtime-baseline'))
    await execute([sys.executable,ROOT/'scripts/acceptance/readiness_acquire_old.py','--project','yazi'],
        'old-yazi','migration-original-pinned-source-acquisition',timeout=180,campaign=Campaign())
    target=RAW/'active/old-yazi'
    review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/yazi/source-review.json')
    if {p.relative_to(target/'src').as_posix():sha256(p) for p in (target/'src').rglob('*') if p.is_file()}!=review['reviewed_inputs']:
        raise RuntimeError('native Yazi source differs from reviewed archive')
    immutable_json(target/'source-review.json',review)
    env=environment('yazi');triple={'Linux':'x86_64-unknown-linux-gnu','Darwin':'aarch64-apple-darwin'}[platform.system()]
    rustup=shutil.which('rustup')
    if rustup is None:raise RuntimeError('read-only installed Rustup prerequisite missing')
    rustup_before=sha256(rustup)
    await run('migration-owned-exact-rust-toolchain',[rustup,'toolchain','install','1.99.0',
        '--profile','minimal','--no-self-update'],env,600,project='yazi')
    if sha256(rustup)!=rustup_before:raise RuntimeError('read-only Rustup prerequisite changed')
    compiler=target/'rustup-home/toolchains'/('1.99.0-'+triple)/'bin/rustc'
    version=await run('migration-owned-exact-rust-identity',[compiler,'-Vv'],env,30,project='yazi')
    if 'release: 1.99.0' not in version['output'] or 'host: '+triple not in version['output']:
        raise RuntimeError('owned compiler differs from original native Rust profile')
    cargo=compiler.with_name('cargo')
    immutable_json(target/'runtime.json',dict(rustc_path=str(compiler),rustc_sha256=sha256(compiler),
        cargo_path=str(cargo),cargo_sha256=sha256(cargo),native_triple=triple,
        read_only_installed_prerequisites=False,installed_globally=False,rust_version_attempt=version['id'],
        read_only_rustup_sha256=rustup_before))
    env.update(RUSTC=str(compiler),RUSTDOC=str(compiler.with_name('rustdoc')))
    env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    dependencies=await fetch(cargo,compiler,env,[triple],project='yazi');immutable_json(target/'dependencies.json',dependencies)
    from readiness_old_yazi_review_hooks import verify
    hooks=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/yazi/dependency-hook-review.json')
    verify(target,dependencies,hooks)
    if any(hooks['reviewed_hook_sha256'].get(n)!=h for n,h in dependencies['build_hooks'].items()):
        raise RuntimeError('native dependency hook differs from pre-build review')
    receipts=RAW/'old-yazi/build-receipts';receipts.mkdir(parents=True)
    for name in ['task-owned.json','acquisition.json','runtime.json','dependencies.json']:
        shutil.copyfile(target/name,receipts/name)
        if sha256(target/name)!=sha256(receipts/name):raise RuntimeError('native setup receipt changed during copy')
    archive=target/'source.tar.gz'
    immutable_json(receipts/'canonical-source-reference.json',dict(archive_sha256=sha256(archive),
        archive_bytes=archive.stat().st_size,canonical_campaign_path='old-yazi/retained-source/source.tar.gz',
        scope='Exact original source archive retained once locally; native upload excludes duplicate archive bytes.'))
    print('Original native Yazi Rust and checksum-reviewed dependencies prepared; no target execution credit yet.')


if __name__=='__main__':asyncio.run(main())
