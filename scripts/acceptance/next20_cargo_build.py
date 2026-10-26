"""Build the reviewed locked cargo-generate CLI offline in owned directories."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW,DOC,ROOT,NextCampaign
from next20_rust_fetch import environment,short_owned_path,materialize_short_cache
from readiness_build_plop import usage
from readiness_evidence import immutable_json,sha256


async def main():
    project='cargo-generate';target=RAW/'active'/project;source=target/'src';package=DOC/project
    if (target/'build.json').exists():raise ValueError('refuse replacing completed build')
    review=json.loads((package/'source-review.json').read_text())
    hooks=json.loads((package/'dependency-hook-review.json').read_text())
    dependencies=json.loads((target/'dependency-fetch-review.json').read_text())
    catalog=json.loads((target/'dependency-source-catalog.json').read_text())
    if not hooks['approved'] or hooks['source_catalog_sha256']!=sha256(target/'dependency-source-catalog.json'):
        raise ValueError('unreviewed build inputs')
    def verify():
        if sha256(source/'Cargo.lock')!=hooks['lock_sha256']:raise ValueError('changed build lock')
        for name,digest in review['reviewed_inputs'].items():
            if sha256(source/name)!=digest:raise ValueError('changed reviewed upstream source')
        for name,digest in catalog['files'].items():
            if sha256(target/name)!=digest:raise ValueError('changed reconstructed dependency source')
        for name,row in dependencies['files'].items():
            if sha256(target/name)!=row['sha256']:raise ValueError('changed locked archive')
    verify()
    compiler=Path(dependencies['rustc_path']);cargo=Path(dependencies['cargo_path'])
    if sha256(compiler)!=dependencies['rustc_sha256'] or sha256(cargo)!=dependencies['cargo_sha256']:
        raise ValueError('read-only installed compiler changed')
    env=environment(target);env.update(RUSTC=str(compiler),RUSTDOC=str(compiler.with_name('rustdoc.exe')),
        CARGO_NET_OFFLINE='true',SOURCE_DATE_EPOCH='1793030400')
    env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    cache=materialize_short_cache(target,dependencies,catalog)
    env['CARGO_HOME']=str(cache)
    # MSVC's textual relative include resolution can exceed MAX_PATH before
    # normalizing '..', even when the actual header exists. Change only native
    # spelling of these exact owned paths; do not move files or alter sources.
    for key in ['CARGO_HOME','CARGO_TARGET_DIR','TEMP','TMP','TMPDIR']:
        env[key]=short_owned_path(env[key])
    triple='x86_64-pc-windows-msvc'
    command=[cargo,'rustc','--locked','--offline','--release','--target',triple,
        '--bin','cargo-generate','--','-C','link-arg=/Brepro']
    samples=[];task=asyncio.create_task(execute(command,project,'reviewed-default-feature-native-compile',
        cwd=Path(short_owned_path(source)),env=env,timeout=1100,campaign=NextCampaign()))
    try:
        while not task.done():
            size=await asyncio.to_thread(usage,RAW);samples.append(size)
            if size>3*1024**3:raise ValueError('owned Rust build storage stop')
            await asyncio.sleep(2)
        result=await task
    finally:
        if not task.done():
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass
        immutable_json(target/('build-storage-'+uuid.uuid4().hex+'.json'),dict(observed_raw_bytes=samples,
            stop_bytes=3*1024**3,scope='Periodic logical samples, not an exact peak or filesystem quota.'))
    verify()
    built=target/'cargo-target'/triple/'release/cargo-generate.exe'
    binary=target/'bin/cargo-generate.exe';binary.parent.mkdir(exist_ok=True);shutil.copyfile(built,binary)
    digest=sha256(binary)
    immutable_json(target/'build.json',dict(schema_version=1,runtime_kind='native',
        pin=review['pin'],binary_relative_path=binary.relative_to(target).as_posix(),binary_sha256=digest,
        build_attempt=result['id'],compiler_path=str(compiler),compiler_sha256=sha256(compiler),
        cargo_path=str(cargo),cargo_sha256=sha256(cargo),native_triple=triple,features='default',
        source_review_sha256=sha256(package/'source-review.json'),
        dependency_hook_review_sha256=sha256(package/'dependency-hook-review.json'),
        dependency_source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),
        actual_short_cache_reference_sha256=sha256(target/'short-cache-reference.json'),
        dependency_fetch_review_sha256=sha256(target/'dependency-fetch-review.json'),
        compiled_files={binary.name:digest},command=list(map(str,command)),
        owned_native_path_spellings={k:env[k] for k in ['CARGO_HOME','CARGO_TARGET_DIR','TEMP','TMP','TMPDIR']},
        installed_globally=False,windows_reproducible_link=True))
    immutable_json(target/'runtime.json',dict(schema_version=1,kind='native',native=str(binary),
        native_sha256=digest,native_triple=triple,source_pin=review['pin'],
        build_sha256=sha256(target/'build.json')))
    inventory=dict(schema_version=1,runtime_root=binary.parent.relative_to(ROOT).as_posix(),files={binary.name:digest})
    immutable_json(target/'installed-inventory.json',inventory)
    immutable_json(target/'launch-runtime-catalog.json',dict(schema_version=1,
        runtime_root=binary.parent.relative_to(ROOT).as_posix(),files=inventory['files'],
        executable=binary.relative_to(ROOT).as_posix(),executable_sha256=digest,
        source_inventory_sha256=sha256(target/'installed-inventory.json')))
    version=await execute([binary,'generate','--version'],project,'actual-built-native-version',
        cwd=source,env=env,timeout=30,campaign=NextCampaign())
    if 'cargo-generate 0.25.1' not in version['output']:raise ValueError('actual built version differs')
    immutable_json(target/'version-check.json',dict(attempt=version['id'],binary_sha256=digest,
        output=version['output'],build_sha256=sha256(target/'build.json')))
    print('Built reviewed default-feature native CLI:',digest,'; version and source/dependency readback passed.')


if __name__=='__main__':asyncio.run(main())
