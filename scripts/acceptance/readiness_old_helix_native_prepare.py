"""Prepare original native Rust prerequisites and reviewed dependency set."""
import asyncio
import os
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
    if os.name!='nt':
        immutable_json(RAW/'old-helix-runtime-baseline.json',await runtime_inventory('old-helix','migration-owned-runtime-baseline'))
    await execute([sys.executable,ROOT/'scripts/acceptance/readiness_acquire_old.py','--project','helix'],
        'old-helix','migration-original-pinned-source-acquisition',timeout=180,campaign=Campaign())
    target=RAW/'active/old-helix';env=environment();triple='x86_64-pc-windows-msvc' if os.name=='nt' else 'x86_64-unknown-linux-gnu'
    executable_suffix='.exe' if os.name=='nt' else ''
    roots=[Path.home()/'.rustup']
    if os.environ.get('RUSTUP_HOME'):roots.insert(0,Path(os.environ['RUSTUP_HOME']))
    compiler=None;read_only=False;version=None
    for root in roots:
        candidate=root/'toolchains'/('stable-'+triple)/('bin/rustc'+executable_suffix)
        if not candidate.is_file():continue
        checked=await run('migration-installed-rust-version-selection',[candidate,'-Vv'],env,30)
        if 'release: 1.97.1' in checked['output'] and 'host: '+triple in checked['output']:
            compiler=candidate;read_only=True;version=checked;break
    if compiler is None:
        rustup=shutil.which('rustup')
        if rustup is None:raise RuntimeError('read-only installed Rustup prerequisite missing')
        await run('migration-owned-exact-rust-toolchain',[rustup,'toolchain','install','1.97.1',
            '--profile','minimal','--no-self-update'],env,600)
        compiler=target/'rustup-home/toolchains'/('1.97.1-'+triple)/('bin/rustc'+executable_suffix)
        version=await run('migration-owned-exact-rust-identity',[compiler,'-Vv'],env,30)
        if 'release: 1.97.1' not in version['output'] or 'host: '+triple not in version['output']:
            raise RuntimeError('owned compiler differs from original native Rust profile')
    cargo=compiler.with_name('cargo'+executable_suffix)
    immutable_json(target/'runtime.json',dict(rustc_path=str(compiler),rustc_sha256=sha256(compiler),
        cargo_path=str(cargo),cargo_sha256=sha256(cargo),native_triple=triple,
        read_only_installed_prerequisites=read_only,installed_globally=False,rust_version_attempt=version['id']))
    env.update(RUSTC=str(compiler),RUSTDOC=str(compiler.with_name('rustdoc'+executable_suffix)))
    env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    dependencies=await fetch(cargo,compiler,env,[triple]);immutable_json(target/'dependencies.json',dependencies)
    hooks=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/helix/dependency-hook-review.json')
    if any(hooks['reviewed_hook_sha256'].get(n)!=h for n,h in dependencies['build_hooks'].items()):
        raise RuntimeError('native dependency hook differs from pre-build review')
    receipts=RAW/'old-helix/build-receipts';receipts.mkdir(parents=True)
    for name in ['task-owned.json','acquisition.json','runtime.json','dependencies.json']:
        shutil.copyfile(target/name,receipts/name)
        if sha256(target/name)!=sha256(receipts/name):raise RuntimeError('native setup receipt changed during copy')
    archive=target/'source.tar.gz'
    immutable_json(receipts/'canonical-source-reference.json',dict(archive_sha256=sha256(archive),
        archive_bytes=archive.stat().st_size,canonical_campaign_path='old-helix/retained-source/source.tar.gz',
        scope='Exact original source archive retained once locally; native upload excludes duplicate archive bytes.'))
    print('Original native Helix Rust and checksum-reviewed dependencies prepared; no target execution credit yet.')


if __name__=='__main__':asyncio.run(main())
