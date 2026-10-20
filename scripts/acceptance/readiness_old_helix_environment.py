"""Confine new Rust prerequisites, caches, homes and build output to Helix ownership."""
import os

from readiness_evidence import RAW


def environment(project='helix'):
    if project not in {'helix','broot','yazi'}:raise RuntimeError('undeclared original Rust project')
    target=RAW/'active'/('old-'+project)
    env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC',
        'SYSTEMDRIVE','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','LANG','LC_ALL'}}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
        ('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),('XDG_DATA_HOME','home/data'),
        ('CARGO_HOME','cargo-home'),('RUSTUP_HOME','rustup-home'),('CARGO_TARGET_DIR','cargo-target')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env.update(RUSTUP_AUTO_INSTALL='0',RUSTUP_TOOLCHAIN=('1.99.0' if project=='yazi' else '1.97.1'),CARGO_BUILD_JOBS='2',CARGO_INCREMENTAL='0',
        CARGO_PROFILE_RELEASE_DEBUG='0',CARGO_PROFILE_RELEASE_LTO='false',CARGO_NET_RETRY='0',
        CARGO_HTTP_TIMEOUT='30',CARGO_HTTP_MULTIPLEXING='false',GIT_CEILING_DIRECTORIES=str(target),
        GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,RUSTUP_DIST_SERVER='https://static.rust-lang.org',
        RUSTUP_UPDATE_ROOT='https://static.rust-lang.org/rustup')
    if project=='helix':env.update(HELIX_DISABLE_AUTO_GRAMMAR_BUILD='1',HELIX_NIX_BUILD_REV='ba40e547426b0f9896c8bdc699a4ab11f2b37dbc')
    elif project=='broot':env.update(BR_INSTALL='no',TERM='screen-256color')
    else:
        env.update(TERM='screen-256color',YAZI_NO_GITCL='1',YAZI_BUILD_BOOTSTRAPPED='1',
            SOURCE_DATE_EPOCH='1791608923',CARGO_PROFILE_RELEASE_WINDOWS_DEBUG='0',CARGO_PROFILE_RELEASE_WINDOWS_LTO='false')
    env['PATH']=str(target/'bin')+os.pathsep+env.get('PATH','')
    return env
