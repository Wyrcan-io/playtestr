"""Install pinned Plop workspace dependencies with scripts disabled and owned caches."""
import asyncio
import json
import os
import uuid
from pathlib import Path

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


def usage(root):
    total=0
    for directory,subdirs,files in os.walk(root,followlinks=False):
        subdirs[:]=[name for name in subdirs if not Path(directory,name).is_symlink()
                    and not getattr(Path(directory,name),'is_junction',lambda:False)()]
        for name in files:
            path=Path(directory,name)
            try:
                if not path.is_symlink():total+=path.stat().st_size
            except FileNotFoundError:pass
    return total


async def main():
    target=RAW/'active/plop'
    marker=json.loads((target/'task-owned.json').read_text())
    if marker['workspace']!=str(ROOT) or marker['project']!='plopjs/plop':raise RuntimeError('unowned active target')
    source=target/'src'
    if 'The MIT License' not in (source/'LICENSE.md').read_text():raise RuntimeError('unreviewed license')
    env={name:os.environ[name] for name in ['PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','LANG','LC_ALL'] if name in os.environ}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
                        ('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),
                        ('YARN_CACHE_FOLDER','yarn-cache'),('YARN_GLOBAL_FOLDER','yarn-global'),
                        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env.update(YARN_ENABLE_SCRIPTS='false',YARN_ENABLE_TELEMETRY='false',PYTHONIOENCODING='utf-8')
    observations=[]
    observation_path=target/('build-storage-'+uuid.uuid4().hex+'.json')
    operation=asyncio.create_task(execute(['node',source/'.yarn/releases/yarn-4.9.4.cjs','install','--immutable','--mode=skip-build'],
        'plop','pinned-yarn-install-no-build-hooks',cwd=source,env=env,timeout=1200,campaign=Campaign()))
    try:
        while not operation.done():
            size=await asyncio.to_thread(usage,target)
            observations.append(dict(active_bytes=size))
            if size>3*1024**3:raise RuntimeError('active operation stopped before 4 GiB bound')
            await asyncio.sleep(2)
        result=await operation
    finally:
        if not operation.done():
            operation.cancel()
            try:await operation
            except asyncio.CancelledError:pass
        immutable_json(observation_path,dict(observations=observations,measurement='periodic observed bytes; not exact peak or quota'))
    # Ordinary relocatable Node CLI launchers, without faking target behavior.
    launchers=target/'bin';launchers.mkdir(exist_ok=True)
    (launchers/'plop.cmd').write_bytes(b'@echo off\r\nnode "%~dp0..\\src\\packages\\plop\\bin\\plop.js" %*\r\n')
    script=launchers/'plop'
    script.write_text('#!/bin/sh\nexec node "$(dirname "$0")/../src/packages/plop/bin/plop.js" "$@"\n',encoding='utf-8')
    if os.name!='nt':script.chmod(0o755)
    immutable_json(target/'build.json',dict(pin=marker['pin'],attempt=result['id'],
        yarn_lock_sha256=sha256(source/'yarn.lock'),license_sha256=sha256(source/'LICENSE.md'),
        yarn_sha256=sha256(source/'.yarn/releases/yarn-4.9.4.cjs'),scripts_disabled=True,
        runtime=json.loads((target/'runtime.json').read_text()),observed_active_bytes=usage(target)))
    print('Plop dependencies installed with scripts disabled:',result['id'])


if __name__=='__main__':asyncio.run(main())
