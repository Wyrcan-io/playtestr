"""Verify bounded Plop source/evidence restore before owned Unix removal."""
import asyncio
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile

from adversarial_process import execute, unix_process_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def node_inventory(label):
    result=await execute(['ps','-axo','pid=,comm='],'plop',label,timeout=15,
                         output_cap=65536,campaign=Campaign())
    birth=await unix_process_inventory()
    selected={}
    for line in result['output'].splitlines():
        fields=line.split(None,1)
        if len(fields)==2 and Path(fields[1]).name in {'node','nodejs'}:
            pid=int(fields[0])
            if pid not in birth:continue
            selected[str(pid)]=list(birth[pid])
    return selected


async def main():
    if os.name=='nt':raise RuntimeError('use the checked native PowerShell removal route on Windows')
    active=RAW/'active/plop'
    base=(RAW/'active').resolve()
    if active.is_symlink() or active.resolve().parent!=base or not base.is_relative_to(RAW.resolve()):
        raise RuntimeError('unsafe cleanup target')
    marker=json.loads((active/'task-owned.json').read_text())
    if marker['workspace']!=str(ROOT) or marker['campaign']!='runner-readiness-ten-project-pass' or marker['project']!='plopjs/plop':
        raise RuntimeError('cleanup ownership mismatch')
    baseline=json.loads((RAW/'plop-node-baseline.json').read_text())
    current=await node_inventory('verify-node-termination-before-removal')
    if any(baseline.get(pid)!=identity for pid,identity in current.items()):
        raise RuntimeError('new Node process remains; cleanup unconfirmed, do not remove live state')
    for report in (RAW/'plop').rglob('*.json'):
        data=json.loads(report.read_text(encoding='utf-8'))
        if isinstance(data,dict) and data.get('report_version')==3:
            for result in data['results']:
                if result['cleanup']['attempted'] and not result['cleanup']['confirmed_exited']:
                    raise RuntimeError('a retained test has unconfirmed process cleanup')
                workspace=result.get('workspace') or {}
                if workspace.get('prepared') and not workspace.get('cleaned'):
                    raise RuntimeError('a managed workspace remains retained')
    retained=RAW/'plop/retained-source';retained.mkdir(exist_ok=False)
    archive=active/'source.tar.gz'
    acquisition=json.loads((active/'acquisition.json').read_text())
    if sha256(archive)!=acquisition['archive_sha256']:raise RuntimeError('source archive identity changed')
    copy=retained/'source.tar.gz';shutil.copyfile(archive,copy)
    if sha256(copy)!=sha256(archive):raise RuntimeError('retained archive differs')
    manifest={};expanded=0;restore=retained/'selected-restore';restore.mkdir()
    selected={'LICENSE.md','packages/plop/src/plop.js','packages/node-plop/src/generator-runner.js',
              'packages/node-plop/src/actions/_common-action-add-file.js','yarn.lock'}
    with tarfile.open(copy,'r:gz') as bundle:
        for member in bundle:
            parts=PurePosixPath(member.name).parts[1:]
            if not parts:continue
            if any(p in {'..','.'} or ':' in p or '\\' in p for p in parts):raise RuntimeError('unsafe retained member')
            if member.isdir():continue
            if not member.isfile() or member.size>8*1024**2:raise RuntimeError('unsafe retained member type/size')
            expanded+=member.size
            if expanded>64*1024**2 or len(manifest)>=10000:raise RuntimeError('restore bounds exceeded')
            value=bundle.extractfile(member).read(member.size+1)
            if len(value)!=member.size:raise RuntimeError('retained member size mismatch')
            relative='/'.join(parts);digest=hashlib.sha256(value).hexdigest()
            if sha256(active/'src'/relative)!=digest:raise RuntimeError('pinned source not restored: '+relative)
            manifest[relative]=dict(sha256=digest,bytes=len(value),mode=member.mode)
            if relative in selected:
                restored=restore/relative;restored.parent.mkdir(parents=True,exist_ok=True);restored.write_bytes(value)
                if sha256(restored)!=digest:raise RuntimeError('selected restore verification failed')
    if not selected<=manifest.keys():raise RuntimeError('restore coverage missing')
    for name in ['task-owned.json','acquisition.json','runtime.json','build.json']:
        shutil.copyfile(active/name,retained/name)
    immutable_json(retained/'verified-index.json',dict(archive_sha256=sha256(copy),files=manifest,
        selected_restore=sorted(selected),expanded_source_bytes=expanded,process_inventory=current))
    # Do not follow package-manager links during either verification or removal.
    entries=0
    for directory,dirs,files in os.walk(active,followlinks=False):
        for name in dirs+files:
            entries+=1
            if entries>100000:raise RuntimeError('owned tree inventory bound')
            path=Path(directory)/name
            if path.is_symlink() and not path.resolve().is_relative_to(active.resolve()):
                raise RuntimeError('unknown escaping package-manager link')
    immutable_json(retained/'removal-prepared.json',dict(owned_relative_path='active/plop',
        source_archive_verified=True,source_members=len(manifest),managed_cleanup_verified=True,
        node_processes_verified=True,entries=entries))
    shutil.rmtree(active)
    if active.exists():raise RuntimeError('owned target removal failed')
    immutable_json(retained/'removed.json',dict(removed=True,owned_relative_path='active/plop',
                                               source_archive_sha256=sha256(copy)))
    print('Owned Plop tree removed after verified archive/restore and termination checks.')


if __name__=='__main__':asyncio.run(main())
