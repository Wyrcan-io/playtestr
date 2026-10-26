"""Prepare exact yo runtime and a separate reviewed official generator framework."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import time

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_cz_cli_lock import closure
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256
from readiness_build_plop import usage


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['lock','fetch']);args=parser.parse_args()
    target=RAW/'active/yo';source=target/'src';package=DOC/'yo';runtime=target/'runtime'
    provenance=json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=provenance['files']:
        raise ValueError('Canonical yo source changed before setup')
    sdk=RAW/'toolchain/node-sdk/node-v22.23.4-win-x64'
    owned=json.loads((sdk/'task-owned.json').read_text(encoding='utf-8'))
    if owned['version']!='v22.23.4' or owned['node_sha256']!='dccc52de28d8df2ee22d2062424f8c563070d95d8ad70c54c4bf01d590dec14f':
        raise ValueError('Reviewed official SDK differs from actual previously executed native Node22.23.4 bytes')
    for name,digest in owned['files'].items():
        if sha256(sdk/name)!=digest:raise ValueError('Owned SDK input changed: '+name)
    sdk_root=sdk/'node-v22.23.4-win-x64';node=target/'node/node.exe';npm=sdk_root/'node_modules/npm/bin/npm-cli.js'
    framework=target/'dependency-research/yeoman-generator/10.2.1'
    primary=json.loads((framework/'registry.json').read_text(encoding='utf-8'))
    metadata=json.loads((source/'package.json').read_text(encoding='utf-8'))
    canonical=json.loads((source/'package-lock.json').read_text(encoding='utf-8'))
    selected=closure(canonical['packages'],['node_modules/'+n for n in metadata['dependencies']])
    app=runtime/'app';generator=runtime/'generator-toolchain'
    if args.stage=='lock':
        if runtime.exists() or node.parent.exists():raise ValueError('Preserve existing runtime preparation attempt')
        node.parent.mkdir();shutil.copyfile(sdk_root/'node.exe',node)
        if sha256(node)!=owned['node_sha256']:raise ValueError('Owned interpreter copy differs')
        app.mkdir(parents=True);generator.mkdir()
        for name in ['package.json','package-lock.json']:shutil.copyfile(source/name,app/name)
        shutil.copytree(source/'lib',app/'lib')
        immutable_json(generator/'package.json',dict(name='playtestr-owned-yo-generator',version='0.0.0',private=True,
            dependencies={'yeoman-generator':'10.2.1'}))
        declaration=dict(schema_version=1,project='yo',pin=provenance['pin'],source_provenance_sha256=sha256(package/'source-provenance.json'),
            approved_for='Owned Node/npm prerequisite execution and package-lock-only resolution, then hooks-disabled dependency fetch. Target/framework execution requires installed source/metadata review.',
            canonical_source_files=len(provenance['files']),canonical_runtime_packages=len(selected),
            canonical_root_scripts=metadata['scripts'],all_lifecycle_hooks_disabled=True,bin_links_disabled=True,
            plugin_framework=dict(package='yeoman-generator',version='10.2.1',primary_metadata_sha256=sha256(framework/'registry.json'),
                source_archive_sha256=sha256(framework/'source.tgz'),integrity=primary['dist']['integrity'],license=primary['license'],
                engine=primary['engines'],source_reviewed=['dist/index.js','dist/generator.js','dist/constants.js','dist/actions/lifecycle.js','package.json'],
                compatibility='Published source requires Environment>=4.0.0-rc.0; pinned yo uses6.0.1. No version-check bypass. Actual execution still required.'),
            prerequisite=dict(version='v22.23.4',node_sha256=owned['node_sha256'],official_archive_sha256=owned['archive_sha256'],
                checksum_manifest_sha256=owned['checksum_manifest_sha256'],npm_cli_sha256=sha256(npm)),
            workload='Documented local generator path; synthetic project label/language/README prompts and saved files through real Generator APIs. No fake adapter, mocked environment, package installation by generators, commits or external services.',
            guardrails=dict(setup_execution_budget_seconds=1200,active_stop_bytes=512*1024**2,global_install=False),
            documentation=['https://yeoman.io/authoring/','https://yeoman.io/authoring/user-interactions.html'],new_project_admissions=0)
        immutable_json(package/'setup-declaration.json',declaration)
    else:
        declaration=json.loads((package/'setup-declaration.json').read_text(encoding='utf-8'))
        if declaration['pin']!=provenance['pin'] or sha256(node)!=owned['node_sha256']:raise ValueError('Reviewed setup identity changed')
        if (app/'node_modules').exists() or (generator/'node_modules').exists():raise ValueError('Preserve prior fetch attempt, do not reinstall')
    env=environment(target);env.update(PATH=str(node.parent)+os.pathsep+env['PATH'],
        npm_config_cache=str(target/'npm-cache'),npm_config_prefix=str(target/'npm-prefix'),
        npm_config_ignore_scripts='true',npm_config_bin_links='false',npm_config_audit='false',npm_config_fund='false',
        npm_config_update_notifier='false',npm_config_progress='false',npm_config_engine_strict='true',NO_UPDATE_NOTIFIER='1',CI='true')
    for key,name in [('npm_config_userconfig','empty-user.npmrc'),('npm_config_globalconfig','empty-global.npmrc')]:
        path=target/name
        if path.exists():
            if path.read_bytes()!=b'':raise ValueError('Owned npm config changed')
        else:path.write_bytes(b'')
        env[key]=str(path)
    campaign=NextCampaign();started=time.monotonic();attempts=[];samples=[]
    async def run(command,label,cwd=ROOT):
        remaining=1200-(time.monotonic()-started)
        if remaining<=0:raise ValueError('Setup execution budget exhausted')
        operation=asyncio.create_task(execute(command,'yo',label,cwd=cwd,env=env,timeout=remaining,campaign=campaign))
        try:
            while not operation.done():
                size=await asyncio.to_thread(usage,target);samples.append(dict(seconds=round(time.monotonic()-started,3),bytes=size))
                if size>512*1024**2:raise ValueError('Declared active target stop exceeded')
                await asyncio.sleep(2)
            result=await operation;attempts.append(result['id']);return result
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
    if args.stage=='lock':
        version=await run([node,'--version'],'reviewed-owned-node22-version')
        npm_version=await run([node,npm,'--version'],'reviewed-owned-npm-version')
        if version['output'].strip()!='v22.23.4':raise ValueError('Actual owned SDK version differs')
        immutable_json(target/'node-prerequisite.json',dict(schema_version=1,node=str(node),node_sha256=sha256(node),
            base_node=str(sdk_root/'node.exe'),base_node_sha256=sha256(sdk_root/'node.exe'),version=version['output'].strip(),
            npm_cli=str(npm),npm_cli_sha256=sha256(npm),npm_version=npm_version['output'].strip(),sdk_marker_sha256=sha256(sdk/'task-owned.json')))
        await run([node,npm,'install','--package-lock-only','--ignore-scripts','--bin-links=false','--no-audit','--no-fund'],
            'official-framework-lock-only-no-install-hooks',generator)
        lock=json.loads((generator/'package-lock.json').read_text(encoding='utf-8'))
        for name,row in lock['packages'].items():
            if not name:continue
            if not row.get('resolved','').startswith('https://registry.npmjs.org/') or not row.get('integrity','').startswith(('sha512-','sha1-')):
                raise ValueError('Noncanonical framework dependency source: '+name)
        if lock['packages']['node_modules/yeoman-generator']['integrity']!=primary['dist']['integrity']:raise ValueError('Resolved framework differs from reviewed primary source')
        shutil.copyfile(generator/'package-lock.json',package/'generator-package-lock.json')
        immutable_json(target/'framework-lock.json',dict(schema_version=1,attempts=attempts,package_lock_sha256=sha256(generator/'package-lock.json'),
            packages=len(lock['packages'])-1,primary_framework_sha256=sha256(framework/'registry.json'),samples=samples,
            scope='Lock resolution only. Application/framework not executed or installed. No compatibility/admission credit.'))
        print('Resolved exact official framework lock:',len(lock['packages'])-1,'packages; hooks disabled; target not executed.')
        return
    if sha256(generator/'package-lock.json')!=sha256(package/'generator-package-lock.json'):raise ValueError('Reviewed generator lock changed')
    for scope,folder in [('app',app),('generator-toolchain',generator)]:
        await run([node,npm,'ci','--omit=dev','--ignore-scripts','--bin-links=false','--no-audit','--no-fund'],
            'locked-'+scope+'-fetch-all-hooks-disabled',folder)
    for name,digest in owned['files'].items():
        if sha256(sdk/name)!=digest:raise ValueError('SDK changed during npm setup')
    inventories={};locks=target/'npm-installed-locks';locks.mkdir()
    for scope,folder in [('app',app),('generator-toolchain',generator)]:
        files={}
        for path in folder.rglob('*'):
            if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Unreviewed installed link')
            if not path.is_file():continue
            if len(files)>30000 or path.stat().st_size>16*1024**2:raise ValueError('Installed file/count bound')
            files[path.relative_to(folder).as_posix()]=sha256(path)
        inventories[scope]=files;shutil.copyfile(folder/'node_modules/.package-lock.json',locks/(scope+'.json'))
    immutable_json(target/'dependency-fetch.json',dict(schema_version=1,attempts=attempts,installed_files=inventories,samples=samples,
        source_lock_sha256=sha256(source/'package-lock.json'),framework_lock_sha256=sha256(generator/'package-lock.json'),
        hooks_disabled=True,bin_links_disabled=True,target_executed=False,framework_executed=False))
    print('Fetched locked yo and official generator dependencies without hooks; installed metadata/source review required before target execution.')


if __name__=='__main__':asyncio.run(main())
