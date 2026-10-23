"""Fetch locked cz-cli dependencies with hooks disabled into owned roots."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import shutil
import time
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256
from readiness_build_plop import usage


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume-runtime',action='store_true');args=parser.parse_args()
    target=RAW/'active/cz-cli';source=target/'src';builder=target/'build-toolchain';app=target/('app-v2' if args.resume_runtime else 'app')
    marker=json.loads((target/'task-owned.json').read_text(encoding='utf-8'))
    review=json.loads((DOC/'cz-cli/setup-declaration.json').read_text(encoding='utf-8'))
    provenance=json.loads((DOC/'cz-cli/source-provenance.json').read_text(encoding='utf-8'))
    if marker['pin']!=review['pin'] or review['source_provenance_sha256']!=sha256(DOC/'cz-cli/source-provenance.json'):raise ValueError('Pinned source review differs')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=provenance['files']:raise ValueError('Canonical target source changed')
    if app.exists():raise ValueError('Existing setup attempt must be inspected; do not reinstall')
    base_node=Path(shutil.which('node') or '').resolve(strict=True)
    npm_command=Path(shutil.which('npm.cmd' if os.name=='nt' else 'npm') or '').resolve(strict=True)
    candidates=[base_node.parent/'node_modules/npm/bin/npm-cli.js',base_node.parent.parent/'lib/node_modules/npm/bin/npm-cli.js',npm_command]
    npm=next((p for p in candidates if p.is_file() and p.name=='npm-cli.js'),None)
    if npm is None:raise ValueError('Installed read-only npm CLI unavailable; no global installation attempted')
    node=target/'node'/('node.exe' if os.name=='nt' else 'node')
    if args.resume_runtime:
        prerequisite=json.loads((target/'node-prerequisite.json').read_text(encoding='utf-8'))
        if prerequisite['node_sha256']!=sha256(node) or prerequisite['npm_cli_sha256']!=sha256(npm):raise ValueError('Previous read-only prerequisite changed')
        if not (builder/'node_modules/.package-lock.json').is_file():raise ValueError('Completed builder install missing')
    else:
        node.parent.mkdir();shutil.copyfile(base_node,node)
        if os.name!='nt':node.chmod(0o755)
    if sha256(node)!=sha256(base_node):raise ValueError('Owned Node copy changed')
    env=environment(target)
    for key,folder in [('npm_config_cache','npm-cache'),('npm_config_prefix','npm-prefix')]:
        path=target/folder;path.mkdir(exist_ok=args.resume_runtime);env[key]=str(path)
    for key,name in [('npm_config_userconfig','empty-user.npmrc'),('npm_config_globalconfig','empty-global.npmrc')]:
        path=target/name
        if path.exists():
            if path.read_bytes()!=b'':raise ValueError('Owned npm configuration changed')
        else:path.write_bytes(b'')
        env[key]=str(path)
    env.update(npm_config_ignore_scripts='true',npm_config_bin_links='false',npm_config_audit='false',
        npm_config_fund='false',npm_config_update_notifier='false',npm_config_progress='false',
        PATH=str(node.parent)+os.pathsep+env['PATH'])
    observations=[];campaign=NextCampaign();started=time.monotonic();attempts=[]
    async def run(argv,label,cwd=ROOT):
        remaining=1200-(time.monotonic()-started)
        if remaining<=0:raise ValueError('Twenty-minute declared setup deadline')
        operation=asyncio.create_task(execute(argv,'cz-cli',label,cwd=cwd,env=env,timeout=remaining,campaign=campaign))
        try:
            while not operation.done():
                # npm atomically replaces/prunes directories while installing.
                # The existing periodic observer tolerates disappearing paths;
                # post-install exact inventories below remain strict.
                size=await asyncio.to_thread(usage,target)
                observations.append(dict(seconds=round(time.monotonic()-started,3),active_bytes=size))
                if size>512*1024**2:raise ValueError('Active target exceeded declared512MiB stop threshold before4GiB cap')
                await asyncio.sleep(2)
            value=await operation;attempts.append(value['id']);return value
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
    try:
        version=await run([node,'--version'],'owned-read-only-node-copy-version')
        if int(version['output'].strip().lstrip('v').split('.')[0])<18:raise ValueError('Target requires Node18 or later')
        npm_version=await run([node,npm,'--version'],'installed-read-only-npm-version')
        record=dict(schema_version=1,node=str(node),node_sha256=sha256(node),
            base_node=str(base_node),base_node_sha256=sha256(base_node),version=version['output'].strip(),
            npm_cli=str(npm),npm_cli_sha256=sha256(npm),npm_version=npm_version['output'].strip(),
            scope='Read-only installed tools; exact copied interpreter bytes, no global install. Native cells record their actual approved runtime versions independently.')
        if args.resume_runtime:
            if record!=prerequisite:raise ValueError('Previous prerequisite identities/version changed')
        else:immutable_json(target/'node-prerequisite.json',record)
        app.mkdir()
        for name in ['package.json','package-lock.json']:
            shutil.copyfile(source/name,app/name)
        shutil.copytree(source/'bin',app/'bin')
        if not args.resume_runtime:
            await run([node,npm,'ci','--ignore-scripts','--bin-links=false','--no-audit','--no-fund'],
                'locked-build-tool-dependencies-no-install-hooks',builder)
        await run([node,npm,'ci',*(['--offline'] if args.resume_runtime else []),'--omit=dev','--ignore-scripts','--bin-links=false','--no-audit','--no-fund'],
            'locked-runtime-dependencies-no-install-hooks',app)
        inventories={};lock_payloads={};locks=target/'npm-installed-locks';locks.mkdir()
        packages=[]
        for label,folder in [('build-toolchain',builder),('app',app)]:
            files={}
            for path in sorted(folder.rglob('*')):
                if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Unreviewed installed dependency link')
                if not path.is_file():continue
                if len(files)>=20000 or path.stat().st_size>16*1024**2:raise ValueError('Dependency file/count bound')
                files[path.relative_to(folder).as_posix()]=sha256(path)
                if path.name=='package.json' and 'node_modules' in path.parts:
                    metadata=json.loads(path.read_text(encoding='utf-8'))
                    if not metadata.get('name'):continue
                    packages.append(dict(scope=label,path=path.relative_to(target).as_posix(),name=metadata['name'],
                        version=metadata.get('version'),license=metadata.get('license'),scripts=metadata.get('scripts',{}),
                        package_sha256=sha256(path)))
            inventories[label]=files
            retained_lock=locks/(label+'.json');shutil.copyfile(folder/'node_modules/.package-lock.json',retained_lock)
            if sha256(retained_lock)!=files['node_modules/.package-lock.json']:raise ValueError('Installed lock payload copy changed')
            lock_payloads[label]=dict(path=retained_lock.relative_to(target).as_posix(),sha256=sha256(retained_lock))
        immutable_json(target/'dependency-fetch.json',dict(schema_version=1,attempts=attempts,app_relative_path=app.name,
            resumed_runtime_in_fresh_root=args.resume_runtime,
            source_lock_sha256=sha256(source/'package-lock.json'),build_lock_sha256=sha256(builder/'package-lock.json'),
            hooks_disabled=True,bin_links_disabled=True,installed_files=inventories,packages=packages,
            installed_lock_payloads=lock_payloads,
            target_or_backend_executed=False,scope='Installed dependencies only. Review metadata and exact inventories before explicit Babel build or application launch.'))
    finally:
        immutable_json(target/('setup-storage-'+uuid.uuid4().hex+'.json'),dict(schema_version=1,
            observations=observations,scope='Periodic observed bytes; not an exact peak or filesystem quota.',
            stop_threshold_bytes=512*1024**2))
    print('Locked runtime and minimal build dependencies installed with all hooks disabled. Explicit metadata review/build still required.')


if __name__=='__main__':asyncio.run(main())
