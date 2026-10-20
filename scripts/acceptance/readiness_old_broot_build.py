"""Build original Broot only on its declared native Unix hosts."""
import asyncio
from pathlib import Path
import platform
import shutil

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_helix_build import build_environment, compile_target, run


async def main():
    if platform.system() not in {'Linux','Darwin'}:raise RuntimeError('Broot target runtime is declared Linux/macOS only')
    target=RAW/'active/old-broot';source=target/'src'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/broot'
    review=load(docs/'source-review.json');hooks=load(docs/'dependency-hook-review.json')
    owner=load(target/'task-owned.json')
    if owner['workspace']!=str(ROOT) or owner['pin']!=review['pin'] or owner['project']!='Canop/broot':
        raise RuntimeError('unowned original Broot target')
    if (target/'build.json').exists():raise RuntimeError('refuse completed Broot build')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=review['reviewed_inputs']:
        raise RuntimeError('original source changed before compilation')
    dependencies=load(target/'dependencies.json')
    if dependencies['lock_sha256']!=hooks['source_lock_sha256'] or sha256(source/'Cargo.lock')!=dependencies['lock_sha256']:
        raise RuntimeError('original dependency lock changed')
    for name,digest in dependencies['build_hooks'].items():
        paths=list((target/'cargo-home/registry/src').glob('*/'+name))
        if hooks['reviewed_hook_sha256'].get(name)!=digest or len(paths)!=1 or sha256(paths[0])!=digest:
            raise RuntimeError('unreviewed or changed dependency hook')
    for name,row in dependencies['files'].items():
        if sha256(target/name)!=row['sha256'] or hooks['registry_archives_sha256'].get(Path(name).name)!=row['sha256']:
            raise RuntimeError('reviewed dependency archive changed')
    target,runtime,cargo,env=build_environment('broot')
    triple={'Linux':'x86_64-unknown-linux-gnu','Darwin':'aarch64-apple-darwin'}[platform.system()]
    if runtime['native_triple']!=triple:raise RuntimeError('wrong native target')
    git=shutil.which('git')
    if git is None:raise RuntimeError('read-only Git prerequisite missing')
    await run('migration-source-git-ceiling',[git,'rev-parse','--show-toplevel'],env,30,128,project='broot')
    result,binary=await compile_target('migration-reviewed-original-broot-build',project='broot')
    version=await run('migration-actual-original-broot-version',[binary,'--version'],env,30,project='broot')
    if version['output'].strip()!='broot 1.61.0':raise RuntimeError('original Broot version differs')
    if any(sha256(source/name)!=digest for name,digest in review['reviewed_inputs'].items()):
        raise RuntimeError('build changed original source')
    immutable_json(target/'build.json',dict(pin=review['pin'],binary_relative_path=binary.relative_to(target).as_posix(),
        binary_sha256=sha256(binary),build_attempt=result['id'],version_attempt=version['id'],
        source_review_sha256=sha256(docs/'source-review.json'),hook_review_sha256=sha256(docs/'dependency-hook-review.json'),
        native_triple=triple,rustc_sha256=runtime['rustc_sha256'],cargo_sha256=runtime['cargo_sha256'],
        installed_globally=False,profile='release; two jobs; no LTO/debug/incremental artifacts'))
    print('Built original native Broot using reviewed locked offline dependencies.')


if __name__=='__main__':asyncio.run(main())
