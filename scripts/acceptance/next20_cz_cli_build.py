"""Review exact installed inputs, then explicitly compile the trusted CLI."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import time

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_cz_cli_lock import closure,BUILD_ROOTS
from next20_compiled_payloads import capture
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native-review',action='store_true');args=parser.parse_args()
    target=RAW/'active/cz-cli';source=target/'src';builder=target/'build-toolchain'
    fetched=json.loads((target/'dependency-fetch.json').read_text(encoding='utf-8'))
    app=target/fetched['app_relative_path'];app.resolve(strict=True).relative_to(target)
    if (app/'dist').exists():raise ValueError('Existing compilation must be inspected, not overwritten')
    provenance=json.loads((DOC/'cz-cli/source-provenance.json').read_text(encoding='utf-8'))
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=provenance['files']:raise ValueError('Canonical source differs')
    canonical=json.loads((source/'package-lock.json').read_text(encoding='utf-8'))
    metadata=json.loads((source/'package.json').read_text(encoding='utf-8'))
    derivation=json.loads((DOC/'cz-cli/build-lock-derivation.json').read_text(encoding='utf-8'))
    if sha256(builder/'package-lock.json')!=derivation['derived_lock_sha256'] or sha256(builder/'babel.config.js')!=derivation['canonical_config_sha256']:
        raise ValueError('Reviewed build lock/config changed')
    package_reviews=[]
    for label,folder,roots in [('build-toolchain',builder,BUILD_ROOTS),('app',app,list(metadata['dependencies']))]:
        expected=closure(canonical['packages'],['node_modules/'+name for name in roots])
        installed=json.loads((folder/'node_modules/.package-lock.json').read_text(encoding='utf-8'))['packages']
        current='win32' if os.name=='nt' else 'linux'
        excluded={n for n,r in expected.items() if r.get('optional') and r.get('os') and current not in r['os']}
        if set(installed)-set(expected) or set(expected)-set(installed)-excluded:
            raise ValueError('Installed dependency physical set differs from canonical closure: '+label+' missing='+str(sorted(set(expected)-set(installed)))+' extra='+str(sorted(set(installed)-set(expected))))
        for name,row in expected.items():
            if name not in installed:
                if (folder/name).exists():raise ValueError('OS-excluded package exists despite missing lock entry: '+name)
                package_reviews.append(dict(scope=label,path=name,skip='upstream optional OS restriction',platforms=row['os']))
                continue
            row=installed[name]
            if row['version']!=expected[name]['version'] or row.get('integrity')!=expected[name].get('integrity'):
                raise ValueError('Installed lock version/integrity differs: '+name)
            package=folder/name/'package.json'
            if not package.is_file():
                declared_os=expected[name].get('os',[])
                if not expected[name].get('optional') or not declared_os or current in declared_os:
                    raise ValueError('Required installed package absent: '+name)
                package_reviews.append(dict(scope=label,path=name,skip='upstream optional OS restriction',platforms=declared_os))
                continue
            value=json.loads(package.read_text(encoding='utf-8'))
            if value['version']!=row['version']:raise ValueError('Installed package metadata differs: '+name)
            package_reviews.append(dict(scope=label,path=name,name=value['name'],version=value['version'],
                license=value.get('license'),metadata_sha256=sha256(package),
                lifecycle_scripts={k:v for k,v in value.get('scripts',{}).items() if k in {'preinstall','install','postinstall','prepare'}}))
        observed={p.relative_to(folder).as_posix():sha256(p) for p in folder.rglob('*') if p.is_file()}
        if observed!=fetched['installed_files'][label]:raise ValueError('Installed dependency bytes changed after fetch: '+label)
    for name in ['package.json','package-lock.json']:
        if sha256(app/name)!=sha256(source/name):raise ValueError('Runtime package metadata differs from canonical source')
    for path in (source/'bin').iterdir():
        if path.is_file() and sha256(app/'bin'/path.name)!=sha256(path):raise ValueError('Actual CLI launcher differs')
    approval=dict(schema_version=1,approved=True,source_provenance_sha256=sha256(DOC/'cz-cli/source-provenance.json'),
        dependency_fetch_sha256=sha256(target/'dependency-fetch.json'),build_lock_sha256=derivation['derived_lock_sha256'],
        packages=package_reviews,all_install_hooks_disabled=True,
        execution='Explicit Babel CLI only with unchanged canonical config; then documented synthetic hook-mode Git message workflows. No root prepare/release/npm adapter installation task.')
    immutable_json(target/'dependency-review.json',approval)
    if args.native_review:
        reviewed=json.loads((DOC/'cz-cli/source-review.json').read_text(encoding='utf-8'))
        actual_packages={(r['scope'],r['path']):r for r in approval['packages']}
        reviewed_packages={(r['scope'],r['path']):r for r in reviewed['packages']}
        if actual_packages!=reviewed_packages or approval['build_lock_sha256']!=reviewed['build_lock_sha256']:
            raise ValueError('Native locked package metadata differs from prior reviewed source inputs')
    else:immutable_json(DOC/'cz-cli/source-review.json',approval)
    prerequisite=json.loads((target/'node-prerequisite.json').read_text(encoding='utf-8'));node=Path(prerequisite['node'])
    if sha256(node)!=prerequisite['node_sha256']:raise ValueError('Owned Node prerequisite changed')
    env=environment(target);env['PATH']=str(node.parent)+os.pathsep+env['PATH']
    env.update(npm_config_cache=str(target/'npm-cache'),BABEL_DISABLE_CACHE='1')
    started=time.monotonic()
    command=[node,builder/'node_modules/@babel/cli/bin/babel.js',source/'src',
        '--out-dir',app/'dist','--config-file',builder/'babel.config.js','--no-babelrc']
    immutable_json(target/'build-planned.json',dict(schema_version=1,command=list(map(str,command)),cwd=str(builder),
        source_inputs=provenance['files'],node_sha256=sha256(node),babel_cli_sha256=sha256(command[1]),
        build_config_sha256=sha256(builder/'babel.config.js')))
    result=await execute(command,
        'cz-cli','reviewed-explicit-babel-build',cwd=builder,env=env,timeout=180,campaign=NextCampaign())
    expected={p.relative_to(source/'src').as_posix() for p in (source/'src').rglob('*.js')}
    actual={p.relative_to(app/'dist').as_posix() for p in (app/'dist').rglob('*') if p.is_file()}
    if actual!=expected or 'Successfully compiled' not in result['output']:raise ValueError('Missing positive complete source build proof')
    modules={p.relative_to(app).as_posix():sha256(p) for p in app.rglob('*') if p.is_file() and p.relative_to(app).parts[0]!='dist'}
    compiled={p.relative_to(app).as_posix():sha256(p) for p in (app/'dist').rglob('*') if p.is_file()}
    payloads=capture(app,compiled)
    immutable_json(target/'installed-inventory.json',dict(schema_version=1,runtime_root=app.relative_to(ROOT).as_posix(),files=modules))
    immutable_json(target/'launch-runtime-catalog.json',dict(schema_version=1,runtime_root=app.relative_to(ROOT).as_posix(),
        files={**modules,**compiled},executable=node.relative_to(ROOT).as_posix(),executable_sha256=sha256(node),
        source_inventory_sha256=sha256(target/'installed-inventory.json')))
    immutable_json(target/'runtime.json',dict(kind='node',node=str(node),node_sha256=sha256(node),
        source_pin=provenance['pin'],app_relative_path=app.name,entrypoint='bin/git-cz',
        prerequisite_sha256=sha256(target/'node-prerequisite.json'),installed_inventory_sha256=sha256(target/'installed-inventory.json')))
    immutable_json(target/'build.json',dict(schema_version=1,pin=provenance['pin'],attempt=result['id'],
        source_inputs={name:digest for name,digest in provenance['files'].items() if name.startswith('src/')},
        compiled_files=compiled,compiled_payloads=payloads,compiled_catalog_sha256=sha256(target/'launch-runtime-catalog.json'),
        planned_sha256=sha256(target/'build-planned.json'),
        runtime_sha256=sha256(target/'runtime.json'),build_config_sha256=sha256(builder/'babel.config.js'),
        installed_dependencies_sha256=sha256(target/'installed-inventory.json'),seconds=round(time.monotonic()-started,3),
        scripts_disabled=True,explicit_build_only=True))
    print('Reviewed pinned dependency identities and compiled',len(compiled),'actual upstream source modules. Ready for the declared public authoring route; no admission credit.')


if __name__=='__main__':asyncio.run(main())
