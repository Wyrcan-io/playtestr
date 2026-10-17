"""Verify bounded Plop source/evidence restore before owned Unix removal."""
import asyncio
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import uuid

from adversarial_process import close_transport, execute, unix_process_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def owned_runtime_command(pid,identity):
    """Inspect bounded arguments privately; persist only the ownership decision."""
    inspector=await asyncio.create_subprocess_exec('ps','-ww','-p',str(pid),'-o','command=',
        stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,
        env=dict(os.environ,LC_ALL='C'))
    try:
        async def read_command():
            data=bytearray()
            while block:=await inspector.stdout.read(4096):
                if len(data)+len(block)>65536:raise RuntimeError('runtime ownership observation byte bound')
                data.extend(block)
            return data
        data=await asyncio.wait_for(read_command(),timeout=2)
        status=await asyncio.wait_for(inspector.wait(),timeout=1)
        current=await unix_process_inventory()
        # A parent may exit while its child remains live. Compare birth, not PPID.
        if pid not in current or current[pid][1]!=identity[1]:return False
        if status!=0 or not data.strip():raise RuntimeError('runtime command ownership unconfirmed for PID '+str(pid))
        return (str(RAW.resolve())+'/').encode('utf-8') in data
    finally:
        if inspector.returncode is None:
            inspector.kill()
            await asyncio.wait_for(inspector.wait(),timeout=2)
        await close_transport(inspector)


async def runtime_inventory(project,label):
    result=await execute(['ps','-axo','pid=,comm='],project,label,timeout=15,
                         output_cap=65536,campaign=Campaign())
    birth=await unix_process_inventory()
    selected={};scope=[]
    ancestors=set();ancestor=os.getpid()
    if project in {'fff','papis'}:
        while ancestor in birth and ancestor not in ancestors:
            if len(ancestors)>=64:raise RuntimeError('process ancestor inventory bound')
            ancestors.add(ancestor);ancestor=birth[ancestor][0]
    for line in result['output'].splitlines():
        fields=line.split(None,1)
        name=Path(fields[1]).name if len(fields)==2 else ''
        runtime_match=(name in {'node','nodejs'} if project=='plop' else
                       name.startswith('ruby') or name in {'git','less','diff'} if project=='rubygems' else
                       name in {'edit','cargo','rustc','rustdoc','cc','ld','lld','collect2'} if project=='edit' else
                       name in {'vis','make','cc','as','ld','collect2'} or name.startswith(('gcc','clang','cc1','x86_64-linux-gn','aarch64-linux-gn')) if project=='vis' else
                       name in {'bash','sh','fff','cp','mv','rm','mkdir','stty','file','chmod','ln'} if project=='fff' else name.startswith('python'))
        if len(fields)==2 and runtime_match:
            pid=int(fields[0])
            if project in {'fff','papis'} and pid in ancestors:continue
            if project=='poetry' and pid in {os.getpid(),os.getppid()}:continue
            if pid not in birth:continue
            if project in {'fff','papis'}:
                owned=await owned_runtime_command(pid,birth[pid])
                scope.append(dict(pid=pid,birth=birth[pid][1],owned_campaign_command=owned))
                if not owned:continue
            selected[str(pid)]=list(birth[pid])
    if project in {'fff','papis'}:
        immutable_json(RAW/project/'runtime-inventories'/(uuid.uuid4().hex+'.json'),
            dict(schema_version=1,label=label,checked_at_utc=datetime.now(timezone.utc).isoformat(),
                 owned_root=str(RAW.resolve()),observations=scope,command_values_persisted=False,
                 boundary='Additional owned-root observer; every public target process-group cleanup must still pass.'))
    return selected


async def node_inventory(label):
    return await runtime_inventory('plop',label)


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--source-only',action='store_true',help='Retain an acquired, never-built local Windows Vis/fff source tree without inventing runtime/build receipts')
    parser.add_argument('--project',choices=['plop','poetry','rubygems','edit','vis','fff','papis'],default='plop')
    args=parser.parse_args()
    if os.name=='nt' and not args.prepare_only:
        raise RuntimeError('use --prepare-only then the checked native PowerShell removal route on Windows')
    project=args.project
    if args.source_only and (os.name!='nt' or project not in {'vis','fff'} or not args.prepare_only):
        raise RuntimeError('source-only retention applies only to never-built local Windows Vis/fff preparation')
    active=RAW/'active'/project
    if args.source_only and any((active/name).exists() for name in ['runtime.json','build.json','src/vis','src/vis.exe']):
        raise RuntimeError('source-only retention refuses build/runtime or executable evidence')
    base=(RAW/'active').resolve()
    if active.is_symlink() or active.resolve().parent!=base or not base.is_relative_to(RAW.resolve()):
        raise RuntimeError('unsafe cleanup target')
    marker=json.loads((active/'task-owned.json').read_text())
    repository={'plop':'plopjs/plop','poetry':'python-poetry/poetry','rubygems':'ruby/rubygems','edit':'microsoft/edit','vis':'martanne/vis','fff':'dylanaraps/fff','papis':'papis/papis'}[project]
    if marker['workspace']!=str(ROOT) or marker['campaign']!='runner-readiness-ten-project-pass' or marker['project']!=repository:
        raise RuntimeError('cleanup ownership mismatch')
    if os.name=='nt':
        proof=json.loads((RAW/project/'local-process-cleanup.json').read_text(encoding='utf-8-sig'))
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(proof['checked_at_utc'].replace('Z','+00:00'))).total_seconds()
        if (proof.get('query_succeeded') is not True or not 0<=age<60 or
            proof.get('active_path')!=str(active.resolve()) or
            proof.get('matching_node_pids' if project=='plop' else 'matching_runtime_pids')!=[]):
            raise RuntimeError('owned Windows runtime process cleanup is unconfirmed')
        current={'windows_owned_command_path_check':proof}
    else:
        baseline_path=RAW/('plop-node-baseline.json' if project=='plop' else project+'-runtime-baseline.json')
        baseline=json.loads(baseline_path.read_text())
        current=await runtime_inventory(project,'verify-runtime-termination-before-removal')
        if any(baseline.get(pid)!=identity for pid,identity in current.items()):
            raise RuntimeError('new runtime process remains; cleanup unconfirmed, do not remove live state')
    for report in (RAW/project).rglob('*.json'):
        data=json.loads(report.read_text(encoding='utf-8-sig'))
        if isinstance(data,dict) and data.get('report_version')==3:
            for result in data['results']:
                if result['cleanup']['attempted'] and not result['cleanup']['confirmed_exited']:
                    raise RuntimeError('a retained test has unconfirmed process cleanup')
                workspace=result.get('workspace') or {}
                if workspace.get('prepared') and not workspace.get('cleaned'):
                    raise RuntimeError('a managed workspace remains retained')
    retained=RAW/project/'retained-source';retained.mkdir(exist_ok=False)
    archive=active/'source.tar.gz'
    acquisition=json.loads((active/'acquisition.json').read_text())
    if sha256(archive)!=acquisition['archive_sha256']:raise RuntimeError('source archive identity changed')
    copy=retained/'source.tar.gz';shutil.copyfile(archive,copy)
    if sha256(copy)!=sha256(archive):raise RuntimeError('retained archive differs')
    manifest={};expanded=0;restore=retained/'selected-restore';restore.mkdir()
    selected={'LICENSE.md','packages/plop/src/plop.js','packages/node-plop/src/generator-runner.js',
              'packages/node-plop/src/actions/_common-action-add-file.js','yarn.lock'}
    if project=='poetry':
        selected={'LICENSE','pyproject.toml','poetry.lock','src/poetry/console/commands/init.py',
                  'src/poetry/console/commands/source/remove.py','src/poetry/console/commands/version.py'}
    elif project=='rubygems':
        selected={'MIT.txt','LICENSE.txt','bundler.gemspec','exe/bundle','exe/gem',
                  'lib/bundler/cli/gem.rb','lib/rubygems/commands/build_command.rb',
                  'lib/bundler/templates/newgem/lib/newgem/version.rb.tt'}
    elif project=='edit':
        selected={'LICENSE','Cargo.lock','Cargo.toml','i18n/edit.toml','crates/edit/build/main.rs',
                  'crates/edit/src/bin/edit/main.rs','crates/edit/src/bin/edit/documents.rs'}
    elif project=='vis':
        selected={'LICENSE','Makefile','configure','main.c','text.c','vis-modes.c','external/termkey.c','lua/lexer.lua'}
    elif project=='fff':
        selected={'LICENSE.md','Makefile','README.md','fff','fff.1'}
    elif project=='papis':
        selected={'LICENSE','pyproject.toml','papis/commands/export.py','papis/commands/tag.py',
                  'papis/commands/update.py','papis/tui/picker/__init__.py','papis/tui/picker/options_list.py'}
    stream_args=dict(name=copy,mode='r:gz')
    if project=='vis':
        from readiness_vis_source import ARCHIVE_SHA256,LINKS,materialize_archive
        if sha256(copy)!=ARCHIVE_SHA256 or acquisition['materialized_links']!=LINKS:raise RuntimeError('vis retained source profile changed')
        stream_args=dict(fileobj=io.BytesIO(materialize_archive(copy.read_bytes(),LINKS)),mode='r:gz')
    with tarfile.open(**stream_args) as bundle:
        for member in bundle:
            parts=PurePosixPath(member.name).parts[1:]
            if not parts:continue
            if any(p in {'..','.'} or ':' in p or '\\' in p for p in parts):raise RuntimeError('unsafe retained member')
            if member.isdir():continue
            if not member.isfile() or member.size>({'rubygems':32,'vis':16}.get(project,8))*1024**2:raise RuntimeError('unsafe retained member type/size')
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
    records=['task-owned.json','acquisition.json'] if args.source_only else ['task-owned.json','acquisition.json','runtime.json','build.json']
    for name in records:
        shutil.copyfile(active/name,retained/name)
    if args.source_only:
        immutable_json(retained/'source-only.json',dict(project=repository,native_local_build_attempted=False,
            native_local_runtime_attempted=False,local_host='Windows',qualification='not attempted; declared runtime hosts Linux/macOS only'))
    if project in {'edit','vis'}:
        for name in (['dependencies.json','build-review.json'] if project=='edit' else []):shutil.copyfile(active/name,retained/name)
        if (active/'build-revisions').is_dir():shutil.copytree(active/'build-revisions',retained/'build-revisions')
    if project=='papis':
        for name in ['wheels.json']:
            if (active/name).is_file():shutil.copyfile(active/name,retained/name)
        for name in ['wheel-manifests','dependency-review']:
            if (active/name).is_dir():shutil.copytree(active/name,retained/name)
    immutable_json(retained/'verified-index.json',dict(archive_sha256=sha256(copy),files=manifest,
        selected_restore=sorted(selected),expanded_source_bytes=expanded,process_inventory=current))
    # Do not follow package-manager links during either verification or removal.
    entries=0;links=[];external_runtime_links=[]
    for directory,dirs,files in os.walk(active,followlinks=False):
        for name in dirs+files:
            entries+=1
            if entries>100000:raise RuntimeError('owned tree inventory bound')
            path=Path(directory)/name
            if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):
                if not path.resolve().is_relative_to(active.resolve()):
                    relative=path.relative_to(active)
                    runtime=json.loads((active/'runtime.json').read_text())
                    if (project not in {'poetry','papis'} or relative.parts[:2]!=('venv','bin') or
                        not re.fullmatch(r'python(?:[0-9]+(?:\.[0-9]+)?)?',path.name) or
                        not path.resolve().is_file() or sha256(path.resolve())!=runtime.get('python_sha256')):
                        raise RuntimeError('unknown escaping package-manager link: '+relative.as_posix())
                    external_runtime_links.append(dict(path=relative.as_posix(),runtime_sha256=runtime['python_sha256']))
                links.append(path.relative_to(active).as_posix())
                if name in dirs:dirs.remove(name)
    immutable_json(retained/'removal-prepared.json',dict(owned_relative_path='active/'+project,
        source_archive_verified=True,source_members=len(manifest),managed_cleanup_verified=True,
        node_processes_verified=project=='plop',runtime_processes_verified=True,
        entries=entries,owned_links=sorted(links),
        existing_runtime_symlinks=external_runtime_links))
    if args.prepare_only:
        print('Archive/restore and cleanup checked; target retained for checked native removal.')
        return
    shutil.rmtree(active)
    if active.exists():raise RuntimeError('owned target removal failed')
    immutable_json(retained/'removed.json',dict(removed=True,owned_relative_path='active/'+project,
                                               source_archive_sha256=sha256(copy)))
    print('Owned',project,'tree removed after verified archive/restore and termination checks.')


if __name__=='__main__':asyncio.run(main())
