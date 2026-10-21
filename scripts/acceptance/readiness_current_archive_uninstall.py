"""Rehearse removing an exact portable private archive install on a native host."""
import argparse
import asyncio
import ctypes
import os
from pathlib import Path
import platform
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_windows_archive_experience import extract


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',type=Path,required=True)
    args=parser.parse_args()
    host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    candidate=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json')
    cell=next(c for c in candidate['cells'] if c['host']==host)
    machine=platform.machine().lower()
    if {'x86_64':'amd64','amd64':'amd64','arm64':'arm64','aarch64':'arm64'}.get(machine)!=cell['architecture']:
        raise RuntimeError('portable uninstall requires the declared actual native architecture')
    archive=args.archive.resolve(strict=True)
    archive.relative_to(RAW.resolve(strict=True))
    root=RAW/'portable-uninstall'/uuid.uuid4().hex
    root.mkdir(parents=True)
    installed=root/'installed caf\u00e9 \u96ea'
    binary=extract(archive,cell,installed)
    before={p.name:sha256(p) for p in installed.iterdir()}
    immutable_json(root/'declared.json',dict(host=host,architecture=cell['architecture'],archive_sha256=sha256(archive),
        binary_sha256=cell['binary_sha256'],installed_relative=installed.relative_to(ROOT).as_posix(),files=before,
        scope='Run the exact portable archive executable in a fresh Unicode/spaces path, then remove only its four verified files and empty directory. No global installation, registry or user configuration changes.'))
    empty=root/'empty-path';empty.mkdir()
    home=root/'home';home.mkdir()
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT'}}
    env.update(PATH=str(empty),HOME=str(home),USERPROFILE=str(home),APPDATA=str(home),LOCALAPPDATA=str(home),
        TEMP=str(RAW/'tmp'),TMP=str(RAW/'tmp'),TMPDIR=str(RAW/'tmp'))
    outcome=await execute([binary,'--version'],'core','current-portable-archive-uninstall-version',env=env,
        timeout=30,campaign=Campaign(phase='final-archive'))
    if outcome['output'].strip()!='playtestr '+candidate['version']:
        raise RuntimeError('fresh portable executable version differs')
    installed.resolve(strict=True).relative_to(root.resolve(strict=True))
    if installed.parent!=root or installed.is_symlink() or getattr(installed,'is_junction',lambda:False)():
        raise RuntimeError('portable removal escapes owned folder')
    actual={p.name:sha256(p) for p in installed.iterdir() if p.is_file() and not p.is_symlink()}
    if actual!=before or len(list(installed.iterdir()))!=4:
        raise RuntimeError('portable installation changed before removal')
    # Four individually verified regular files; no recursive or computed shell deletion.
    for name in sorted(before):
        path=installed/name
        if path.is_symlink() or not path.is_file() or sha256(path)!=before[name]:
            raise RuntimeError('portable file changed during removal')
        path.unlink()
    installed.rmdir()
    if installed.exists() or os.path.lexists(installed):
        raise RuntimeError('portable installation still exists')
    immutable_json(root/'verified.json',dict(host=host,architecture=cell['architecture'],native_machine=machine,archive_sha256=sha256(archive),
        binary_sha256=cell['binary_sha256'],declaration_sha256=sha256(root/'declared.json'),version_attempt=outcome['id'],
        installed_files_verified=before,installed_directory_removed=True,
        privileged_role_enabled=(bool(ctypes.windll.shell32.IsUserAnAdmin()) if os.name=='nt' else os.geteuid()==0),
        scope='Actual native portable archive launch and removal of only its four checked files and empty owned directory. The canonical private archive and immutable evidence remain retained.',final_archive_credit=0))
    print('Verified exact current portable archive install/launch/uninstall:',host,root.name)


if __name__=='__main__':asyncio.run(main())
