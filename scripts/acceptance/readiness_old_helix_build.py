"""Compile reviewed ordinary Helix with locked offline dependencies and owned output."""
import asyncio
import os
from pathlib import Path
import re
import shutil
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_helix_environment import environment


async def run(label,argv,env,timeout=120,expected=0,project='helix'):
    if project not in {'helix','broot'}:raise RuntimeError('undeclared original Rust command scope')
    target=RAW/'active'/('old-'+project);sizes=[]
    operation=asyncio.create_task(execute(argv,'old-'+project,label,cwd=target/'src',env=env,
        timeout=timeout,expected=expected,campaign=Campaign()))
    try:
        while not operation.done():
            size=await asyncio.to_thread(usage,target);sizes.append(size)
            if size>3*1024**3:raise RuntimeError('owned Helix build exceeds three-GiB stop')
            await asyncio.sleep(2)
        return await operation
    finally:
        if not operation.done():
            operation.cancel()
            try:await operation
            except asyncio.CancelledError:pass
        immutable_json(target/('storage-'+uuid.uuid4().hex+'.json'),dict(observed_bytes=sizes,
            scope='Periodic owned logical bytes, not exact peak or OS quota.'))


def build_environment(project='helix'):
    target=RAW/'active'/('old-'+project);runtime=load(target/'runtime.json');env=environment(project)
    compiler=Path(runtime['rustc_path']);cargo=Path(runtime['cargo_path'])
    if sha256(compiler)!=runtime['rustc_sha256'] or sha256(cargo)!=runtime['cargo_sha256']:
        raise RuntimeError('actual Rust/Cargo prerequisite changed')
    env.update(RUSTC=str(compiler),RUSTDOC=str(compiler.with_name('rustdoc.exe' if os.name=='nt' else 'rustdoc')),
        CARGO_NET_OFFLINE='true')
    env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    Path(env['CARGO_TARGET_DIR']).resolve().relative_to(target.resolve())
    return target,runtime,cargo,env


async def compile_target(label,*,clean=False,project='helix'):
    target,runtime,cargo,env=build_environment(project);triple=runtime['native_triple']
    package,binary_name={'helix':('helix-term','hx'),'broot':('broot','broot')}[project]
    if clean:
        cleared=await run(label+'-invalidate-'+package,[cargo,'clean','--locked','--offline','--profile','release',
            '--target',triple,'-p',package],env,120,project=project)
        count=re.search(r'Removed\s+([0-9]+)\s+files?',cleared['output'])
        if count is None or int(count.group(1))==0:raise RuntimeError('compiled package invalidation lacks positive evidence')
    command=[cargo,'rustc' if os.name=='nt' else 'build','--locked','--offline','--profile','release',
        '--target',triple,'-p',package,'--bin',binary_name]
    if os.name=='nt':command+=['--','-C','link-arg=/Brepro']
    result=await run(label,command,env,900,project=project)
    built=target/'cargo-target'/triple/'release'/(binary_name+('.exe' if os.name=='nt' else ''))
    binary=target/'bin'/built.name;binary.parent.mkdir(exist_ok=True);shutil.copyfile(built,binary)
    if os.name!='nt':binary.chmod(0o755)
    return result,binary


async def main():
    target=RAW/'active/old-helix';source=target/'src'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/helix'
    review=load(docs/'source-review.json');hooks=load(docs/'dependency-hook-review.json')
    owner=load(target/'task-owned.json')
    if owner['workspace']!=str(ROOT) or owner['pin']!=review['pin'] or owner['project']!=review['repository']:
        raise RuntimeError('unowned original Helix target')
    if (target/'build.json').exists():raise RuntimeError('refuse completed original Helix build')
    for name,digest in review['reviewed_inputs'].items():
        if sha256(source/name)!=digest:raise RuntimeError('original source changed before compilation')
    dependencies=load(target/('dependencies.json' if (target/'dependencies.json').exists() else 'dependency-fetch-review.json'))
    if dependencies['lock_sha256']!=hooks['source_lock_sha256'] or sha256(source/'Cargo.lock')!=dependencies['lock_sha256']:
        raise RuntimeError('original dependency lock changed')
    for name,digest in dependencies['build_hooks'].items():
        matches=list((target/'cargo-home/registry/src').glob('*/'+name))
        if hooks['reviewed_hook_sha256'].get(name)!=digest or len(matches)!=1 or sha256(matches[0])!=digest:
            raise RuntimeError('unreviewed or changed dependency build hook')
    for name,row in dependencies['files'].items():
        if sha256(target/name)!=row['sha256'] or hooks['registry_archives_sha256'].get(Path(name).name)!=row['sha256']:
            raise RuntimeError('reviewed dependency archive changed')
    if not (target/'runtime.json').exists():
        if os.name!='nt':raise RuntimeError('native prerequisite setup receipt required')
        compiler=Path(dependencies['rustc_path']);cargo=Path(dependencies['cargo_path']);env=environment()
        version=await run('migration-exact-installed-rust-identity',[compiler,'-Vv'],env,30)
        if 'release: 1.97.1' not in version['output'] or 'host: x86_64-pc-windows-msvc' not in version['output']:
            raise RuntimeError('installed compiler differs from original native profile')
        immutable_json(target/'runtime.json',dict(rustc_path=str(compiler),rustc_sha256=sha256(compiler),
            cargo_path=str(cargo),cargo_sha256=sha256(cargo),native_triple='x86_64-pc-windows-msvc',
            read_only_installed_prerequisites=True,installed_globally=False,rust_version_attempt=version['id']))
    target,runtime,cargo,env=build_environment()
    git=shutil.which('git')
    if git is None:raise RuntimeError('installed Git prerequisite missing')
    await run('migration-source-git-ceiling',[git,'rev-parse','--show-toplevel'],env,30,128)
    result,binary=await compile_target('migration-reviewed-original-helix-build')
    resources=target/'bin/runtime'
    shutil.copytree(source/'runtime',resources,ignore=shutil.ignore_patterns('grammars'))
    resource_inputs={p.relative_to(resources).as_posix():sha256(p) for p in resources.rglob('*') if p.is_file()}
    version=await run('migration-actual-original-helix-version',[binary,'--version'],env,30)
    if 'ba40e547' not in version['output']:raise RuntimeError('built version not bound to original Helix pin')
    for name,digest in review['reviewed_inputs'].items():
        if sha256(source/name)!=digest:raise RuntimeError('build changed original source')
    immutable_json(target/'build.json',dict(pin=review['pin'],binary_relative_path=binary.relative_to(target).as_posix(),
        binary_sha256=sha256(binary),build_attempt=result['id'],version_attempt=version['id'],
        source_review_sha256=sha256(docs/'source-review.json'),hook_review_sha256=sha256(docs/'dependency-hook-review.json'),
        native_triple=runtime['native_triple'],rustc_sha256=runtime['rustc_sha256'],cargo_sha256=runtime['cargo_sha256'],
        runtime_resources=resource_inputs,grammar_acquisition=False,installed_globally=False,
        windows_reproducible_link=os.name=='nt',profile='release; two jobs; no LTO/debug/incremental artifacts'))
    print('Built original native plain-text Helix with reviewed offline dependencies and owned output.')


if __name__=='__main__':asyncio.run(main())
