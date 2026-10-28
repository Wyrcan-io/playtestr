"""Fetch wheel-only dependencies for one reviewed selected Python target."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import tomllib
import zipfile

sys.dont_write_bytecode=True
from adversarial_process import execute
from next20_check import NAME,RAW,ROOT,NextCampaign
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def environment(target):
    env={k:os.environ[k] for k in ['PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','LANG','LC_ALL'] if k in os.environ}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
        ('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),
        ('XDG_DATA_HOME','home/data'),('XDG_STATE_HOME','home/state'),('PIP_CACHE_DIR','pip-cache')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    shellcache=RAW/'shell-cache/module-analysis';shellcache.parent.mkdir(parents=True,exist_ok=True)
    env.update(PIP_CONFIG_FILE=os.devnull,PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONDONTWRITEBYTECODE='1',
        PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,
        PYTHON_KEYRING_BACKEND='keyring.backends.null.Keyring',PSModuleAnalysisCachePath=str(shellcache),
        TZ='UTC')
    return env


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('project',choices=['jrnl','commitizen-python','pdm'])
    parser.add_argument('stage',choices=['fetch','review','install','verify-installed']);args=parser.parse_args()
    target=RAW/'active'/args.project;source=target/'src'
    marker=json.loads((target/'task-owned.json').read_text())
    if marker['workspace']!=str(ROOT) or marker['campaign']!=NAME:raise ValueError('unowned Python target')
    if measure(target)['total_bytes']>256*1024**2:raise ValueError('initial Python target forecast exceeded')
    env=environment(target);campaign=NextCampaign()
    declaration=json.loads((DOC/args.project/'setup-declaration.json').read_text()) if args.project=='pdm' else None
    if declaration:
        if declaration['pin']!=marker['pin'] or declaration['backend']!='pdm.backend':raise ValueError('PDM source/build declaration differs')
        env.update(PDM_BUILD_SCM_VERSION=declaration['built_source_version'],PDM_CHECK_UPDATE='false')
    async def run(argv,label):
        return await execute(argv,args.project,label,cwd=source,env=env,timeout=600,campaign=campaign)
    metadata=tomllib.loads((source/'pyproject.toml').read_text(encoding='utf-8'))
    venv=target/'venv';python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    requirements=target/'requirements.txt';wheels=target/'wheels'
    if args.stage in {'fetch','review'}:
        if args.stage=='fetch':
            if venv.exists():raise ValueError('venv already exists; inspect completed stage')
            await run([sys.executable,'-B','-m','venv','--copies',venv],'owned-copied-python-venv')
            with requirements.open('x',encoding='utf-8') as stream:
                stream.write('\n'.join(metadata['project']['dependencies']+metadata['build-system']['requires'])+'\n')
            wheels.mkdir()
            await run([python,'-B','-m','pip','download','--only-binary=:all:','--dest',wheels,'-r',requirements],
                      'wheel-only-dependency-fetch-no-target-hooks')
        elif not python.is_file() or not wheels.is_dir() or not requirements.is_file():
            raise ValueError('incomplete existing wheel-only fetch; inspect before review')
        approved_path=target/'wheel-script-approval.json'
        approved=json.loads(approved_path.read_text()) if approved_path.is_file() else {}
        inventory={};reviews=[]
        for path in sorted(wheels.iterdir()):
            if path.suffix!='.whl' or path.stat().st_size>32*1024**2:raise ValueError('wheel type/size bound')
            inventory[path.name]=dict(bytes=path.stat().st_size,sha256=sha256(path))
            with zipfile.ZipFile(path) as archive:
                infos=archive.infolist()
                if len(infos)>10000 or sum(i.file_size for i in infos)>128*1024**2:raise ValueError('wheel expanded bound')
                if any(i.filename.endswith('.pth') for i in infos):raise ValueError('wheel startup hook requires separate source review: '+path.name)
                scripts={i.filename:__import__('hashlib').sha256(archive.read(i)).hexdigest() for i in infos if '.data/scripts/' in i.filename}
                if scripts:
                    approval=approved.get(path.name,{})
                    if approval.get('wheel_sha256')!=sha256(path) or approval.get('scripts')!=scripts:
                        raise ValueError('wheel startup/script hook requires separate source review: '+path.name)
                names=[i.filename for i in infos if i.filename.endswith('.dist-info/METADATA')]
                if len(names)!=1:raise ValueError('wheel metadata identity')
                data=archive.read(names[0])
                metadata_path=target/'dependency-review'/(path.name+'.metadata.txt')
                metadata_path.parent.mkdir(exist_ok=True)
                if metadata_path.exists():
                    if metadata_path.read_bytes()!=data:raise ValueError('retained wheel metadata changed')
                else:
                    with metadata_path.open('xb') as stream:stream.write(data)
                reviews.append(dict(wheel=path.name,metadata_sha256=sha256(metadata_path),
                    startup_hooks=False,reviewed_scripts=scripts,binary_members=[i.filename for i in infos if i.filename.endswith(('.pyd','.dll','.so'))]))
        immutable_json(target/'wheels.json',inventory)
        immutable_json(target/'dependency-review.json',dict(wheels=reviews,approved_for_install=False,
            scope='Wheel metadata and startup hook review inputs; source/backend installation is a separate explicit stage'))
        print('Fetched',len(inventory),'hash-bound wheels; target/build hooks not executed. Review before install.')
    else:
        approval=json.loads((target/'install-approval.json').read_text())
        if approval['review_sha256']!=sha256(target/'dependency-review.json') or not approval['approved']:
            raise ValueError('dependency review approval mismatch')
        for name,row in json.loads((target/'wheels.json').read_text()).items():
            if sha256(target/'wheels'/name)!=row['sha256']:raise ValueError('dependency wheel changed')
        env['PATH']=str(python.parent)+os.pathsep+env['PATH']
        if args.stage=='install':
            await run([python,'-B','-m','pip','install','--no-index','--find-links',target/'wheels',
                '--only-binary=:all:','-r',target/'requirements.txt'],'offline-reviewed-runtime-install')
            await run([python,'-B','-m','pip','install','--no-index','--no-deps','--no-build-isolation',
                '--editable',source],'offline-reviewed-target-editable-build')
        installed={p.relative_to(venv).as_posix():sha256(p) for p in sorted(venv.rglob('*'))
                   if p.is_file() and '__pycache__' not in p.parts}
        if args.stage=='install':
            immutable_json(target/'installed-inventory.json',dict(schema_version=1,files=installed))
            immutable_json(target/'runtime.json',dict(python=str(python),python_sha256=sha256(python),
                base_python=sys.executable,base_python_sha256=sha256(sys.executable),source_pin=marker['pin'],
                installed_inventory_sha256=sha256(target/'installed-inventory.json')))
        elif json.loads((target/'installed-inventory.json').read_text())['files']!=installed:
            raise ValueError('previously installed runtime changed; do not reinstall over unknown bytes')
        module='pdm' if args.project=='pdm' else ('jrnl' if args.project=='jrnl' else 'commitizen')
        version_args=['--version'] if args.project in {'jrnl','pdm'} else ['version','--commitizen']
        result=await run([python,'-B','-m',module,*version_args],'installed-target-version')
        expected=declaration['built_source_version'] if declaration else ('jrnl' if args.project=='jrnl' else metadata['project']['version'])
        if expected not in result['output'].lower():raise ValueError('installed version missing positive target banner')
        immutable_json(target/'build.json',dict(pin=marker['pin'],source_editable=True,
            source_pyproject_sha256=sha256(source/'pyproject.toml'),wheels_sha256=sha256(target/'wheels.json'),
            runtime_sha256=sha256(target/'runtime.json'),version_attempt=result['id'],
            observed_target_bytes=measure(target)['total_bytes']))
        print('Built reviewed pinned source and identified copied runtime:',result['output'].strip())


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');asyncio.run(main())
