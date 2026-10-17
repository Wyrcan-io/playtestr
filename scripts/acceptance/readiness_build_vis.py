"""Ordinary reviewed native C build; no installation or optional plugin libraries."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import platform
import re
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_vis_source import ARCHIVE_SHA256,PIN


def build_environment():
    host=platform.system()
    if host not in {'Linux','Darwin'}:raise RuntimeError('vis is declared only for native Linux/macOS; no Windows execution attempted')
    active=RAW/'active/vis'
    owner=json.loads((active/'task-owned.json').read_text())
    if owner!=dict(workspace=str(ROOT),campaign='runner-readiness-ten-project-pass',project='martanne/vis',pin=PIN):
        raise RuntimeError('unowned vis build root')
    if sha256(active/'source.tar.gz')!=ARCHIVE_SHA256:raise RuntimeError('reviewed source archive changed')
    for parent in [RAW,RAW/'active',active,active/'src']:
        if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():raise RuntimeError('linked vis build root')
    env={'PATH':os.environ['PATH'],'LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
    for name,folder in [('HOME','home'),('USERPROFILE','home'),('TMPDIR','tmp'),('TEMP','tmp'),('TMP','tmp'),
        ('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config'),('CLANG_MODULE_CACHE_PATH','cache/clang')]:
        path=active/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CEILING_DIRECTORIES=str(active),
        HOMEBREW_NO_AUTO_UPDATE='1',HOMEBREW_CACHE=str(active/'cache/brew'),CCACHE_DISABLE='1')
    prerequisite={}
    if host=='Darwin':
        developer=Path(os.environ.get('DEVELOPER_DIR','/Applications/Xcode.app/Contents/Developer')).resolve()
        compiler=developer/'Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
        sdk=developer/'Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk'
        if not compiler.is_file() or not sdk.is_dir():raise RuntimeError('read-only installed Xcode compiler/SDK unavailable')
        env.update(DEVELOPER_DIR=str(developer),SDKROOT=str(sdk.resolve()))
        settings=sdk/'SDKSettings.json'
        prerequisite=dict(developer_dir=str(developer),sdk=str(sdk.resolve()),
            sdk_settings_sha256=sha256(settings) if settings.is_file() else None)
    else:
        compiler=next((p for p in [Path('/usr/bin/gcc'),Path('/usr/bin/clang')] if p.is_file()),None)
        if compiler is None:raise RuntimeError('installed native C compiler missing; no global installation attempted')
    compiler=compiler.resolve();make=Path('/usr/bin/make')
    if not make.is_file():raise RuntimeError('installed make unavailable')
    env['CC']=str(compiler);env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    return active,compiler,make,env,prerequisite


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',default='initial')
    parser.add_argument('--version-exit-code',type=int,choices=range(256),default=0);args=parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',args.label):raise RuntimeError('invalid native build label')
    active,compiler,make,env,prerequisite=build_environment();source=active/'src'
    review=json.loads((ROOT/'docs/validation/runner-readiness-ten-project-pass/vis/source-review.json').read_text())
    if any(sha256(source/name)!=digest for name,digest in review['reviewed_build_inputs'].items()):
        raise RuntimeError('reviewed vis configure/Makefile changed')
    runtime=active/'runtime.json'
    if not runtime.exists():
        compiler_version=await execute([compiler,'--version'],'vis','installed-native-c-compiler-version',env=env,timeout=30,campaign=Campaign())
        make_version=await execute([make,'--version'],'vis','installed-native-make-version',env=env,timeout=30,campaign=Campaign())
        immutable_json(runtime,dict(compiler_path=str(compiler),compiler_sha256=sha256(compiler),make_path=str(make),make_sha256=sha256(make),
            compiler_version_attempt=compiler_version['id'],make_version_attempt=make_version['id'],
            native_os=platform.system(),native_arch=platform.machine(),installed_globally=False,prerequisites=prerequisite))
    configured=None
    if not (source/'config.mk').exists():
        configured=await execute(['/bin/sh','./configure','--prefix='+str(active/'install'),
            '--enable-curses','--disable-lua','--disable-lpeg-static','--disable-tre','--disable-acl','--disable-selinux'],
            'vis','reviewed-owned-configure',cwd=source,env=env,timeout=120,campaign=Campaign())
    build_args=[make,'-j2','VERSION=10b630af0940','API=0','vis']
    operation=asyncio.create_task(execute(build_args,'vis',args.label+'-ordinary-native-c-build',
        cwd=source,env=env,timeout=300,campaign=Campaign()))
    sizes=[]
    try:
        while not operation.done():
            observed=await asyncio.to_thread(usage,active);sizes.append(observed)
            if observed>192*1024**2:raise RuntimeError('vis build stopped below declared 256-MiB active forecast')
            await asyncio.sleep(2)
        built=await operation
    finally:
        if not operation.done():
            operation.cancel()
            try:await operation
            except asyncio.CancelledError:pass
    binary=source/'vis'
    version=await execute([binary,'-v'],'vis',args.label+'-built-native-vis-version',cwd=source,env=env,
        timeout=30,expected=args.version_exit_code,campaign=Campaign())
    if 'vis 10b630af0940 +curses' not in version['output']:raise RuntimeError('unexpected pinned/configured vis version')
    if any(flag in version['output'] for flag in ['+lua','+lpeg','+tre','+acl','+selinux']):raise RuntimeError('undeclared optional feature enabled')
    output=active/'build.json' if args.label=='initial' else active/'build-revisions'/(args.label+'-'+uuid.uuid4().hex+'.json')
    immutable_json(output,dict(pin=PIN,archive_sha256=ARCHIVE_SHA256,binary_relative_path='src/vis',binary_sha256=sha256(binary),
        configure_attempt=configured['id'] if configured else None,build_attempt=built['id'],version_attempt=version['id'],
        version=version['output'].strip(),version_exit_code=args.version_exit_code,compiler_sha256=sha256(compiler),
        make_sha256=sha256(make),config_mk_sha256=sha256(source/'config.mk'),config_h_sha256=sha256(source/'config.h'),
        license_sha256=sha256(source/'LICENSE'),active_bytes_observed=sizes,build_command=list(map(str,build_args)),
        features='curses; Lua/LPeg/TRE/ACL/SELinux disabled through upstream configure options; no install target'))
    print('Built pinned native vis with owned configuration/cache/temp and installed C prerequisites.')


if __name__=='__main__':asyncio.run(main())
