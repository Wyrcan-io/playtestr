"""Compile a declared actual source variant and bind exact executed JS bytes."""
import json
import hashlib
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,NextCampaign
from next20_python_setup import environment
from next20_catalog_store import catalog_bytes
from next20_compiled_payloads import capture
from readiness_evidence import immutable_json,sha256


async def rebuild(expected_source,label):
    target=RAW/'active/cz-cli';source=target/'src';builder=target/'build-toolchain'
    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8'));app=target/runtime['app_relative_path']
    actual={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
    if actual!=expected_source:raise ValueError('Actual compiled source differs from explicitly declared variant')
    fetched=json.loads((target/'dependency-fetch.json').read_text(encoding='utf-8'))
    for name,digest in fetched['installed_files']['build-toolchain'].items():
        if sha256(builder/name)!=digest:raise ValueError('Reviewed compiler dependency changed: '+name)
    installed=json.loads((target/'installed-inventory.json').read_text(encoding='utf-8'))
    for name,digest in installed['files'].items():
        if sha256(app/name)!=digest:raise ValueError('Reviewed runtime dependency/launcher changed: '+name)
    node=Path(runtime['node'])
    if sha256(node)!=runtime['node_sha256']:raise ValueError('Actual owned Node executable changed')
    env=environment(target);env.update(PATH=str(node.parent)+os.pathsep+env['PATH'],
        npm_config_cache=str(target/'npm-cache'),BABEL_DISABLE_CACHE='1')
    command=[node,builder/'node_modules/@babel/cli/bin/babel.js',source/'src',
        '--out-dir',app/'dist','--config-file',builder/'babel.config.js','--no-babelrc']
    destination=RAW/'cz-cli/rebuilds'/uuid.uuid4().hex;destination.mkdir(parents=True)
    immutable_json(destination/'planned.json',dict(schema_version=1,label=label,command=list(map(str,command)),cwd=str(builder),
        source_inputs=expected_source,node_sha256=sha256(node),babel_cli_sha256=sha256(command[1]),
        build_config_sha256=sha256(builder/'babel.config.js'),ordinary_credit=0))
    result=await execute(command,
        'cz-cli',label,cwd=builder,env=env,timeout=180,campaign=NextCampaign())
    expected={p.relative_to(source/'src').as_posix() for p in (source/'src').rglob('*.js')}
    compiled={p.relative_to(app).as_posix():sha256(p) for p in (app/'dist').rglob('*') if p.is_file()}
    if {name.removeprefix('dist/') for name in compiled}!=expected or 'Successfully compiled' not in result['output']:
        raise ValueError('Missing actual complete compiled output')
    payloads=capture(app,compiled)
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected_source:
        raise ValueError('Compiler changed declared target source')
    catalog=dict(schema_version=1,runtime_root=app.relative_to(ROOT).as_posix(),
        files={**installed['files'],**compiled},executable=node.relative_to(ROOT).as_posix(),
        executable_sha256=sha256(node),source_inventory_sha256=sha256(target/'installed-inventory.json'))
    encoded=(json.dumps(catalog,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
    catalog_path=RAW/'cz-cli/runtime-catalogs'/(hashlib.sha256(encoded).hexdigest()+'.json')
    archived=RAW/'cz-cli/retained-catalogs-v1/index.json'
    retained_names=json.loads(archived.read_text(encoding='utf-8'))['files'] if archived.is_file() else {}
    if catalog_path.exists() or catalog_path.relative_to(RAW).as_posix() in retained_names:
        if catalog_bytes(catalog_path,hashlib.sha256(encoded).hexdigest())!=encoded:raise ValueError('Runtime catalog content identity collision')
    else:immutable_json(catalog_path,catalog)
    immutable_json(destination/'compiled.json',dict(schema_version=1,source_inputs=expected_source,
        compiled_files=compiled,compiled_payloads=payloads,attempt=result['id'],actual_runtime_catalog_sha256=hashlib.sha256(encoded).hexdigest(),
        runtime_catalog=catalog_path.relative_to(ROOT).as_posix(),
        planned_sha256=sha256(destination/'planned.json'),
        installed_inventory_sha256=sha256(target/'installed-inventory.json'),ordinary_credit=0))
    (target/'launch-runtime-catalog.json').write_bytes(encoded)
    if hashlib.sha256(encoded).hexdigest()!=sha256(target/'launch-runtime-catalog.json'):raise ValueError('Actual launch catalog publication changed')
    return dict(attempt=result['id'],compiled_receipt=(destination/'compiled.json').relative_to(ROOT).as_posix(),
        compiled_receipt_sha256=sha256(destination/'compiled.json'),catalog_sha256=sha256(target/'launch-runtime-catalog.json'),
        catalog_path=catalog_path.relative_to(ROOT).as_posix(),compiled_files=compiled,compiled_payloads=payloads)
