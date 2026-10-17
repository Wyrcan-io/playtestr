"""Explicit owned build paths and read-only installed Rust toolchain selection."""
import os
from pathlib import Path
import platform

from readiness_evidence import RAW,ROOT


def build_environment():
    import json
    active=RAW/'active/edit'
    owner=json.loads((active/'task-owned.json').read_text())
    if owner!=dict(workspace=str(ROOT),campaign='runner-readiness-ten-project-pass',project='microsoft/edit',
        pin='cb6de0a8966aecd01d19a3541dab1829d0e679ca'):raise RuntimeError('unowned editor build root')
    for path in [RAW,RAW/'active',active]:
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise RuntimeError('linked editor build root')
    if platform.machine().lower() not in {'amd64','x86_64'}:raise RuntimeError('undeclared editor build architecture')
    triple='x86_64-pc-windows-msvc' if os.name=='nt' else 'x86_64-unknown-linux-gnu'
    roots=[Path.home()/'.rustup']
    if os.environ.get('RUSTUP_HOME'):roots.insert(0,Path(os.environ['RUSTUP_HOME']))
    extension='.exe' if os.name=='nt' else ''
    installed=next((p/'toolchains'/('stable-'+triple)/'bin' for p in roots
        if (p/'toolchains'/('stable-'+triple)/'bin'/('rustc'+extension)).is_file()),None)
    if not installed:raise RuntimeError('installed stable native Rust toolchain missing; no global update attempted')
    env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC',
        'SYSTEMDRIVE','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','LANG','LC_ALL'}}
    for name,folder in [('CARGO_HOME','cargo-home'),('CARGO_TARGET_DIR','target'),('RUSTUP_HOME','rustup-home'),
        ('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),('LOCALAPPDATA','home/localappdata'),
        ('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config')]:
        path=active/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env.update(RUSTC=str(installed/('rustc'+extension)),RUSTDOC=str(installed/('rustdoc'+extension)),
        RUSTUP_AUTO_INSTALL='0',CARGO_NET_RETRY='0',CARGO_HTTP_TIMEOUT='30',CARGO_HTTP_MULTIPLEXING='false',
        CARGO_INCREMENTAL='0')
    env['PATH']=str(installed)+os.pathsep+env.get('PATH','')
    return active,installed/('cargo'+extension),triple,env
