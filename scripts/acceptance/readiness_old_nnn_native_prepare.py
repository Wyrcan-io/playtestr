"""Build the original native nnn with read-only installed C prerequisites."""
import asyncio
import platform
from pathlib import Path
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_nnn_environment import environment
from readiness_old_nnn_build import compile_target


async def main():
    if platform.system() not in {'Linux','Darwin'}:raise RuntimeError('original nnn declares native Unix only')
    immutable_json(RAW/'old-nnn-runtime-baseline.json',await runtime_inventory('old-nnn','migration-owned-runtime-baseline'))
    await execute([sys.executable,ROOT/'scripts/acceptance/readiness_acquire_old.py','--project','nnn'],
        'old-nnn','migration-original-source-acquisition',timeout=180,campaign=Campaign())
    target=RAW/'active/old-nnn';source=target/'src';env=environment()
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/nnn';review=load(docs/'source-review.json')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=review['reviewed_inputs']:
        raise RuntimeError('original nnn source catalog differs before build')
    tools={}
    for name in ['cc','make','locale','otool' if platform.system()=='Darwin' else 'ldd']:
        found=shutil.which(name,path=env['PATH'])
        if found is None:raise RuntimeError('read-only native prerequisite missing: '+name)
        path=Path(found).resolve(strict=True);tools[name]=dict(path=str(path),sha256=sha256(path))
    versions={}
    for name in ['cc','make']:
        result=await execute([tools[name]['path'],'--version'],'old-nnn','migration-read-only-'+name+'-version',
            cwd=source,env=env,timeout=30,campaign=Campaign());versions[name]=dict(attempt=result['id'],output=result['output'])
    locale=await execute([tools['locale']['path'],'charmap'],'old-nnn','migration-native-utf8-locale',
        cwd=source,env=env,timeout=30,campaign=Campaign())
    charmap=locale['output'].strip()
    if charmap.replace('-','').replace('_','').upper()!='UTF8':raise RuntimeError('original Unicode profile requires operational native UTF-8 locale')
    immutable_json(target/'runtime.json',dict(compiler_path=tools['cc']['path'],compiler_sha256=tools['cc']['sha256'],
        make_path=tools['make']['path'],make_sha256=tools['make']['sha256'],tools=tools,versions=versions,
        native_locale_charmap=charmap,locale_attempt=locale['id'],native_host=platform.system(),
        installed_globally=False,packages_installed=False))
    result,binary=await compile_target('migration-reviewed-original-nnn-build')
    version=await execute([binary,'-V'],'old-nnn','migration-actual-original-nnn-version',cwd=source,env=env,
        timeout=30,campaign=Campaign())
    if version['output'].strip()!='5.3':raise RuntimeError('actual original nnn version differs')
    inspector='otool' if platform.system()=='Darwin' else 'ldd'
    libraries=await execute([tools[inspector]['path'],*(['-L'] if platform.system()=='Darwin' else []),binary],
        'old-nnn','migration-native-shared-library-identities',cwd=source,env=env,timeout=30,campaign=Campaign())
    if any(sha256(Path(t['path']))!=t['sha256'] for t in tools.values()):raise RuntimeError('read-only native prerequisite changed')
    actual={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
    if actual!={**review['reviewed_inputs'],'nnn':sha256(binary)}:raise RuntimeError('unexpected generated source file or original source change')
    immutable_json(target/'build.json',dict(pin=review['pin'],binary_relative_path='bin/nnn',binary_sha256=sha256(binary),
        build_attempt=result['id'],version_attempt=version['id'],libraries_attempt=libraries['id'],
        native_shared_libraries=libraries['output'],runtime_sha256=sha256(target/'runtime.json'),
        compiler_sha256=tools['cc']['sha256'],make_sha256=tools['make']['sha256'],
        source_review_sha256=sha256(docs/'source-review.json'),installed_globally=False,
        build_recipe='make -B all; default O_NORL=1, locale retained, default patch flags zero'))
    receipts=RAW/'old-nnn/build-receipts';receipts.mkdir(parents=True)
    for name in ['task-owned.json','acquisition.json','runtime.json','build.json']:shutil.copyfile(target/name,receipts/name)
    archive=target/'source.tar.gz'
    immutable_json(receipts/'canonical-source-reference.json',dict(archive_sha256=sha256(archive),
        archive_bytes=archive.stat().st_size,canonical_campaign_path='old-nnn/retained-source/source.tar.gz',
        scope='Exact original source archive retained once locally; native upload excludes duplicate archive bytes.'))
    print('Built original native nnn with ordinary Makefile/default flags and existing read-only tools; scenarios still required.')


if __name__=='__main__':asyncio.run(main())
