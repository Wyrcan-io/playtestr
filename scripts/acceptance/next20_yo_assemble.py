"""Copy one declared interpreted-source variant into the actual owned runtime."""
import hashlib
import json
import uuid

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


async def assemble(expected_source, label):
    target=RAW/'active/yo';source=target/'src'
    build=json.loads((target/'build.json').read_text())
    if build['mode']!='copied-interpreted-source' or build['compiled_files']:
        raise ValueError('Interpreted source assembly requires original honest mode')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected_source:
        raise ValueError('Actual source differs from declared complete variant')
    installed=json.loads((target/'installed-inventory.json').read_text())
    runtime_root=ROOT/installed['runtime_root']
    runtime_root.resolve(strict=True).relative_to(target.resolve(strict=True))
    mutable=set(build['copied_source_files'].values())
    if {p.relative_to(runtime_root).as_posix() for p in runtime_root.rglob('*') if p.is_file()}!=set(installed['files']):
        raise ValueError('Actual runtime file membership changed')
    for name,digest in installed['files'].items():
        if name not in mutable and sha256(runtime_root/name)!=digest:
            raise ValueError('Reviewed runtime dependency changed: '+name)
    runtime=json.loads((target/'runtime.json').read_text())
    if sha256(runtime['node'])!=runtime['node_sha256']:raise ValueError('Owned Node changed')
    destination=RAW/'yo/assemblies'/uuid.uuid4().hex
    destination.mkdir(parents=True)
    immutable_json(destination/'planned.json',dict(schema_version=1,label=label,mode=build['mode'],
        source_inputs=expected_source,copied_source_files=build['copied_source_files'],
        installed_inventory_sha256=sha256(target/'installed-inventory.json'),
        executable_sha256=runtime['node_sha256'],compiler_execution=False,ordinary_credit=0))
    files=dict(installed['files']);payloads={}
    for original,copied in build['copied_source_files'].items():
        data=(source/original).read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected_source[original]:raise ValueError('Source changed during copy')
        (runtime_root/copied).write_bytes(data)
        if sha256(runtime_root/copied)!=expected_source[original]:raise ValueError('Actual interpreted-source copy differs')
        files[copied]=expected_source[original]
        payload=RAW/'yo/interpreted-payloads'/expected_source[original]
        payload.parent.mkdir(parents=True,exist_ok=True)
        if payload.exists():
            if payload.read_bytes()!=data:raise ValueError('Interpreted payload hash collision')
        else:payload.write_bytes(data)
        payloads[copied]=dict(sha256=expected_source[original],path=payload.relative_to(ROOT).as_posix())
    catalog=dict(schema_version=1,runtime_root=runtime_root.relative_to(ROOT).as_posix(),files=files,
        executable=ROOT.joinpath(runtime['node']).relative_to(ROOT).as_posix(),
        executable_sha256=runtime['node_sha256'],source_inventory_sha256=sha256(target/'installed-inventory.json'))
    encoded=(json.dumps(catalog,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
    digest=hashlib.sha256(encoded).hexdigest()
    catalog_path=RAW/'yo/runtime-catalogs'/(digest+'.json');catalog_path.parent.mkdir(parents=True,exist_ok=True)
    if catalog_path.exists():
        if catalog_path.read_bytes()!=encoded:raise ValueError('Runtime catalog identity collision')
    else:catalog_path.write_bytes(encoded)
    receipt=destination/'assembled.json'
    immutable_json(receipt,dict(schema_version=1,mode=build['mode'],source_inputs=expected_source,
        copied_source_files=build['copied_source_files'],copied_payloads=payloads,
        runtime_catalog=catalog_path.relative_to(ROOT).as_posix(),runtime_catalog_sha256=digest,
        planned_sha256=sha256(destination/'planned.json'),compiler_execution=False,ordinary_credit=0))
    (target/'launch-runtime-catalog.json').write_bytes(encoded)
    return dict(mode=build['mode'],assembly_receipt=receipt.relative_to(ROOT).as_posix(),
        assembly_receipt_sha256=sha256(receipt),catalog_sha256=digest,
        catalog_path=catalog_path.relative_to(ROOT).as_posix(),copied_payloads=payloads,compiler_execution=False)
