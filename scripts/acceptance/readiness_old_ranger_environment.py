"""Owned environment for the original native Ranger source launcher."""
import os

from readiness_evidence import RAW


def environment():
    target=RAW/'active/old-ranger'
    env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC',
        'SYSTEMDRIVE','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','LANG','LC_ALL'}}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
        ('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),('XDG_DATA_HOME','home/data')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env.update(TERM='screen-256color',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
        GIT_CEILING_DIRECTORIES=str(target),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    env['PATH']=str(target/'bin')+os.pathsep+env.get('PATH','')
    return env
