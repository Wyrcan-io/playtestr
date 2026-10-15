"""Reviewed ordinary nnn Makefile build using owned source, output and temporary files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from adversarial_process import ROOT,DOC,run
from adversarial_owned_source import claim
from adversarial_fixture_directories import prepare


def build(app,project):
    if project!='nnn' or os.name=='nt':raise RuntimeError('The reviewed C target requires Unix')
    path=app/'runtime.json';identity=json.loads(path.read_text(encoding='utf-8'))
    compiler=shutil.which('cc');make=shutil.which('make')
    if not compiler or not make:raise RuntimeError('Existing native C compiler and make are required')
    temp=app/'tmp';temp.mkdir(exist_ok=True)
    env=dict(os.environ,CC=compiler,TMPDIR=str(temp))
    version=run([compiler,'--version'],project,'native-c-compiler-version',env=env,timeout=15)['output']
    make_version=run([make,'--version'],project,'native-make-version',env=env,timeout=15)['output']
    # Force the normal all target each time. Its prepatch/postpatch hooks are
    # no-ops with upstream default patch flags; installation, signing/upload,
    # static/musl and icon-generator targets are never selected.
    run([make,'-B','all'],project,'target-c-build',cwd=app/'source',env=env,timeout=180)
    built=app/'source/nnn';binary=app/'bin/nnn';binary.parent.mkdir(exist_ok=True)
    shutil.copyfile(built,binary);binary.chmod(0o755)
    dependency_inspector=shutil.which('otool' if platform.system()=='Darwin' else 'ldd')
    if not dependency_inspector:raise RuntimeError('Native C shared-library inspector is missing')
    dependencies=run([dependency_inspector,*(['-L'] if platform.system()=='Darwin' else []),binary],
                     project,'native-c-shared-library-identities',env=env,timeout=15)['output']
    identity.update(binary=str(binary),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                    toolchain='C compiler: '+version.splitlines()[0],compiler_version=version,
                    compiler_sha256=hashlib.sha256(Path(compiler).resolve(strict=True).read_bytes()).hexdigest(),
                    native_shared_libraries=dependencies,
                    make_version=make_version,build_recipe='make -B all; upstream default O_NORL=1, locale retained')
    path.write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
    return identity


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True,choices=['nnn'])
    parser.add_argument('--native-source',action='store_true')
    parser.add_argument('--rebuild',action='store_true')
    args=parser.parse_args();project=args.project
    if os.name=='nt':raise RuntimeError('The reviewed nnn matrix is Unix only')
    candidate=next(c for c in json.loads((DOC/'candidates.json').read_text(encoding='utf-8'))
                   if c['repo'].split('/')[-1]==project and c['disposition']=='selected')
    local=ROOT/'.cache/ten-new-project-apps'
    app=claim(Path('/var/tmp') if args.native_source else local,project,candidate['sha'],
              other_roots=[local,Path('/var/tmp')],prefix='playtestr-adversarial-' if args.native_source else '')
    source=app/'source'
    if not source.exists():
        run(['git','clone','--filter=blob:none','--no-checkout',candidate['url']+'.git',source],
            project,'source-acquisition',timeout=180)
        run(['git','-C',source,'checkout','--detach',candidate['sha']],project,'pinned-checkout',timeout=180)
    if subprocess.check_output(['git','-C',source,'rev-parse','HEAD'],text=True,timeout=15).strip()!=candidate['sha']:
        raise RuntimeError('C source revision differs from reviewed pin')
    if not args.rebuild and subprocess.check_output(['git','-C',source,'status','--porcelain','--untracked-files=no'],
                                                   text=True,timeout=15).strip():
        raise RuntimeError('Pristine C setup cannot adopt mutated source')
    package=DOC/project;package.mkdir(parents=True,exist_ok=True);prepare(package)
    for name,retained in [('LICENSE','UPSTREAM-LICENSE.txt'),('Makefile','target-Makefile.txt')]:
        data=subprocess.check_output(['git','-C',source,'show',candidate['sha']+':'+name],timeout=15)
        if len(data)>4*1024*1024:raise RuntimeError('Pinned build metadata bound')
        (package/retained).write_bytes(data)
    identity_path=app/'runtime.json'
    if not identity_path.exists():
        identity_path.write_text(json.dumps(dict(source=candidate['sha'],native_host=platform.platform(),
            app=str(app),source_path=str(source),path=str(app/'bin'),editable=False),indent=2)+'\n',encoding='utf-8')
    # nnn uses native wide-character curses. Keep the public test's ordinary
    # operational locale inheritance identical for recorder and replay instead
    # of embedding a Linux locale name in a portable spec.
    locale=shutil.which('locale')
    if not locale:raise RuntimeError('Existing native locale utility is required')
    character_map=run([locale,'charmap'],project,'native-character-map-prerequisite',timeout=60)['output'].strip()
    if character_map.replace('-','').replace('_','').upper()!='UTF8':
        raise RuntimeError('Reviewed Unicode journeys require an existing operational UTF-8 locale')
    identity=json.loads(identity_path.read_text(encoding='utf-8'))
    identity['native_locale_charmap']=character_map
    identity_path.write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(build(app,project),indent=2))


if __name__=='__main__':main()
