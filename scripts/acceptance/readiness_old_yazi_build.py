"""Build the original native Yazi from reviewed locked offline inputs."""
import asyncio
import argparse
import platform

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_helix_build import compile_target, run, build_environment
from readiness_old_yazi_review_hooks import verify


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume-compiled',action='store_true');args=parser.parse_args()
    triples={'Windows':'x86_64-pc-windows-msvc','Linux':'x86_64-unknown-linux-gnu','Darwin':'aarch64-apple-darwin'}
    triple=triples[platform.system()];target=RAW/'active/old-yazi';source=target/'src'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/yazi'
    review=load(docs/'source-review.json');hooks=load(docs/'dependency-hook-review.json')
    owner=load(target/'task-owned.json')
    if owner['workspace']!=str(ROOT) or owner['pin']!=review['pin'] or owner['project']!='sxyazi/yazi':
        raise RuntimeError('unowned original Yazi source')
    if (target/'build.json').exists():raise RuntimeError('refuse completed original Yazi build')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=review['reviewed_inputs']:
        raise RuntimeError('original Yazi source catalog changed')
    receipt=target/('dependencies.json' if (target/'dependencies.json').exists() else 'dependency-fetch-review.json')
    dependencies=load(receipt);verify(target,dependencies,hooks)
    if not (target/'runtime.json').exists():
        tools=load(target/'toolchain.json')
        if tools['rust_version']!='1.99.0' or tools['native_triple']!=triple or tools['installed_globally']:
            raise RuntimeError('original exact native Rust prerequisite differs')
        immutable_json(target/'runtime.json',dict(rustc_path=tools['rustc_path'],rustc_sha256=tools['rustc_sha256'],
            cargo_path=tools['cargo_path'],cargo_sha256=tools['cargo_sha256'],native_triple=triple,
            read_only_installed_prerequisites=False,installed_globally=False,
            toolchain_receipt_sha256=sha256(target/'toolchain.json')))
    _,runtime,_,env=build_environment('yazi')
    if runtime['native_triple']!=triple:raise RuntimeError('cross compilation cannot qualify native Yazi')
    compiler=await run('migration-actual-exact-rust-version',[runtime['rustc_path'],'-Vv'],env,30,project='yazi')
    if 'release: 1.99.0' not in compiler['output'] or 'host: '+triple not in compiler['output']:
        raise RuntimeError('actual native Rust version differs')
    if args.resume_compiled:
        # Resume only a completed successful compile followed by a successful
        # real version command whose prelaunch identity binds this exact binary.
        events=[]
        for path in (RAW/'events').glob('*-finished.json'):
            row=load(path)
            if row['project']=='old-yazi' and row['label']=='migration-reviewed-original-yazi-build':events.append(row)
        if len(events)!=1:raise RuntimeError('resume requires one unambiguous original compile')
        result=events[0]
        if (result['category']!='passed' or result['exit_code']!=0
                or result['harness_cleanup']!='harness_process_reaped' or result['cleanup_errors']):
            raise RuntimeError('resume refuses incomplete or failed compiler execution')
        from readiness_new_control_matrix import packet_file
        reference=load(RAW/'events'/(result['id']+'-identified.json'))['identity']
        compiled_manifest=packet_file(RAW,reference['manifest'].replace('\\','/'),2*1024**2)
        if sha256(compiled_manifest)!=reference['sha256']:raise RuntimeError('original compile manifest changed')
        compiled=load(compiled_manifest)
        if (any(compiled['files'][(source/name).relative_to(ROOT).as_posix()]!=digest
                for name,digest in review['reviewed_inputs'].items())
                or compiled['runtime_executables']!={'rustc':runtime['rustc_sha256'],'cargo':runtime['cargo_sha256']}):
            raise RuntimeError('original compile source/compiler differs')
        binary=target/'bin'/('yazi.exe' if platform.system()=='Windows' else 'yazi')
        versions=[]
        for path in (RAW/'events').glob('*-finished.json'):
            row=load(path)
            if row['project']=='old-yazi' and row['label']=='migration-actual-original-yazi-version':versions.append(row)
        if len(versions)!=1 or versions[0]['category']!='passed' or versions[0]['exit_code']!=0:
            raise RuntimeError('resume requires completed successful original version execution')
        identity=load(RAW/'events'/(versions[0]['id']+'-identified.json'))['identity']
        manifest=packet_file(RAW,identity['manifest'].replace('\\','/'),2*1024**2)
        if (sha256(manifest)!=identity['sha256']
                or load(manifest)['files'][binary.relative_to(ROOT).as_posix()]!=sha256(binary)):
            raise RuntimeError('resume binary differs from actual post-build version execution')
    else:result,binary=await compile_target('migration-reviewed-original-yazi-build',project='yazi')
    version=await run('migration-actual-original-yazi-version',[binary,'--version'],env,30,project='yazi')
    rust=dict(line.split(': ',1) for line in compiler['output'].splitlines() if ': ' in line)
    os_arch={'Windows':'windows-x86_64','Linux':'linux-x86_64','Darwin':'macos-aarch64'}[platform.system()]
    expected=['Yazi','Version: 26.9.1 (no-gitcl 2026-10-10)','Debug  : false',
        'Triple : '+triple+' ('+os_arch+')',
        'Rustc  : 1.99.0 ('+rust['commit-hash'][:8]+' '+rust['commit-date']+')']
    if [line.strip() for line in version['output'].strip().splitlines()]!=expected:
        raise RuntimeError('actual Yazi version does not match reviewed version/date profile')
    if any(sha256(source/name)!=digest for name,digest in review['reviewed_inputs'].items()):
        raise RuntimeError('Yazi build modified original source')
    verify(target,dependencies,hooks)
    immutable_json(target/'build.json',dict(pin=review['pin'],binary_relative_path=binary.relative_to(target).as_posix(),
        binary_sha256=sha256(binary),build_attempt=result['id'],version_attempt=version['id'],
        source_review_sha256=sha256(docs/'source-review.json'),hook_review_sha256=sha256(docs/'dependency-hook-review.json'),
        native_triple=triple,rustc_sha256=runtime['rustc_sha256'],cargo_sha256=runtime['cargo_sha256'],
        dependencies_receipt_sha256=sha256(receipt),installed_globally=False,
        windows_reproducible_link=platform.system()=='Windows',source_date_epoch=1791608923,
        profile='release-windows' if platform.system()=='Windows' else 'release',
        build_policy='Two jobs; no LTO/debug/incremental artifacts; default vendored Lua; no installer/completions.'))
    print('Built original native Yazi from reviewed offline dependencies; scenario validation still required.')


if __name__=='__main__':asyncio.run(main())
