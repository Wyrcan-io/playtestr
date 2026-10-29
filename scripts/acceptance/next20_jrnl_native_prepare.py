"""Prepare reviewed pinned jrnl and explicit contracts on a fresh native host."""
import asyncio
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tomllib
import urllib.request
import zipfile

sys.dont_write_bytecode=True
from adversarial_process import execute
from next20_acquire import main as acquire_main
from next20_check import DOC,RAW,ROOT,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def primary_json(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:
        data=response.read(4*1024**2+1)
    if len(data)>4*1024**2:raise ValueError('primary wheel metadata bound')
    return json.loads(data)


async def main(project='jrnl',profile=None):
    if platform.system() not in {'Linux','Windows'}:raise ValueError('undeclared jrnl native host')
    host='windows' if os.name=='nt' else 'linux'
    package=DOC/project;target=RAW/'active'/project;campaign=NextCampaign()
    lock=json.loads((package/'native-runtime-lock.json').read_text())
    overrides={}
    if profile:
        profile=profile.resolve(strict=True);profile.relative_to(package.resolve(strict=True))
        declared=json.loads(profile.read_text())
        if (declared['host']!=host or declared['native_runtime_lock_sha256']!=sha256(package/'native-runtime-lock.json') or
                declared['canonical_freeze_sha256']!=sha256(package/'development-test-freeze.json')):
            raise ValueError('native profile does not bind declared host/runtime/contracts')
        overrides=declared['case_profiles']
    if project=='jrnl' and not lock['reviewed_linux_additions']:raise ValueError('Linux dependency review absent')
    if target.exists():raise ValueError('target already active; do not overwrite or repeat native preparation')
    # The source acquirer owns its path/pin/entry/byte checks and runs no hooks.
    previous=sys.argv
    try:
        sys.argv=['next20_acquire.py',project];acquire_main()
    finally:sys.argv=previous
    marker=json.loads((target/'task-owned.json').read_text());source=target/'src'
    provenance=json.loads((package/'source-provenance.json').read_text())
    actual_source={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
    if marker['pin']!=provenance['pin'] or actual_source!=provenance['files']:
        raise ValueError('native acquired source differs from complete pinned canonical content')
    review=json.loads((package/'source-review.json').read_text())
    for name,digest in review['reviewed_source'].items():
        if sha256(source/name)!=digest:raise ValueError('reviewed target source/backend changed: '+name)
    env=environment(target)
    if lock.get('build_environment'):
        declaration=json.loads((package/'setup-declaration.json').read_text())
        if lock['build_environment']!={'PDM_BUILD_SCM_VERSION':declaration['built_source_version']}:
            raise ValueError('native build environment differs from reviewed setup declaration')
        env.update(lock['build_environment'])
    async def run(argv,label):
        return await execute(argv,project,label,cwd=source,env=env,timeout=600,campaign=campaign)
    candidates=[]
    if sys.version_info[:2]==(3,12):candidates.append(Path(sys.executable))
    if os.environ.get('Python3_12_ROOT_DIR'):
        candidates.append(Path(os.environ['Python3_12_ROOT_DIR'])/('python.exe' if os.name=='nt' else 'bin/python'))
    toolcache=os.environ.get('RUNNER_TOOL_CACHE')
    if toolcache:
        for folder in sorted((Path(toolcache)/'Python').glob('3.12.*/x64'),reverse=True):
            candidates.append(folder/('python.exe' if os.name=='nt' else 'bin/python'))
    candidates=[p for p in candidates if p.is_file()]
    if not candidates:raise ValueError('installed read-only Python 3.12 prerequisite missing; no global SDK installation attempted')
    base_python=candidates[0]
    probe=await run([base_python,'-B','-c','import sys; print(sys.version); assert sys.version_info[:2] == (3,12)'],
                    'native-read-only-python312-prerequisite')
    venv=target/'venv'
    await run([base_python,'-B','-m','venv','--copies',venv],'native-owned-copied-venv')
    python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    metadata=tomllib.loads((source/'pyproject.toml').read_text())
    requirements=target/'requirements.txt';constraints=target/'constraints.txt'
    requirements.write_text('\n'.join(metadata['project']['dependencies']+metadata['build-system']['requires'])+'\n',encoding='utf-8',newline='\n')
    constraints.write_text('\n'.join(name+'=='+version for name,version in sorted(lock['versions'].items()))+'\n',encoding='utf-8',newline='\n')
    wheels=target/'wheels';wheels.mkdir()
    await run([python,'-B','-m','pip','download','--only-binary=:all:','--dest',wheels,
        '--constraint',constraints,'-r',requirements],'native-locked-wheel-only-download')
    wheel_inventory={};wheel_reviews=[]
    for path in sorted(wheels.iterdir()):
        if path.suffix!='.whl' or path.stat().st_size>32*1024**2:raise ValueError('native wheel type/size bound')
        with zipfile.ZipFile(path) as archive:
            infos=archive.infolist()
            if len(infos)>10000 or sum(i.file_size for i in infos)>128*1024**2:raise ValueError('native wheel expanded bound')
            if any(i.filename.endswith('.pth') for i in infos):raise ValueError('new native wheel startup hook')
            scripts={i.filename:hashlib.sha256(archive.read(i)).hexdigest() for i in infos if '.data/scripts/' in i.filename}
            if scripts:
                approved=lock.get('backend_script')
                suffix='.exe' if os.name=='nt' else ''
                if not approved or len(scripts)!=1 or not next(iter(scripts)).endswith('/'+approved['name']+suffix):
                    raise ValueError('new native wheel script not reviewed')
                if hashlib.sha256(archive.read(approved['shim_file'])).hexdigest()!=approved['shim_sha256']:
                    raise ValueError('native backend Python shim differs from reviewed source')
            names=[i.filename for i in infos if i.filename.endswith('.dist-info/METADATA')]
            if len(names)!=1:raise ValueError('native wheel metadata coverage')
            data=archive.read(names[0]);info=BytesParser().parsebytes(data)
        name=info['Name'].lower().replace('_','-');version=info['Version']
        if lock['versions'].get(name)!=version:raise ValueError('unreviewed native dependency version: '+name)
        if scripts:
            approved=lock['backend_script'];suffix='.exe' if os.name=='nt' else ''
            if name!=approved['distribution'] or set(scripts)!={name.replace('-','_')+'-'+version+'.data/scripts/'+approved['name']+suffix}:
                raise ValueError('native backend executable distribution/path differs from reviewed package')
        # Bind native extension wheel bytes independently to the primary release,
        # rather than trusting a filename or a locally calculated digest alone.
        primary=primary_json('https://pypi.org/pypi/'+name+'/'+version+'/json')
        matched=[r for r in primary['urls'] if r['filename']==path.name and r['digests']['sha256']==sha256(path)]
        if len(matched)!=1:raise ValueError('native wheel absent from primary release digest inventory')
        wheel_inventory[path.name]=dict(bytes=path.stat().st_size,sha256=sha256(path),url=matched[0]['url'])
        wheel_reviews.append(dict(name=name,version=version,metadata_sha256=hashlib.sha256(data).hexdigest(),startup_hooks=False,reviewed_scripts=scripts))
    immutable_json(target/'wheels.json',wheel_inventory)
    immutable_json(target/'dependency-review.json',dict(approved=True,reviewed_version_lock_sha256=sha256(package/'native-runtime-lock.json'),
        wheels=wheel_reviews,scope='Frozen reviewed versions, primary release wheel digests, no source distributions/startup hooks; only declared synthetic project interactions.'))
    if project!='jrnl':env['PATH']=str(python.parent)+os.pathsep+env['PATH']
    await run([python,'-B','-m','pip','install','--no-index','--find-links',wheels,'--only-binary=:all:',
        '--constraint',constraints,'-r',requirements],'native-offline-reviewed-dependencies')
    await run([python,'-B','-m','pip','install','--no-index','--no-deps','--no-build-isolation',
        '--editable',source],'native-offline-reviewed-editable-source')
    installed={p.relative_to(venv).as_posix():sha256(p) for p in sorted(venv.rglob('*')) if p.is_file() and not p.is_symlink()}
    links={p.relative_to(venv).as_posix():os.readlink(p) for p in venv.iterdir() if p.is_symlink()}
    if links and links!={'lib64':'lib'}:raise ValueError('unreviewed runtime directory link')
    immutable_json(target/'installed-inventory.json',dict(schema_version=1,files=installed,owned_links=links,
        scope='All installed files including executable bytecode; runtime directory alias is recorded and never followed for cleanup.'))
    immutable_json(target/'runtime.json',dict(python=str(python),python_sha256=sha256(python),
        base_python=str(base_python),base_python_sha256=sha256(base_python),source_pin=marker['pin'],
        installed_inventory_sha256=sha256(target/'installed-inventory.json')))
    module=lock.get('module','jrnl');version_args=lock.get('version_args',['--version'])
    version=await run([python,'-B','-m',module,*version_args],'native-built-target-version')
    if lock.get('expected_version','jrnl v4.6') not in version['output']:raise ValueError('native target version mismatch')
    immutable_json(target/'build.json',dict(pin=marker['pin'],source_editable=True,source_pyproject_sha256=sha256(source/'pyproject.toml'),
        wheels_sha256=sha256(target/'wheels.json'),runtime_sha256=sha256(target/'runtime.json'),version_attempt=version['id'],
        observed_target_bytes=measure(target)['total_bytes']))
    if lock.get('generated_source_files'):
        actual={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
        extra=set(actual)-set(provenance['files'])
        if extra!=set(lock['generated_source_files']) or any(actual[n]!=d for n,d in provenance['files'].items()):
            raise ValueError('unexpected generated native source inventory')
        allowed={'src/pdm/VERSION':(lock['expected_version']+'\n').encode(),
            '.pdm-build/.gitignore':('*'+os.linesep).encode(),
            '.pdm-build/_editable_impl_pdm.pth':str(source/'src').encode()}
        if extra!=set(allowed) or any((source/n).read_bytes()!=raw for n,raw in allowed.items()):
            raise ValueError('generated native backend file content differs from declared semantics')
        immutable_json(RAW/project/'native-generated-source.json',dict(schema_version=1,
            primary_source_provenance_sha256=sha256(package/'source-provenance.json'),
            generated_files={n:dict(sha256=actual[n]) for n in sorted(extra)}))
    if measure(target)['total_bytes']>256*1024**2:raise ValueError('native runtime forecast exceeded')
    # Copy reviewed inputs only. A native argv/EOF profile is explicit, with the
    # canonical spec, actual native spec and every exact fixture byte bound.
    if (package/'fixture-git.json').is_file():
        from next20_fixture_git import reconstruct
        reconstruct(package)
    contracts=RAW/project/'host-contracts';contracts.mkdir(parents=True)
    declaration=json.loads((package/'scenarios.json').read_text());canonical=json.loads((package/'development-test-freeze.json').read_text())
    for name,digest in canonical['inputs'].items():
        path=package/name
        if sha256(path)!=digest:raise ValueError('canonical reviewed input changed before native preparation')
        if name.endswith('.json') and any(c['spec']==name for c in declaration['cases']):continue
        destination=contracts/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
    for name in canonical['directories']:(contracts/name).mkdir(parents=True,exist_ok=True)
    cases=[]
    for case in declaration['cases']:
        spec=json.loads((package/case['spec']).read_text())
        spec['command'][0]=os.path.relpath(python,contracts).replace('\\','/')
        if lock.get('explicit_python_wizard_profile'):
            from next20_python_host_profile import wizard_profile
            spec=wizard_profile(spec,dict(case,**overrides.get(case['id'],{})),python,host)
        if project=='jrnl' and host=='linux' and case['id']=='N06':
            steps=spec['steps'];index=next(i for i,s in enumerate(steps) if s.get('key')=='CtrlZ')
            if steps[index+1]!={'key':'Enter'}:raise ValueError('native EOF control group changed')
            spec['steps']=steps[:index]+[{'key':'CtrlD'}]+steps[index+2:]
        if project=='commitizen-python' and host=='linux':
            spec['env']['PATH']='/usr/bin:/bin';spec['env']['GIT_CONFIG_GLOBAL']='/dev/null'
        immutable_json(contracts/case['spec'],spec)
        cases.append(dict(case,canonical_sha256=case['spec_sha256'],spec_sha256=sha256(contracts/case['spec'])))
    declaration['cases']=cases;declaration['host']=host
    immutable_json(contracts/'scenarios.json',declaration)
    frozen_files={p.relative_to(contracts).as_posix():sha256(p) for p in contracts.rglob('*') if p.is_file()}
    immutable_json(contracts/'development-test-freeze.json',dict(canonical_freeze_sha256=sha256(package/'development-test-freeze.json'),
        inputs=frozen_files,**(dict(explicit_profile_sha256=sha256(profile)) if profile else {}),
        profile=lock.get('native_profile','Native copied Python path; Unix N06 EOF CtrlD replaces the documented Windows CtrlZ+Enter group. All semantic saved bytes and other actions unchanged.')))
    immutable_json(RAW/project/'native-prepared.json',dict(schema_version=1,host=host,pin=marker['pin'],
        target_archive_sha256=sha256(target/'source.tar.gz'),runtime_sha256=sha256(target/'runtime.json'),
        build_sha256=sha256(target/'build.json'),host_contract_freeze_sha256=sha256(contracts/'development-test-freeze.json'),
        target_bytes=measure(target)['total_bytes'],new_project_admissions=0))
    print('Prepared reviewed native',project,'runtime and exact host profile:',host,'twenty cases; no execution/admission credit.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--project',default='jrnl');parser.add_argument('--profile',type=Path);args=parser.parse_args()
    if '/' in args.project or '\\' in args.project or not (DOC/args.project/'source-provenance.json').is_file():raise ValueError('undeclared project')
    asyncio.run(main(args.project,args.profile))
