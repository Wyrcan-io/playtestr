"""Owned native homes and build temporary paths for original nnn."""
import os

from readiness_evidence import RAW


def environment():
    target=RAW/'active/old-nnn'
    env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','LANG','LC_ALL'}}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),('XDG_DATA_HOME','home/data')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env['PATH']=str(target/'bin')+os.pathsep+env.get('PATH','');env['TERM']='screen-256color'
    return env
