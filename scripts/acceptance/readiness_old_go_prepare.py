"""Build a reviewed original Go target with entirely owned prerequisites."""
import argparse
import asyncio
import os
import platform
import re
import sys
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_build_rclone import environment
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['lf'],required=True)
    parser.add_argument('--resume-after');args=parser.parse_args()
    project=args.project;slug='old-'+project;target=RAW/'active'/slug;source=target/'src'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration'/project
    review=load(docs/'source-review.json');owner=load(target/'task-owned.json')
    if owner['workspace']!=str(ROOT) or owner['pin']!=review['pin'] or owner['project']!=review['repository']:
        raise RuntimeError('unowned original Go application')
    for name,digest in review['reviewed_inputs'].items():
        if sha256(source/name)!=digest:raise RuntimeError('original reviewed source changed')
    if (target/'build.json').exists():raise RuntimeError('refuse existing completed build')
    env=environment(target)
    if os.name=='nt':env['USERNAME']='synthetic-maintainer'
    if args.resume_after:
        if not re.fullmatch('[0-9a-f]{32}',args.resume_after):raise RuntimeError('invalid setup failure identity')
        failure=load(RAW/'events'/(args.resume_after+'-finished.json'))
        if failure['project']!=slug or failure['label']!='migration-original-built-cli-version' or failure['exit_code']!=2:
            raise RuntimeError('resume requires the retained failed original version probe')
    async def run(label,argv,timeout=120):
        return await execute(argv,slug,label,cwd=source,env=env,timeout=timeout,campaign=Campaign())
    sdk=target/'toolchain/sdk.json'
    if not sdk.exists():
        await run('migration-original-owned-go-sdk',[sys.executable,ROOT/'scripts/acceptance/readiness_bootstrap_old_go.py','--project',project],360)
    descriptor=load(sdk)
    if descriptor['version']!='go1.27.0':raise RuntimeError('unexpected original target SDK')
    go=target/'toolchain/go/bin'/('go.exe' if os.name=='nt' else 'go')
    settings=await run('migration-original-native-go-settings',[go,'env','-json','GOOS','GOARCH','GOVERSION','CGO_ENABLED'],30)
    import json
    native=json.loads(settings['output'])
    host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    arch={'amd64':'amd64','x86_64':'amd64','arm64':'arm64','aarch64':'arm64'}[platform.machine().lower()]
    if native!=dict(GOOS=host,GOARCH=arch,GOVERSION='go1.27.0',CGO_ENABLED='0'):
        raise RuntimeError('target build would not use reviewed native pure-Go settings')
    binary=target/'bin'/(project+('.exe' if os.name=='nt' else ''));binary.parent.mkdir(exist_ok=bool(args.resume_after))
    flags=review['build_flags'];sizes=[]
    operation=asyncio.create_task(run('migration-original-reviewed-cli-build',[go,'build',*flags,'-o',binary,'.'],600))
    try:
        while not operation.done():
            size=await asyncio.to_thread(usage,target);sizes.append(size)
            if size>review['active_stop_mib']*1024**2:raise RuntimeError('owned original Go build storage stop')
            await asyncio.sleep(2)
        built=await operation
    finally:
        if not operation.done():
            operation.cancel()
            try:await operation
            except asyncio.CancelledError:pass
        immutable_json(target/('build-storage-'+uuid.uuid4().hex+'.json'),dict(observed_bytes=sizes,scope='Periodic logical bytes, not exact peak or quota.'))
    for name,digest in review['reviewed_inputs'].items():
        if sha256(source/name)!=digest:raise RuntimeError('build changed reviewed source')
    version=await run('migration-original-built-cli-version',[binary,'-version'],30)
    immutable_json(target/'runtime.json',dict(go=str(go),compiler_sha256=sha256(go),sdk_sha256=sha256(sdk),
        native_settings=native,version_attempt=version['id'],installed_globally=False))
    immutable_json(target/'build.json',dict(pin=review['pin'],binary_relative_path=binary.relative_to(target).as_posix(),
        binary_sha256=sha256(binary),source_review_sha256=sha256(docs/'source-review.json'),compiler_sha256=sha256(go),
        sdk_sha256=sha256(sdk),native_settings=native,build_attempt=built['id'],settings_attempt=settings['id'],
        version_attempt=version['id'],build_flags=flags,cgo_enabled=False,target_hooks_executed=False,
        resumed_after_failed_probe=args.resume_after))
    print('Built original native',project,'with owned pinned SDK and exact source/module locks.')


if __name__=='__main__':asyncio.run(main())
