"""Materialize reviewed retained Windows inputs for a new rebuild-proof window."""
import asyncio
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import uuid
import zipfile

from adversarial_process import execute
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_peco_cell_readback import Evidence
from readiness_build_rclone import environment
from readiness_evidence import immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume-after');args=parser.parse_args();resuming=args.resume_after is not None
    if os.name!='nt':raise ValueError('retained Windows prerequisite materialization only')
    target=RAW/'active/peco';package=DOC/'peco';e=Evidence('windows');retained='peco/retained-source/'
    active=[p for p in (RAW/'active').iterdir() if p.is_dir()]
    if resuming:
        if len(args.resume_after)!=32 or any(c not in '0123456789abcdef' for c in args.resume_after):raise ValueError('invalid explicit metadata failure')
        failure=json.loads((RAW/'events'/(args.resume_after+'-finished.json')).read_text())
        if failure['project']!='peco' or failure['label']!='retained-reviewed-module-integrity-before-rebuild-window' or failure['category']!='exit_mismatch' or failure['exit_code']!=1 or active!=[target]:raise ValueError('explicit original offline verification failure required')
    elif active:raise ValueError('preserve single active target')
    removal=e.load(retained+'removed.json')
    if not removal['removed']:raise ValueError('original source/runtime checked removal required')
    gate=json.loads((package/'restoration-rebuild-gate.json').read_text())
    if gate['status']!='open-normal-restored-source-rebuild-proof':raise ValueError('explicit normal rebuild correction gate required')
    owner=e.load(retained+'task-owned.json');primary=json.loads((package/'source-provenance.json').read_text())['files']
    if owner['workspace']!=str(ROOT) or owner['slug']!='peco' or owner['pin']!=json.loads((package/'source-provenance.json').read_text())['pin']:raise ValueError('foreign retained source inputs')
    declaration=RAW/'peco'/('rebuild-materialization-'+uuid.uuid4().hex+'.json')
    if resuming:
        candidates=[p for p in (RAW/'peco').glob('rebuild-materialization-*.json') if p.read_bytes()==(target/'recovery-materialization.json').read_bytes()]
        if len(candidates)!=1:raise ValueError('original materialization declaration missing/ambiguous')
        declaration=candidates[0]
        immutable_json(RAW/'peco/rebuild-materialization-resume-v2.json',dict(schema_version=1,failed_verification=args.resume_after,original_declaration_sha256=sha256(declaration),graph_metadata_recovery_sha256=sha256(RAW/'peco/graph-metadata-recovery-v1/complete.json'),scope='Verify existing retained source/module/runtime bytes without overwriting; resume original offline integrity check after exact historical graph metadata recovery.'))
    else:immutable_json(declaration,dict(schema_version=1,source='retained original source/module archives and actual Windows executable bytes',gate_sha256=sha256(package/'restoration-rebuild-gate.json'),
        original_removed_sha256=e.sha(retained+'removed.json'),target=target.relative_to(ROOT).as_posix(),ordinary_credit=0,project_admissions=0,
        scope='Explicit new materialization after original cleanup. Does not reconstruct any old attempt/frame or claim fresh remote acquisition. Normal source rebuild recoveries still required.'))
    if not resuming:target.mkdir();(target/'src').mkdir()
    def put(relative,body):
        path=target/relative;path.resolve().relative_to(target.resolve())
        if any(p in {'','.','..'} or ':' in p or '\\' in p for p in relative.split('/')):raise ValueError('unsafe retained materialization path')
        if resuming and path.is_file():
            if path.read_bytes()!=body:raise ValueError('existing retained materialization differs')
            return
        path.parent.mkdir(parents=True,exist_ok=True);path.open('xb').write(body)
        if path.read_bytes()!=body:raise ValueError('retained input materialization changed bytes')
    names=['task-owned.json','acquisition.json','runtime.json','build.json','installed-inventory.json','dependency-source-catalog.json','dependency-fetch-review.json',
        'module-fetch.json','native-package-inputs.json','module-metadata-readback.json','binary-buildinfo.json','build-planned.json']
    for name in names:put(name,e.data(retained+name))
    put('recovery-materialization.json',declaration.read_bytes());put('source.tar.gz',e.data(retained+'source.tar.gz'))
    seen={};links={}
    with tarfile.open(fileobj=io.BytesIO(e.data(retained+'source.tar.gz')),mode='r:gz') as archive:
        for member in archive:
            if member.isdir():continue
            name=member.name.split('/',1)[1]
            if member.issym():links[name]=member.linkname;continue
            if not member.isfile() or name not in primary or name in seen or member.size>8*1024**2:raise ValueError('unsafe original source input')
            body=archive.extractfile(member).read(member.size+1)
            if hashlib.sha256(body).hexdigest()!=primary[name]:raise ValueError('original source body changed')
            put('src/'+name,body);seen[name]=True
    if set(seen)!=set(primary) or links!=json.loads((package/'source-link-policy.json').read_text())['omitted_documentation_links']:raise ValueError('original primary/link coverage differs')
    fetch=json.loads((target/'module-fetch.json').read_text());catalog=json.loads((target/'dependency-source-catalog.json').read_text())
    def relative(value):
        path=Path(value);return path.relative_to(target).as_posix()
    for module in fetch['modules']:
        prefix='peco/go-module-corpus/archives/'+module['Path']+'/@v/'+module['Version'];key=module['Path']+'@'+module['Version']
        bodies={field:e.data(prefix+extension) for field,extension in [('Zip','.zip'),('GoMod','.mod'),('Info','.info')]}
        for field,body in bodies.items():put(relative(module[field]),body)
        put(relative(module['Zip'])+'hash',module['Sum'].encode())
        with zipfile.ZipFile(io.BytesIO(bodies['Zip'])) as archive:
            for member in archive.infolist():
                if member.is_dir():continue
                if not member.filename.startswith(key+'/') or member.file_size>8*1024**2:raise ValueError('module input scope/bound differs')
                name=member.filename.removeprefix(key+'/');destination=relative(module['Dir'])+'/'+name;body=archive.read(member)
                if hashlib.sha256(body).hexdigest()!=catalog['files'][destination]:raise ValueError('reviewed module body changed')
                put(destination,body)
    put('build-inputs/pinned.mod',(target/'src/go.mod').read_bytes());put('build-inputs/pinned.sum',(package/'build-checksums-v2.txt').read_bytes())
    index=e.load('peco/go-module-corpus/executables-index.json');archive=e.data('peco/go-module-corpus/executables.tar.xz')
    if hashlib.sha256(archive).hexdigest()!=index['archive_sha256']:raise ValueError('original Windows executable archive changed')
    wanted={name:row for name,row in index['files'].items() if name.startswith('bin/')};binaries={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:xz') as stream:
        for member in stream:
            if member.name not in {r.get('member',n) for n,r in wanted.items()}:continue
            if not member.isfile() or member.size>16*1024**2:raise ValueError('actual executable member bound')
            binaries[member.name]=stream.extractfile(member).read(member.size+1)
    for name,row in wanted.items():
        body=binaries[row.get('member',name)]
        if not body.startswith(b'MZ') or len(body)!=row['bytes'] or hashlib.sha256(body).hexdigest()!=row['sha256']:raise ValueError('original actual Windows binary changed')
        put(name,body)
    for name,expected in catalog['files'].items():
        if sha256(target/name)!=expected:raise ValueError('materialized actual source/module differs')
    build=json.loads((target/'build.json').read_text())
    if sha256(fetch['compiler'])!=build['compiler_sha256'] or any(sha256(p)!=h for p,h in build['compiler_tools'].items()):raise ValueError('read-only compiler prerequisite changed')
    contracts=RAW/'peco/host-contracts-rebuild-v1'
    if not resuming:contracts.mkdir()
    freeze=e.load('peco/host-contracts/development-test-freeze.json')
    for name,expected in freeze['inputs'].items():
        path=contracts/name;path.parent.mkdir(parents=True,exist_ok=True);body=e.data('peco/host-contracts/'+name)
        if hashlib.sha256(body).hexdigest()!=expected:raise ValueError('original frozen host input changed')
        if resuming:
            if path.read_bytes()!=body:raise ValueError('existing original frozen host input changed')
        else:path.open('xb').write(body)
    for name in freeze['directories']:(contracts/name).mkdir(parents=True,exist_ok=True)
    for name in ['scenarios.json','development-test-freeze.json']:
        body=e.data('peco/host-contracts/'+name)
        if resuming:
            if (contracts/name).read_bytes()!=body:raise ValueError('existing original host declaration changed')
        else:(contracts/name).open('xb').write(body)
    env=environment(target);env.update(GOENV='off',GOPROXY='off',GOSUMDB='off',GONOPROXY='none',GONOSUMDB='none')
    result=await execute([fetch['compiler'],'mod','verify','-modfile='+str(target/'build-inputs/pinned.mod')],'peco','retained-reviewed-module-integrity-before-rebuild-window',cwd=target/'src',env=env,timeout=90,campaign=NextCampaign())
    if result['output'].strip()!='all modules verified':raise ValueError('materialized modules failed actual compiler integrity check')
    immutable_json(RAW/'peco/rebuild-materialization-complete-v1.json',dict(schema_version=1,declaration_sha256=sha256(declaration),primary_source_files=len(primary),reviewed_modules=26,
        source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),frozen_host_inputs=len(freeze['inputs']),compiler_module_verify_attempt=result['id'],actual_baseline_executables=wanted,
        scope='Exact reviewed source/module/baseline executable inputs materialized from retained bodies,not new target coverage. Rebuild recovery execution remains required.'))
    print('Materialized121primary files,26reviewed module archives/sources and exact original Windows app/capture; normal rebuilt recovery window ready.')


if __name__=='__main__':asyncio.run(main())
