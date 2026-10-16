"""Build pinned Poetry in an owned venv, using wheel-only runtime dependencies."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tomllib

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    target=RAW/'active/poetry'
    marker=json.loads((target/'task-owned.json').read_text())
    if marker['workspace']!=str(ROOT) or marker['project']!='python-poetry/poetry':
        raise RuntimeError('unowned Poetry tree')
    source=target/'src'
    license=(source/'LICENSE').read_text(encoding='utf-8')
    if 'Permission is hereby granted, free of charge' not in license:
        raise RuntimeError('unreviewed Poetry license')
    metadata=tomllib.loads((source/'pyproject.toml').read_text(encoding='utf-8'))
    env={k:os.environ[k] for k in ['PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','LANG','LC_ALL'] if k in os.environ}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
        ('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),('PIP_CACHE_DIR','pip-cache')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env.update(PIP_CONFIG_FILE=os.devnull,PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONDONTWRITEBYTECODE='1',
               PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    async def run(argv,label):
        task=asyncio.create_task(execute(argv,'poetry',label,cwd=source,env=env,timeout=1200,campaign=Campaign()))
        observations=[]
        try:
            while not task.done():
                size=await asyncio.to_thread(usage,target)
                observations.append(size)
                if size>3*1024**3:raise RuntimeError('stop before active target storage ceiling')
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
    await run([sys.executable,'-m','venv',venv],'owned-runtime-venv')
    python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    requirements=target/'runtime-requirements.txt'
    requirements.write_text('\n'.join(metadata['project']['dependencies'])+'\n',encoding='utf-8')
    wheels=target/'wheels';wheels.mkdir()
    await run([python,'-m','pip','download','--only-binary=:all:','--dest',wheels,'-r',requirements],
              'reviewed-runtime-wheel-download')
    wheel_identity={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in wheels.iterdir()}
    immutable_json(target/'wheels.json',wheel_identity)
    await run([python,'-m','pip','install','--no-index','--find-links',wheels,'--only-binary=:all:',
               '-r',requirements],'offline-runtime-wheel-install')
    await run([python,'-m','pip','install','--no-index','--no-deps','--no-build-isolation','--editable',source],
              'reviewed-source-editable-build')
    result=await run([python,'-m','poetry','--no-plugins','--version'],'built-version')
    if metadata['project']['version'] not in result['output']:raise RuntimeError('built Poetry version mismatch')
    immutable_json(target/'runtime.json',dict(python=str(python),python_version=sys.version,
        python_sha256=sha256(python),source_pin=marker['pin']))
    immutable_json(target/'build.json',dict(pin=marker['pin'],license_sha256=sha256(source/'LICENSE'),
        source_editable=True,build_backend=metadata['build-system'],dependency_wheels=wheel_identity,
        version_attempt=result['id'],observed_active_bytes=usage(target)))
    print('Pinned Poetry built using reviewed backend and wheel-only dependencies:',result['output'].strip())


if __name__=='__main__':asyncio.run(main())
