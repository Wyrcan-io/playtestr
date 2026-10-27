"""Build the reviewed locked cargo-generate CLI offline in owned directories."""
import asyncio
import argparse
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
    parser=argparse.ArgumentParser();parser.add_argument('--verify-built',action='store_true')
    parser.add_argument('--native-build',action='store_true');args=parser.parse_args()
    if args.verify_built and args.native_build:raise ValueError('legacy version-assertion readback is separate from fresh native build')
    project='cargo-generate';target=RAW/'active'/project;source=target/'src';package=DOC/project
    if (target/'build.json').exists() and not args.verify_built:raise ValueError('refuse replacing completed build')
    review=json.loads((package/'source-review.json').read_text())
    hook_path=target/'native-hook-review.json' if args.native_build else package/'dependency-hook-review.json'
    hooks=json.loads(hook_path.read_text())
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
    suffix='.exe' if os.name=='nt' else ''
    env=environment(target);env.update(RUSTC=str(compiler),RUSTDOC=str(compiler.with_name('rustdoc'+suffix)),
        CARGO_NET_OFFLINE='true',SOURCE_DATE_EPOCH='1793030400')
    env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    if args.native_build and os.name!='nt':
        located=shutil.which('cc',path=env['PATH'])
        if not located:raise ValueError('read-only native C compiler prerequisite missing')
        native_cc=Path(located).resolve(strict=True);env['CC']=str(native_cc)
        version=await execute([native_cc,'--version'],project,'native-read-only-c-compiler-version',
            cwd=source,env=env,timeout=30,campaign=NextCampaign())
        machine=await execute([native_cc,'-dumpmachine'],project,'native-read-only-c-compiler-target',
            cwd=source,env=env,timeout=30,campaign=NextCampaign())
        if machine['output'].strip() not in {'x86_64-linux-gnu','x86_64-pc-linux-gnu','x86_64-unknown-linux-gnu'}:raise ValueError('C compiler is not native for declared Linux host')
        immutable_json(target/'native-c-compiler.json',dict(path=str(native_cc),sha256=sha256(native_cc),
            version_attempt=version['id'],target_attempt=machine['id'],target=machine['output'].strip(),explicit_CC=True))
    cache=materialize_short_cache(target,dependencies,catalog) if os.name=='nt' else target/'cargo-home'
    env['CARGO_HOME']=str(cache)
    if args.verify_built:
        if (target/'version-check.json').exists():raise ValueError('preserve completed version check')
        build=json.loads((target/'build.json').read_text());binary=target/build['binary_relative_path']
        finished=json.loads((RAW/'events'/(build['build_attempt']+'-finished.json')).read_text())
        if (sha256(binary)!=build['binary_sha256'] or finished['category']!='passed' or finished['exit_code']!=0
            or finished['cleanup_errors'] or finished['harness_cleanup']!='harness_process_reaped'):
            raise ValueError('resume requires actual completed compile and exact executable')
        matches=[]
        for path in (RAW/'events').glob('*-finished.json'):
            row=json.loads(path.read_text())
            if row['project']==project and row['label']=='actual-built-native-version':matches.append(row)
        if len(matches)!=1:raise ValueError('resume requires one unambiguous original version execution')
        version=matches[0];vid=version['id']
        identified=json.loads((RAW/'events'/(vid+'-identified.json')).read_text())['identity']
        identity=RAW/identified['manifest']
        if sha256(identity)!=identified['sha256']:raise ValueError('version identity changed')
        reference=json.loads(identity.read_text())['target_catalog'];catalog_path=RAW/reference['manifest']
        if sha256(catalog_path)!=reference['sha256']:raise ValueError('version target catalog changed')
        bound=json.loads(catalog_path.read_text())['files']
        if (bound.get(binary.relative_to(ROOT).as_posix())!=build['binary_sha256'] or
            bound.get((target/'build.json').relative_to(ROOT).as_posix())!=sha256(target/'build.json')):
            raise ValueError('original version command did not bind this actual compiled executable')
        console=RAW/project/vid/'console.log'
        if (version['category']!='passed' or version['exit_code']!=0 or version['cleanup_errors'] or
            version['harness_cleanup']!='harness_process_reaped' or sha256(console)!=version['console_sha256']):
            raise ValueError('original version outcome not positive')
        output=console.read_text(encoding='utf-8-sig').strip()
        if output!='cargo generate-generate 0.25.1':raise ValueError('unexpected actual Clap subcommand version')
        immutable_json(target/'post-build-dependency-readback.json',dict(schema_version=1,
            actual_source_files_verified=len(catalog['files']),actual_registry_archives_verified=len(dependencies['files']),
            actual_short_materialization_sha256=sha256(cache/'materialized.json'),
            original_source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),
            build_sha256=sha256(target/'build.json'),scope='Both original and actual short dependency trees checked after build; no new compile or target execution.'))
        immutable_json(target/'version-check.json',dict(attempt=vid,binary_sha256=sha256(binary),output=output,
            build_sha256=sha256(target/'build.json'),
            disposition='Original successful compile/version retained. The outer helper failed only its incorrect hyphenated banner assertion; readback reuses the actual positive original execution without rerunning or overwriting it.'))
        print('Verified original successful build/version and both exact dependency trees; no compile or target rerun.')
        return
    # MSVC's textual relative include resolution can exceed MAX_PATH before
    # normalizing '..', even when the actual header exists. Change only native
    # spelling of these exact owned paths; do not move files or alter sources.
    if os.name=='nt':
        for key in ['CARGO_HOME','CARGO_TARGET_DIR','TEMP','TMP','TMPDIR']:
            env[key]=short_owned_path(env[key])
    triple='x86_64-pc-windows-msvc' if os.name=='nt' else 'x86_64-unknown-linux-gnu'
    command=[cargo,'rustc','--locked','--offline','--release','--target',triple,
        '--bin','cargo-generate']
    if os.name=='nt':command+=['--','-C','link-arg=/Brepro']
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
    built=target/'cargo-target'/triple/'release'/('cargo-generate'+suffix)
    binary=target/'bin'/('cargo-generate'+suffix);binary.parent.mkdir(exist_ok=True);shutil.copyfile(built,binary)
    if os.name!='nt':binary.chmod(0o755)
    digest=sha256(binary)
    immutable_json(target/'build.json',dict(schema_version=1,runtime_kind='native',
        pin=review['pin'],binary_relative_path=binary.relative_to(target).as_posix(),binary_sha256=digest,
        build_attempt=result['id'],compiler_path=str(compiler),compiler_sha256=sha256(compiler),
        cargo_path=str(cargo),cargo_sha256=sha256(cargo),native_triple=triple,features='default',
        source_review_sha256=sha256(package/'source-review.json'),
        dependency_hook_review_sha256=sha256(hook_path),
        dependency_source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),
        **(dict(actual_short_cache_reference_sha256=sha256(target/'short-cache-reference.json')) if os.name=='nt' else dict(actual_dependency_cache='cargo-home')),
        dependency_fetch_review_sha256=sha256(target/'dependency-fetch-review.json'),
        **(dict(native_c_compiler_sha256=sha256(target/'native-c-compiler.json')) if args.native_build and os.name!='nt' else {}),
        compiled_files={binary.name:digest},command=list(map(str,command)),
        owned_native_path_spellings={k:env[k] for k in ['CARGO_HOME','CARGO_TARGET_DIR','TEMP','TMP','TMPDIR']},
        installed_globally=False,windows_reproducible_link=os.name=='nt'))
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
    if version['output'].strip()!='cargo generate-generate 0.25.1':raise ValueError('actual built version differs')
    immutable_json(target/'version-check.json',dict(attempt=version['id'],binary_sha256=digest,
        output=version['output'],build_sha256=sha256(target/'build.json')))
    print('Built reviewed default-feature native CLI:',digest,'; version and source/dependency readback passed.')


if __name__=='__main__':asyncio.run(main())
