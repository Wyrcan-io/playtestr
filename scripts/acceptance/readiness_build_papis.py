"""Build pinned Papis with owned wheels and its reviewed python-doi source build."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import sys
import tomllib
import urllib.request
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_acquire_plop import extract_source


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    target=RAW/'active/papis'
    marker=json.loads((target/'task-owned.json').read_text())
    if marker['workspace']!=str(ROOT) or marker['project']!='papis/papis':
        raise RuntimeError('unowned Papis tree')
    source=target/'src'
    license=(source/'LICENSE').read_text(encoding='utf-8')
    if 'GNU GENERAL PUBLIC LICENSE' not in license:
        raise RuntimeError('unreviewed Papis license')
    metadata=tomllib.loads((source/'pyproject.toml').read_text(encoding='utf-8'))
    env={k:os.environ[k] for k in ['PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','LANG','LC_ALL'] if k in os.environ}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
        ('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),('PIP_CACHE_DIR','pip-cache')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env.update(PIP_CONFIG_FILE=os.devnull,PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONDONTWRITEBYTECODE='1',
               PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    async def run(argv,label):
        task=asyncio.create_task(execute(argv,'papis',label,cwd=source,env=env,timeout=1200,campaign=Campaign()))
        observations=[]
        try:
            while not task.done():
                size=await asyncio.to_thread(usage,target)
                observations.append(size)
                if size>768*1024**2:raise RuntimeError('stop before active target storage ceiling')
                await asyncio.sleep(2)
            return await task
        finally:
            if not task.done():
                task.cancel()
                try:await task
                except asyncio.CancelledError:pass
            import uuid
            immutable_json(target/f'{label}-{uuid.uuid4().hex}-storage.json',
                           dict(observed_bytes=observations,measurement='periodic; not an exact peak or quota'))
    venv=target/'venv'
    if args.resume:
        if (target/'build.json').exists() or not (venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')).is_file():
            raise RuntimeError('resume requires the unfinished owned venv')
    else:
        await run([sys.executable,'-m','venv','--copies',venv],'owned-runtime-venv')
    python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    requirements=target/'runtime-requirements.txt'
    requirements.write_text('\n'.join([*metadata['project']['dependencies'],'hatchling>=1.10.0','editables','setuptools','wheel'])+'\n',encoding='utf-8')
    wheels=target/'wheels';wheels.mkdir(exist_ok=args.resume)
    await run([python,'-m','pip','download','--only-binary=:all:','--dest',wheels,'setuptools','wheel'],
              'reviewed-packaging-wheel-download')
    await run([python,'-m','pip','install','--no-index','--find-links',wheels,'setuptools','wheel'],
              'offline-packaging-wheel-install')
    review=json.loads((ROOT/'docs/validation/runner-readiness-ten-project-pass/papis/source-dependency-review.json').read_text(encoding='utf-8-sig'))
    dependency_root=target/'dependency-review';dependency_root.mkdir(exist_ok=True)
    for dependency in review['dependencies']:
        # The resolved arxiv version uses httpx; its older feedparser/sgmllib
        # dependency is absent. Preserve the historical review without building it.
        if dependency['name']!='python-doi':continue
        archive=dependency_root/dependency['filename']
        if not archive.exists():
            with urllib.request.urlopen(dependency['url'],timeout=30) as response:
                data=response.read(review['archive_limit_bytes']+1)
            if len(data)>review['archive_limit_bytes']:raise RuntimeError('reviewed dependency archive bound')
            archive.write_bytes(data)
        if sha256(archive)!=dependency['sha256']:raise RuntimeError('reviewed dependency archive changed')
        existing=list(wheels.glob(dependency['name'].replace('-','_')+'-'+dependency['version']+'-*.whl'))
        if existing:
            prior=json.loads((target/'wheels.json').read_text(encoding='utf-8-sig')) if args.resume else {}
            if len(existing)!=1 or prior.get(existing[0].name,{}).get('sha256')!=sha256(existing[0]):
                raise RuntimeError('resumed source wheel lacks its original immutable hash')
            continue
        extracted=dependency_root/(dependency['name']+'-reviewed-source-'+uuid.uuid4().hex[:8])
        extract_source(archive.read_bytes(),extracted,expanded_limit=review['expanded_limit_bytes'],
            entry_limit=review['entry_limit'],member_limit=review['member_limit_bytes'])
        for name,digest in dependency['reviewed_build_files'].items():
            relative='/'.join(name.split('/')[1:])
            if sha256(extracted/relative)!=digest:raise RuntimeError('reviewed dependency setup changed')
        await run([python,'-m','pip','wheel','--no-deps','--no-build-isolation','--no-index',
            '--wheel-dir',wheels,extracted],'reviewed-source-wheel-'+dependency['name'])
    await run([python,'-m','pip','download','--only-binary=:all:','--find-links',wheels,'--dest',wheels,'-r',requirements],
              'reviewed-runtime-wheel-download')
    wheel_identity={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in wheels.iterdir()}
    wheel_manifest=target/'wheel-manifests'/(uuid.uuid4().hex+'.json')
    immutable_json(wheel_manifest,wheel_identity)
    await run([python,'-m','pip','install','--no-index','--find-links',wheels,'--only-binary=:all:',
               '-r',requirements],'offline-runtime-wheel-install')
    await run([python,'-m','pip','install','--no-index','--no-deps','--no-build-isolation','--editable',source],
              'reviewed-source-editable-build')
    result=await run([python,'-m','papis','--version'],'built-version')
    if metadata['project']['version'] not in result['output']:raise RuntimeError('built Papis version mismatch')
    immutable_json(target/'runtime.json',dict(python=str(python),python_version=sys.version,
        python_sha256=sha256(python),source_pin=marker['pin']))
    immutable_json(target/'build.json',dict(pin=marker['pin'],license_sha256=sha256(source/'LICENSE'),
        source_editable=True,build_backend=metadata['build-system'],dependency_wheels=wheel_identity,
        wheel_manifest=wheel_manifest.relative_to(target).as_posix(),
        version_attempt=result['id'],observed_active_bytes=usage(target)))
    print('Pinned Papis built with reviewed backend, exact source-built prerequisites and other wheel-only dependencies:',result['output'].strip())


if __name__=='__main__':asyncio.run(main())
