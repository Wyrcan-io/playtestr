"""Build reviewed pinned Frogmouth with wheel-only prerequisites in an owned venv."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import sys
import tomllib
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    target=RAW/'active/frogmouth';source=target/'src'
    marker=json.loads((target/'task-owned.json').read_text())
    if marker['workspace']!=str(ROOT) or marker['project']!='Textualize/frogmouth':raise RuntimeError('unowned source')
    metadata=tomllib.loads((source/'pyproject.toml').read_text(encoding='utf-8'))
    if metadata['build-system']!={'requires':['poetry-core'],'build-backend':'poetry.core.masonry.api'} or metadata['tool']['poetry']['version']!='0.9.2':raise RuntimeError('unreviewed source backend/version')
    env={k:os.environ[k] for k in ['PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','LANG','LC_ALL'] if k in os.environ}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),('XDG_DATA_HOME','home/data'),('PIP_CACHE_DIR','pip-cache')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env.update(PIP_CONFIG_FILE=os.devnull,PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    async def run(argv,label):
        task=asyncio.create_task(execute(argv,'frogmouth',label,cwd=source,env=env,timeout=1200,campaign=Campaign()))
        observations=[]
        try:
            while not task.done():
                size=await asyncio.to_thread(usage,target);observations.append(size)
                if size>512*1024**2:raise RuntimeError('active target storage ceiling')
                await asyncio.sleep(2)
            return await task
        finally:
            if not task.done():
                task.cancel()
                try:await task
                except asyncio.CancelledError:pass
            immutable_json(target/(label+'-'+uuid.uuid4().hex+'-storage.json'),dict(observed_bytes=observations,measurement='periodic, not an exact peak or quota'))
    python=target/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    requirements=target/'runtime-requirements.txt'
    wheels=target/'wheels'
    if not args.resume:
        await run([sys.executable,'-m','venv','--copies',target/'venv'],'owned-runtime-venv')
        requirements.write_text('textual==0.53.1\ntyping-extensions>=4.5,<5\nhttpx>=0.24.1,<0.25\nxdg>=6,<7\npoetry-core>=1,<3\n',encoding='utf-8')
        wheels.mkdir()
        await run([python,'-m','pip','download','--only-binary=:all:','--dest',wheels,'-r',requirements],'reviewed-wheel-only-download')
    elif (target/'build.json').exists() or not python.is_file():raise RuntimeError('resume requires unfinished owned installation')
    identities={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in wheels.iterdir()}
    if args.resume:
        if json.loads((target/'wheels.json').read_text())!=identities:raise RuntimeError('resumed wheels differ from original receipt')
    else:
        immutable_json(target/'wheels.json',identities)
        await run([python,'-m','pip','install','--no-index','--find-links',wheels,'--only-binary=:all:','-r',requirements],'offline-runtime-wheel-install')
        await run([python,'-m','pip','install','--no-index','--no-deps','--no-build-isolation','--editable',source],'reviewed-source-editable-build')
    version=await run([python,'-m','frogmouth','--version'],'built-version')
    if version['output'].strip()!='frogmouth 0.9.1 (Textual v0.53.1)':raise RuntimeError('built target version differs from pinned __init__.py')
    launcher=python.parent/('frogmouth.exe' if os.name=='nt' else 'frogmouth')
    immutable_json(target/'runtime.json',dict(python=str(python),python_version=sys.version,python_sha256=sha256(python),source_pin=marker['pin']))
    immutable_json(target/'build.json',dict(pin=marker['pin'],license_sha256=sha256(source/'LICENSE'),source_editable=True,build_backend=metadata['build-system'],dependency_wheels=identities,wheel_manifest='wheels.json',launcher_relative_path=launcher.relative_to(target).as_posix(),launcher_sha256=sha256(launcher),version_attempt=version['id'],observed_active_bytes=usage(target),package_metadata_version='0.9.2',source_banner_version='0.9.1'))
    print('Owned pinned Frogmouth build:',version['output'].strip())


if __name__=='__main__':asyncio.run(main())
