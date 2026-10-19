"""Build the original pinned Cookiecutter with wheel-only owned prerequisites."""
import argparse
import asyncio
import json
import os
import sys
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def environment():
    target=RAW/'active/old-cookiecutter'
    env={k:os.environ[k] for k in ['PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','LANG','LC_ALL'] if k in os.environ}
    for key,name in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),('LOCALAPPDATA','home/localappdata'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),('XDG_DATA_HOME','home/data'),
        ('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('PIP_CACHE_DIR','pip-cache')]:
        path=target/name;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
    env.update(PIP_CONFIG_FILE=os.devnull,PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONDONTWRITEBYTECODE='1',
        PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    env['PATH']=str(target/'venv'/('Scripts' if os.name=='nt' else 'bin'))+os.pathsep+env.get('PATH','')
    return env


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    target=RAW/'active/old-cookiecutter';source=target/'src'
    review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/cookiecutter/source-review.json')
    owner=load(target/'task-owned.json')
    if owner['workspace']!=str(ROOT) or owner['pin']!=review['pin'] or owner['project']!=review['repository']:
        raise RuntimeError('unowned original Cookiecutter source')
    for name,digest in review['reviewed_inputs'].items():
        if sha256(source/name)!=digest:raise RuntimeError('original source changed before build')
    original=ROOT/'docs/validation/ten-new-project-adversarial-pass/cookiecutter/dependency-constraints.txt'
    if sha256(original)!=review['dependency_constraints_sha256']:raise RuntimeError('original constraints changed')
    env=environment()
    async def run(label,argv,timeout=300):
        operation=asyncio.create_task(execute(argv,'old-cookiecutter',label,cwd=source,env=env,timeout=timeout,campaign=Campaign()))
        sizes=[]
        try:
            while not operation.done():
                size=await asyncio.to_thread(usage,target);sizes.append(size)
                if size>768*1024**2:raise RuntimeError('owned Python target exceeds 768-MiB forecast')
                await asyncio.sleep(2)
            return await operation
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
            immutable_json(target/(label+'-'+uuid.uuid4().hex+'-storage.json'),dict(observed_bytes=sizes,scope='Periodic logical bytes, not an exact peak.'))
    venv=target/'venv';python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if args.resume:
        if not python.is_file() or (target/'build.json').exists():raise RuntimeError('resume requires unfinished owned venv')
    else:
        if venv.exists():raise RuntimeError('refuse existing venv without explicit retained failure resume')
        await run('migration-owned-venv',[sys.executable,'-B','-I','-m','venv','--copies',venv],120)
    requirements=target/'runtime-requirements.txt'
    expected=original.read_text(encoding='utf-8-sig').replace('\r\n','\n').rstrip('\n')+'\n'+'\n'.join(review['packaging_prerequisites'])+'\n'
    if requirements.exists():
        if requirements.read_text(encoding='utf-8')!=expected:raise RuntimeError('resumed requirements changed')
    else:requirements.write_text(expected,encoding='utf-8',newline='\n')
    wheels=target/'wheels';wheels.mkdir(exist_ok=args.resume)
    await run('migration-pinned-wheel-download',[python,'-B','-m','pip','download','--index-url','https://pypi.org/simple',
        '--only-binary=:all:','--no-deps','--dest',wheels,'-r',requirements])
    identities={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in wheels.iterdir() if p.is_file()}
    if (target/'wheels.json').exists():
        if load(target/'wheels.json')!=identities:raise RuntimeError('resumed wheel payloads changed')
    else:immutable_json(target/'wheels.json',identities)
    await run('migration-offline-pinned-wheels',[python,'-B','-m','pip','install','--no-index','--find-links',wheels,
        '--only-binary=:all:','--no-deps','-r',requirements])
    await run('migration-reviewed-source-editable-install',[python,'-B','-m','pip','install','--no-index','--no-deps',
        '--no-build-isolation','--editable',source])
    probe=await run('migration-actual-source-module',[python,'-B','-c',
        'import cookiecutter,json,sys; print(json.dumps(dict(version=cookiecutter.__version__,module=cookiecutter.__file__,prefix=sys.prefix)))'],30)
    actual=json.loads(probe['output'])
    if actual['version']!='2.7.1' or os.path.normcase(actual['module'])!=os.path.normcase(str(source/'cookiecutter/__init__.py')):
        raise RuntimeError('installed runtime does not execute the reviewed source')
    launcher=python.parent/('cookiecutter.exe' if os.name=='nt' else 'cookiecutter')
    version=await run('migration-original-cli-version',[launcher,'--version'],30)
    if 'Cookiecutter 2.7.1' not in version['output']:raise RuntimeError('actual CLI version differs')
    freeze=await run('migration-installed-freeze',[python,'-B','-m','pip','freeze'],30)
    for name,digest in review['reviewed_inputs'].items():
        if sha256(source/name)!=digest:raise RuntimeError('editable build changed original source bytes')
    generated={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*')
        if p.is_file() and p.relative_to(source).as_posix() not in review['reviewed_inputs']}
    immutable_json(target/'runtime.json',dict(python=str(python),python_sha256=sha256(python),source_pin=review['pin'],
        module=actual['module'],version=actual['version'],module_probe_attempt=probe['id']))
    immutable_json(target/'build.json',dict(pin=review['pin'],source_review_sha256=sha256(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/cookiecutter/source-review.json'),
        source_editable=True,version='2.7.1',launcher_relative_path=launcher.relative_to(target).as_posix(),launcher_sha256=sha256(launcher),
        dependency_wheels=identities,generated_source_inputs=generated,version_attempt=version['id'],dependency_freeze_attempt=freeze['id'],
        observed_active_bytes=usage(target),scope='Owned original Cookiecutter plus pinned wheel-only runtime/build prerequisites; no global installation.'))
    print('Original pinned Cookiecutter installed and source identity verified in owned venv; no migration scenario credit yet.')


if __name__=='__main__':asyncio.run(main())
