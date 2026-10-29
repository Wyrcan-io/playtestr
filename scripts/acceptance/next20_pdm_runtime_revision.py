"""Preserve PDM's original environment and build a declared lock-compatible one."""
import argparse
import asyncio
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tomllib
import urllib.request
import zipfile

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure

VERSIONS={'unearth':'0.18.2','hishel':'1.2.1'}
PROBE="import importlib.metadata as m,json,httpx;from unearth.fetchers import PyPIClient;from pdm.models.session import PDMPyPIClient;print(json.dumps(dict(versions={n:m.version(n) for n in ['pdm','unearth','hishel','httpx']},unearth_inherits_httpx=issubclass(PyPIClient,httpx.Client),pdm_inherits_httpx=issubclass(PDMPyPIClient,httpx.Client),unearth_mro=[c.__module__+'.'+c.__name__ for c in PyPIClient.__mro__])))"


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['fetch','build','activate']);args=parser.parse_args()
    target=RAW/'active/pdm';source=target/'src';root=RAW/'pdm/runtime-revision/v2';package=DOC/'pdm'
    old_python=target/('venv/Scripts/python.exe' if os.name=='nt' else 'venv/bin/python')
    new_venv=target/'venv-v2';new_python=new_venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    env=environment(target);env.update(PDM_CHECK_UPDATE='false',PDM_BUILD_SCM_VERSION=json.loads((package/'setup-declaration.json').read_text())['built_source_version'])
    campaign=NextCampaign()
    async def run(argv,label,timeout=180,cwd=ROOT):return await execute(argv,'pdm',label,cwd=cwd,env=env,timeout=timeout,campaign=campaign)
    if args.stage=='fetch':
        if root.exists():raise ValueError('preserve original runtime revision attempt')
        if measure(target)['total_bytes']+128*1024**2>512*1024**2:raise ValueError('declared PDM runtime forecast exhausted')
        lock=tomllib.loads((source/'pdm.lock').read_text(encoding='utf-8'))
        for name,version in VERSIONS.items():
            if {r['version'] for r in lock['package'] if r['name']==name}!={version}:raise ValueError('proposed versions differ from pinned upstream lock')
        root.mkdir(parents=True);prior=root/'prior';prior.mkdir()
        preserved={}
        for name in ['runtime.json','build.json','installed-inventory.json','wheels.json','dependency-review.json','install-approval.json','requirements.txt']:
            shutil.copyfile(target/name,prior/name);preserved[name]=sha256(prior/name)
        immutable_json(root/'declaration.json',dict(schema_version=1,source_pin='201bdc719c15a7c86cc305c0c788fe9cbdef15c3',
            upstream_lock_sha256=sha256(source/'pdm.lock'),constraints=VERSIONS,preserved_original_metadata=preserved,
            actual_original_runtime_directory='venv',proposed_new_runtime_directory='venv-v2',original_runtime_kept_intact=True,
            failure_trace_sha256=sha256(RAW/'pdm/import-diagnostic/v2/report.json'),maximum_mro_probes=2,
            scope='Normal PDM dependency choices from its own pinned lock,not a Playtestr/PDM source patch. Preserve initial15/5 and original environment. Import/state oracles unchanged. Entire new20-case/native qualification required; no inherited outcome credit.'))
        (root/'constraints.txt').write_text(''.join(name+'=='+version+'\n' for name,version in VERSIONS.items()),encoding='utf-8',newline='\n')
        before=await run([old_python,'-B','-c',PROBE],'pdm-original-runtime-http-client-class-proof')
        original=json.loads(before['output'])
        if original['unearth_inherits_httpx'] or original['pdm_inherits_httpx']:raise ValueError('original incompatible class relationship not reproduced')
        immutable_json(root/'original-class-proof.json',dict(original,attempt=before['id'],qualification_credit=0))
        wheels=root/'wheels';wheels.mkdir()
        await run([old_python,'-B','-m','pip','download','--only-binary=:all:','--no-deps','--dest',wheels,
            *[name+'=='+version for name,version in VERSIONS.items()]],'pdm-upstream-locked-client-wheel-fetch-no-hooks',300)
        reviews=[];primary=root/'primary';primary.mkdir()
        for path in sorted(wheels.iterdir()):
            if path.suffix!='.whl' or path.stat().st_size>8*1024**2:raise ValueError('unexpected new wheel type/size')
            with zipfile.ZipFile(path) as wheel:
                names=wheel.namelist()
                if len(names)>5000 or sum(i.file_size for i in wheel.infolist())>32*1024**2 or any(n.endswith('.pth') or '.data/scripts/' in n for n in names):raise ValueError('unreviewed new wheel startup/script inputs')
                metadata=[n for n in names if n.endswith('.dist-info/METADATA')]
                if len(metadata)!=1:raise ValueError('new wheel metadata ambiguous')
                info=BytesParser().parsebytes(wheel.read(metadata[0]));name=info['Name'].lower().replace('_','-');version=info['Version']
                if VERSIONS.get(name)!=version:raise ValueError('new wheel not exact upstream lock version')
                if name=='unearth':
                    text=wheel.read('unearth/fetchers/sync.py').decode('utf-8')
                    if 'class PyPIClient(httpx.Client)' not in text or 'import httpx2' in text:raise ValueError('lockfile client no longer has expected compatible base')
                with urllib.request.urlopen('https://pypi.org/pypi/'+name+'/'+version+'/json',timeout=30) as response:payload=response.read(4*1024**2+1)
                if len(payload)>4*1024**2:raise ValueError('primary release metadata bound')
                release=json.loads(payload);matches=[r for r in release['urls'] if r['filename']==path.name]
                if len(matches)!=1 or matches[0]['digests']['sha256']!=sha256(path) or matches[0]['size']!=path.stat().st_size:raise ValueError('new wheel primary checksum differs')
                original_metadata=primary/(path.name+'.json');original_metadata.write_bytes(payload)
                reviews.append(dict(name=name,version=version,wheel=path.name,sha256=sha256(path),bytes=path.stat().st_size,
                    primary_metadata_sha256=sha256(original_metadata),license=info.get('License-Expression') or info.get('License'),
                    wheel_python_sources={n:hashlib.sha256(wheel.read(n)).hexdigest() for n in names if n.endswith('.py')},startup_hooks=False))
        if len(reviews)!=2:raise ValueError('two exact reviewed upstream-locked clients required')
        immutable_json(root/'reviewed-wheels.json',dict(schema_version=1,approved_for_offline_runtime_build=True,wheels=reviews,
            declaration_sha256=sha256(root/'declaration.json'),scope='Exact primary-release pure Python package bytes. No wheel was installed or imported during fetch/review; target source and original environment unchanged.'))
        print('Preserved original incompatible class proof; verified2 exact upstream-lock wheels against primary releases; new runtime build pending');return
    review=json.loads((root/'reviewed-wheels.json').read_text())
    if review['declaration_sha256']!=sha256(root/'declaration.json') or not review['approved_for_offline_runtime_build']:raise ValueError('runtime build approval differs')
    for row in review['wheels']:
        if sha256(root/'wheels'/row['wheel'])!=row['sha256']:raise ValueError('reviewed new wheel changed')
    if args.stage=='build':
        if new_venv.exists():raise ValueError('preserve partial/new runtime; inspect before any retry')
        await run([sys.executable,'-B','-m','venv','--copies',new_venv],'pdm-separate-owned-locked-runtime-venv',180)
        env['PATH']=str(new_python.parent)+os.pathsep+env['PATH']
        await run([new_python,'-B','-m','pip','install','--no-index','--find-links',target/'wheels','--find-links',root/'wheels',
            '--constraint',root/'constraints.txt','--only-binary=:all:','-r',root/'prior/requirements.txt'],'pdm-offline-upstream-locked-runtime-dependencies',300)
        await run([new_python,'-B','-m','pip','install','--no-index','--no-deps','--no-build-isolation','--editable',source],
            'pdm-same-reviewed-source-separate-locked-editable-build',300,cwd=source)
        await run([new_python,'-B','-m','pip','check'],'pdm-locked-runtime-declared-dependency-consistency')
        result=await run([new_python,'-B','-c',PROBE],'pdm-upstream-locked-http-client-class-proof')
        observed=json.loads(result['output'])
        if not observed['unearth_inherits_httpx'] or not observed['pdm_inherits_httpx'] or any(observed['versions'][n]!=v for n,v in VERSIONS.items()):raise ValueError('new client hierarchy/version still incompatible')
        version=await run([new_python,'-B','-m','pdm','--version'],'pdm-locked-runtime-real-version')
        if env['PDM_BUILD_SCM_VERSION'] not in version['output']:raise ValueError('new actual target version differs')
        files={p.relative_to(new_venv).as_posix():sha256(p) for p in new_venv.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        immutable_json(root/'installed-inventory.json',dict(schema_version=1,files=files))
        immutable_json(root/'ready.json',dict(schema_version=1,review_sha256=sha256(root/'reviewed-wheels.json'),
            installed_inventory_sha256=sha256(root/'installed-inventory.json'),actual_python=str(new_python),actual_python_sha256=sha256(new_python),
            actual_runtime_directory='venv-v2',class_proof=observed,class_proof_attempt=result['id'],version_attempt=version['id'],
            original_runtime_untouched=True,activated=False,qualification_credit=0))
        print('Separate ordinary PDM runtime built offline; upstream-locked clients have compatible actual bases; dependency check/version passed; activation/fresh scenarios pending');return
    ready=json.loads((root/'ready.json').read_text());inventory=json.loads((root/'installed-inventory.json').read_text())
    if ready['review_sha256']!=sha256(root/'reviewed-wheels.json') or ready['installed_inventory_sha256']!=sha256(root/'installed-inventory.json'):raise ValueError('new runtime readiness subject changed')
    for name,digest in inventory['files'].items():
        if sha256(new_venv/name)!=digest:raise ValueError('new runtime actual bytes changed')
    prior=json.loads((root/'declaration.json').read_text())['preserved_original_metadata']
    for name,digest in prior.items():
        if sha256(target/name)!=digest:raise ValueError('current original runtime selector changed before explicit activation')
    old_runtime=json.loads((root/'prior/runtime.json').read_text());old_build=json.loads((root/'prior/build.json').read_text())
    runtime=dict(old_runtime,python=str(new_python),python_sha256=sha256(new_python),runtime_directory='venv-v2',runtime_revision=2,
        installed_inventory_sha256=sha256(root/'installed-inventory.json'),additional_reviewed_wheels_sha256=sha256(root/'reviewed-wheels.json'))
    (target/'installed-inventory.json').write_bytes((root/'installed-inventory.json').read_bytes())
    (target/'runtime.json').write_text(json.dumps(runtime,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    build=dict(old_build,runtime_sha256=sha256(target/'runtime.json'),version_attempt=ready['version_attempt'],runtime_revision=2,
        previous_actual_build_sha256=prior['build.json'],additional_reviewed_wheels_sha256=sha256(root/'reviewed-wheels.json'),observed_target_bytes=measure(target)['total_bytes'])
    (target/'build.json').write_text(json.dumps(build,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(root/'activated.json',dict(schema_version=1,old_runtime_sha256=prior['runtime.json'],new_runtime_sha256=sha256(target/'runtime.json'),
        old_build_sha256=prior['build.json'],new_build_sha256=sha256(target/'build.json'),original_runtime_still_present=True,
        original_runtime_metadata_preserved=True,current_runtime_directory='venv-v2',qualification_credit=0,
        scope='Explicit selector transition after new actual runtime verification. No original environment payload overwritten. All cases/public repeat/final/native evidence must execute afresh on the newly selected runtime.'))
    print('Activated explicitly verified separate PDM runtime; original environment and metadata preserved; no old outcome transfer')


if __name__=='__main__':asyncio.run(main())
