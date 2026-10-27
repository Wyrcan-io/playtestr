"""Fetch locked Rust inputs without running target code or Cargo build scripts."""
import argparse
import asyncio
import os
from pathlib import Path
import tomllib
import uuid

from adversarial_process import execute
from next20_check import RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256
from readiness_build_plop import usage


def environment(target):
    target.resolve(strict=True).relative_to((RAW/'active').resolve(strict=True))
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','SYSTEMDRIVE',
        'PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432'}}
    for key,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
        ('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),
        ('XDG_DATA_HOME','home/data'),('CARGO_HOME','cargo-home'),
        ('RUSTUP_HOME','rustup-home'),('CARGO_TARGET_DIR','cargo-target')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
    env.update(RUSTUP_AUTO_INSTALL='0',CARGO_BUILD_JOBS='2',CARGO_INCREMENTAL='0',
        CARGO_PROFILE_RELEASE_DEBUG='0',CARGO_PROFILE_RELEASE_LTO='false',
        CARGO_NET_RETRY='0',CARGO_HTTP_TIMEOUT='30',CARGO_HTTP_MULTIPLEXING='false',
        GIT_CEILING_DIRECTORIES=str(target),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    env['PSModuleAnalysisCachePath']=str(RAW/'shell-cache/module-analysis')
    return env


def short_owned_path(path):
    """Spell an existing owned Windows path with its native 8.3 components."""
    resolved=Path(path).resolve(strict=True)
    resolved.relative_to(RAW.resolve(strict=True))
    if os.name!='nt':return str(resolved)
    import ctypes
    buffer=ctypes.create_unicode_buffer(32768)
    length=ctypes.windll.kernel32.GetShortPathNameW(str(resolved),buffer,len(buffer))
    if not 0<length<len(buffer) or Path(buffer.value).resolve(strict=True)!=resolved:
        raise ValueError('native short spelling does not resolve to the exact owned path')
    return buffer.value


def materialize_short_cache(target,dependencies,catalog):
    """Copy the already reviewed cache into a physically shorter owned root."""
    import json
    import shutil
    cache=RAW/'r'
    owner=dict(schema_version=1,workspace=str(ROOT),project='cargo-generate',
        source_target=str(target),catalog_sha256=sha256(target/'dependency-source-catalog.json'))
    if cache.exists():
        if json.loads((cache/'task-owned.json').read_text())!=owner:
            raise ValueError('short compiler cache has a different owner')
        receipt=json.loads((cache/'materialized.json').read_text())
    else:
        cache.mkdir();immutable_json(cache/'task-owned.json',owner)
        shutil.copytree(target/'cargo-home/registry',cache/'registry')
        receipt=dict(schema_version=1,owner_sha256=sha256(cache/'task-owned.json'),
            original_source_catalog_sha256=owner['catalog_sha256'],
            files={name.removeprefix('cargo-home/'):digest for name,digest in catalog['files'].items()},
            archives={name.removeprefix('cargo-home/'):row['sha256'] for name,row in dependencies['files'].items()},
            scope='Exact already reviewed dependency bytes; physical short path for MSVC; no fetch or source changes.')
        for name,digest in {**receipt['files'],**receipt['archives']}.items():
            if sha256(cache/name)!=digest:raise ValueError('short cache copy differs')
        immutable_json(cache/'materialized.json',receipt)
        immutable_json(target/'short-cache-reference.json',dict(root=str(cache),
            owner_sha256=sha256(cache/'task-owned.json'),materialized_sha256=sha256(cache/'materialized.json')))
    for name,digest in {**receipt['files'],**receipt['archives']}.items():
        if sha256(cache/name)!=digest:raise ValueError('actual short cache changed')
    return cache


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('project',choices=['cargo-generate'])
    parser.add_argument('--native-host',action='store_true');args=parser.parse_args();target=RAW/'active'/args.project
    if (target/'dependency-fetch-review.json').exists():raise ValueError('refuse replacing dependency receipt')
    import json
    owner=json.loads((target/'task-owned.json').read_text())
    if owner['workspace']!=str(ROOT) or owner['slug']!=args.project or not owner['source_only']:
        raise ValueError('unreviewed source ownership')
    source=target/'src';lock=source/'Cargo.lock';before=sha256(lock)
    packages=tomllib.loads(lock.read_text())['package']
    registry='registry+https://github.com/rust-lang/crates.io-index'
    if any(p.get('source') not in {None,registry} for p in packages):raise ValueError('unreviewed dependency source')
    expected={p['name']+'-'+p['version']+'.crate':p['checksum'] for p in packages if p.get('source')==registry}
    if os.name!='nt' and not args.native_host:raise ValueError('explicit native-host fetch required outside Windows')
    triple='x86_64-pc-windows-msvc' if os.name=='nt' else 'x86_64-unknown-linux-gnu'
    tools=Path.home()/('.rustup/toolchains/stable-'+triple+'/bin');suffix='.exe' if os.name=='nt' else ''
    compiler=tools/('rustc'+suffix);cargo=tools/('cargo'+suffix)
    if not compiler.is_file() or not cargo.is_file():raise ValueError('installed read-only stable native Rust prerequisite missing')
    env=environment(target);env.update(RUSTC=str(compiler),RUSTDOC=str(tools/('rustdoc'+suffix)))
    env['PATH']=str(tools)+os.pathsep+env['PATH']
    attempts=[];samples=[]
    async def run(argv,label,timeout):
        task=asyncio.create_task(execute(argv,args.project,label,cwd=source,env=env,
            timeout=timeout,campaign=NextCampaign()))
        try:
            while not task.done():
                size=await asyncio.to_thread(usage,RAW);samples.append(size)
                # Leave over two GiB headroom for the unchanged historical root.
                if size>2*1024**3:raise ValueError('Rust fetch raw storage stop')
                await asyncio.sleep(2)
            result=await task;attempts.append(result['id']);return result
        finally:
            if not task.done():
                task.cancel()
                try:await task
                except asyncio.CancelledError:pass
    try:
        for tool in [compiler,cargo]:
            probe=await run([tool,'-Vv'],'rust-read-only-prerequisite-'+tool.stem,30)
            if args.native_host and tool==compiler and ('host: '+triple) not in probe['output'].splitlines():
                raise ValueError('installed Rust compiler is not native for this declared host')
        await run([cargo,'fetch','--locked','--manifest-path',source/'Cargo.toml',
            '--target','x86_64-pc-windows-msvc','--target','x86_64-unknown-linux-gnu'],
            'rust-owned-locked-source-fetch',600)
        if sha256(lock)!=before:raise ValueError('dependency lock changed')
        files={}
        for path in (target/'cargo-home/registry/cache').rglob('*.crate'):
            if path.stat().st_size>32*1024**2 or path.name not in expected or sha256(path)!=expected[path.name]:
                raise ValueError('locked dependency checksum differs: '+path.name)
            files[path.relative_to(target).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha256(path))
        if not files or sum(r['bytes'] for r in files.values())>512*1024**2:raise ValueError('dependency archive bound')
        hooks={}
        for manifest in (target/'cargo-home/registry/src').glob('*/*/Cargo.toml'):
            package=tomllib.loads(manifest.read_text(encoding='utf-8'))['package']
            declared=package.get('build');hook=manifest.parent/(declared if isinstance(declared,str) else 'build.rs')
            if declared is False or not hook.is_file():continue
            hook.resolve(strict=True).relative_to(manifest.parent.resolve())
            if hook.stat().st_size>128*1024:raise ValueError('hook review bound')
            hooks[hook.relative_to(target).as_posix()]=sha256(hook)
        immutable_json(target/'dependency-fetch-review.json',dict(schema_version=1,
            lock_sha256=before,files=files,build_hooks=hooks,attempts=attempts,
            rustc_path=str(compiler),rustc_sha256=sha256(compiler),cargo_path=str(cargo),
            cargo_sha256=sha256(cargo),build_hooks_executed=False,target_executed=False,
            policy='Source fetch only; exact hook review and offline build authorization remain pending.'))
        print('Fetched',len(files),'checksum-verified archives;',len(hooks),'hooks require review; no builds executed.')
    finally:
        immutable_json(target/('fetch-storage-'+uuid.uuid4().hex+'.json'),dict(observed_raw_bytes=samples,
            scope='Periodic logical samples, not an exact peak or filesystem quota.'))


if __name__=='__main__':asyncio.run(main())
