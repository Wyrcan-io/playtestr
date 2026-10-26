"""Fetch the already reviewed yo locks on a native hosted cell, without hooks."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import time

from adversarial_process import execute
from next20_check import RAW, ROOT, DOC, NextCampaign
from next20_python_setup import environment
from readiness_build_plop import usage
from readiness_evidence import immutable_json, sha256


async def main():
    target=RAW/'active/yo';source=target/'src';package=DOC/'yo'
    provenance=json.loads((package/'source-provenance.json').read_text())
    approved=json.loads((package/'setup-declaration.json').read_text())
    if json.loads((target/'task-owned.json').read_text())['pin']!=approved['pin'] or approved['pin']!=provenance['pin']:
        raise ValueError('Native setup differs from approved target')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=provenance['files']:
        raise ValueError('Native source differs from all reviewed pinned Git blobs')
    if (target/'runtime').exists() or (target/'node').exists():raise ValueError('Preserve existing native preparation')
    base_node=Path(shutil.which('node') or '').resolve(strict=True)
    npm_command=Path(shutil.which('npm.cmd' if os.name=='nt' else 'npm') or '').resolve(strict=True)
    candidates=[base_node.parent/'node_modules/npm/bin/npm-cli.js',base_node.parent.parent/'lib/node_modules/npm/bin/npm-cli.js',npm_command]
    npm=next((p for p in candidates if p.is_file() and p.name=='npm-cli.js'),None)
    if npm is None:raise ValueError('Read-only installed npm unavailable')
    node=target/'node'/('node.exe' if os.name=='nt' else 'node');node.parent.mkdir()
    shutil.copyfile(base_node,node)
    if os.name!='nt':node.chmod(0o755)
    if sha256(node)!=sha256(base_node):raise ValueError('Actual copied Node differs')
    app=target/'runtime/app';generator=target/'runtime/generator-toolchain'
    app.mkdir(parents=True);generator.mkdir()
    for name in ['package.json','package-lock.json']:shutil.copyfile(source/name,app/name)
    shutil.copytree(source/'lib',app/'lib')
    immutable_json(generator/'package.json',dict(name='playtestr-owned-yo-generator',version='0.0.0',private=True,
        dependencies={'yeoman-generator':'10.2.1'}))
    shutil.copyfile(package/'generator-package-lock.json',generator/'package-lock.json')
    env=environment(target);env.update(PATH=str(node.parent)+os.pathsep+env['PATH'],
        npm_config_cache=str(target/'npm-cache'),npm_config_prefix=str(target/'npm-prefix'),
        npm_config_ignore_scripts='true',npm_config_bin_links='false',npm_config_audit='false',npm_config_fund='false',
        npm_config_update_notifier='false',npm_config_progress='false',npm_config_engine_strict='true',NO_UPDATE_NOTIFIER='1',CI='true')
    for key,name in [('npm_config_userconfig','empty-user.npmrc'),('npm_config_globalconfig','empty-global.npmrc')]:
        path=target/name;path.write_bytes(b'');env[key]=str(path)
    campaign=NextCampaign();started=time.monotonic();attempts=[];samples=[]
    async def run(command,label,cwd=ROOT):
        remaining=1200-(time.monotonic()-started)
        if remaining<=0:raise ValueError('Native setup execution budget exhausted')
        operation=asyncio.create_task(execute(command,'yo',label,cwd=cwd,env=env,timeout=remaining,campaign=campaign))
        try:
            while not operation.done():
                size=await asyncio.to_thread(usage,target);samples.append(dict(seconds=round(time.monotonic()-started,3),bytes=size))
                if size>512*1024**2:raise ValueError('Declared native active stop exceeded')
                await asyncio.sleep(2)
            result=await operation;attempts.append(result['id']);return result
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
    version=await run([node,'--version'],'native-owned-node-version')
    parts=tuple(map(int,version['output'].strip().lstrip('v').split('.')))
    if not ((parts[0]==22 and parts>=(22,18,0)) or parts>=(24,11,0)):
        raise ValueError('Actual Node fails approved framework engine')
    npm_version=await run([node,npm,'--version'],'native-read-only-npm-version')
    immutable_json(target/'node-prerequisite.json',dict(schema_version=1,node=str(node),node_sha256=sha256(node),
        base_node=str(base_node),base_node_sha256=sha256(base_node),version=version['output'].strip(),
        npm_cli=str(npm),npm_cli_sha256=sha256(npm),npm_version=npm_version['output'].strip(),
        scope='Native installed read-only prerequisites; actual owned copied Node and npm bytes observed independently. No global installs.'))
    for scope,folder in [('app',app),('generator-toolchain',generator)]:
        await run([node,npm,'ci','--omit=dev','--ignore-scripts','--bin-links=false','--no-audit','--no-fund'],
            'native-locked-'+scope+'-fetch-all-hooks-disabled',folder)
    locks=target/'npm-installed-locks';locks.mkdir();inventories={}
    for scope,folder in [('app',app),('generator-toolchain',generator)]:
        files={}
        for path in folder.rglob('*'):
            if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Unreviewed native installed link')
            if not path.is_file():continue
            if len(files)>=30000 or path.stat().st_size>16*1024**2:raise ValueError('Native dependency file/count bound')
            files[path.relative_to(folder).as_posix()]=sha256(path)
        inventories[scope]=files
        shutil.copyfile(folder/'node_modules/.package-lock.json',locks/(scope+'.json'))
    immutable_json(target/'dependency-fetch.json',dict(schema_version=1,attempts=attempts,installed_files=inventories,samples=samples,
        source_lock_sha256=sha256(source/'package-lock.json'),framework_lock_sha256=sha256(generator/'package-lock.json'),
        hooks_disabled=True,bin_links_disabled=True,target_executed=False,framework_executed=False))
    print('Native exact reviewed yo/framework locks fetched without hooks; installed byte review still required.')


if __name__=='__main__':asyncio.run(main())
