"""Prepare the original dependency-free Ranger on its native Unix hosts."""
import asyncio
import json
import platform
from pathlib import Path
import shlex
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_ranger_environment import environment


async def main():
    if platform.system() not in {'Linux','Darwin'}:raise RuntimeError('native Unix Python/curses is required')
    immutable_json(RAW/'old-ranger-runtime-baseline.json',await runtime_inventory('old-ranger','migration-owned-runtime-baseline'))
    await execute([sys.executable,ROOT/'scripts/acceptance/readiness_acquire_old.py','--project','ranger'],
        'old-ranger','migration-original-source-acquisition',timeout=180,campaign=Campaign())
    target=RAW/'active/old-ranger';source=target/'src';env=environment()
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/ranger';review=load(docs/'source-review.json')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=review['reviewed_inputs']:
        raise RuntimeError('native Ranger source differs from reviewed pin')
    base_python=Path(sys.executable).resolve(strict=True);base_digest=sha256(base_python)
    await execute([base_python,'-B','-m','venv','--without-pip','--copies',target/'venv'],
        'old-ranger','migration-owned-private-python-copies',cwd=source,env=env,timeout=120,campaign=Campaign())
    python=target/'venv/bin/python'
    if python.is_symlink() or sha256(base_python)!=base_digest:raise RuntimeError('read-only base Python changed or private interpreter is linked')
    code='import curses,_curses,json,sys,ranger; print(json.dumps(dict(version=sys.version,curses=curses.__file__,extension=_curses.__file__,target_version=ranger.__version__)))'
    probe=await execute([python,'-B','-c',code],'old-ranger','migration-native-python-curses-probe',
        cwd=source,env=env,timeout=30,campaign=Campaign());native=json.loads(probe['output'])
    if native['target_version']!='1.9.4':raise RuntimeError('original Ranger package version differs')
    launcher=target/'bin/ranger';launcher.parent.mkdir(exist_ok=True)
    launcher.write_text('#!/bin/sh\nexport GIT_CEILING_DIRECTORIES='+shlex.quote(str(target))+
        '\nexport GIT_CONFIG_NOSYSTEM=1\nexport GIT_CONFIG_GLOBAL=/dev/null\nexec '+shlex.quote(str(python))+
        ' -B -O '+shlex.quote(str(source/'ranger.py'))+' "$@"\n',encoding='utf-8',newline='\n');launcher.chmod(0o755)
    immutable_json(target/'runtime.json',dict(python_path=str(python),python_sha256=sha256(python),
        base_python_path=str(base_python),base_python_sha256=base_digest,
        curses_path=native['curses'],curses_sha256=sha256(native['curses']),
        curses_extension_path=native['extension'],curses_extension_sha256=sha256(native['extension']),
        python_version=native['version'],probe_attempt=probe['id'],native_host=platform.system(),
        third_party_packages_installed=False,installed_globally=False,venv_copies=True))
    version=await execute([launcher,'--clean','--version'],'old-ranger','migration-actual-original-ranger-version',
        cwd=source,env=env,timeout=30,campaign=Campaign())
    if 'ranger version: ranger-master' not in version['output']:raise RuntimeError('unexpected archive-source Ranger version profile')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=review['reviewed_inputs']:
        raise RuntimeError('source launch wrote or changed original files')
    immutable_json(target/'build.json',dict(pin=review['pin'],binary_relative_path='bin/ranger',
        binary_sha256=sha256(launcher),python_sha256=sha256(python),runtime_sha256=sha256(target/'runtime.json'),
        source_review_sha256=sha256(docs/'source-review.json'),version_attempt=version['id'],
        execution='Transparent exec of original ranger.py; -B -O and original --clean scenario flag; no installer or third-party package.',
        compiled_target=False,installed_globally=False))
    receipts=RAW/'old-ranger/build-receipts';receipts.mkdir(parents=True)
    for name in ['task-owned.json','acquisition.json','runtime.json','build.json']:shutil.copyfile(target/name,receipts/name)
    archive=target/'source.tar.gz'
    immutable_json(receipts/'canonical-source-reference.json',dict(archive_sha256=sha256(archive),
        archive_bytes=archive.stat().st_size,canonical_campaign_path='old-ranger/retained-source/source.tar.gz',
        scope='Exact original archive retained once locally; native uploads exclude duplicate source archive bytes.'))
    print('Original native Ranger source launcher and private Python/curses prepared; scenarios still required.')


if __name__=='__main__':asyncio.run(main())
