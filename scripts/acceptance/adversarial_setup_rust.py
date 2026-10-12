"""Pinned Rust targets with explicit build hooks and exclusively owned caches."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from adversarial_process import ROOT, DOC, run
from adversarial_fixture_directories import prepare

TOOLCHAIN='1.97.1'
TARGETS={'helix':('helix-term','hx'),'broot':('broot','broot'),'yazi':('yazi-fm','yazi')}


def build(app,project,*,clean_package=False):
    identity=json.loads((app/'runtime.json').read_text(encoding='utf-8'))
    source=app/'source'
    env=dict(os.environ)
    for name,folder in [('CARGO_HOME','cargo-home'),('RUSTUP_HOME','rustup-home'),
                        ('CARGO_TARGET_DIR','cargo-target'),('TMPDIR','rust-tmp')]:
        path=app/folder;path.mkdir(exist_ok=True);env[name]=str(path)
    env.update(RUSTUP_TOOLCHAIN=TOOLCHAIN,CARGO_BUILD_JOBS='2',CARGO_INCREMENTAL='0',
               CARGO_PROFILE_RELEASE_DEBUG='0',CARGO_PROFILE_RELEASE_LTO='false',
               RUSTUP_DIST_SERVER='https://static.rust-lang.org',
               RUSTUP_UPDATE_ROOT='https://static.rust-lang.org/rustup')
    if os.name=='nt':env.update(TEMP=str(app/'rust-tmp'),TMP=str(app/'rust-tmp'))
    # The admitted Helix scope is deterministic plain-text editing. The pinned
    # upstream build hook explicitly supports disabling grammar acquisition.
    # No downloaded grammar repository, LSP or syntax compatibility is claimed.
    if project=='helix':env['HELIX_DISABLE_AUTO_GRAMMAR_BUILD']='1'
    rustup=os.environ.get('PLAYTESTR_RUSTUP') or shutil.which('rustup')
    if not rustup:raise RuntimeError('Rustup prerequisite missing; install the official bootstrap in an owned runtime first')
    installed=app/'rustup-home/toolchains'
    if not installed.is_dir() or not any(installed.glob(TOOLCHAIN+'-*')):
        run([rustup,'toolchain','install',TOOLCHAIN,'--profile','minimal','--no-self-update'],project,
            'owned-exact-rust-toolchain',env=env,timeout=600)
    tool=[rustup,'run',TOOLCHAIN]
    # A private CARGO_HOME intentionally has no user/global rustc proxy. Cargo
    # otherwise finds an unrelated system rustc through PATH, even though
    # `rustup run ... rustc --version` selected the correct compiler directly.
    compiler=Path(run([rustup,'which','--toolchain',TOOLCHAIN,'rustc'],project,
        'resolve-owned-rust-compiler',env=env)['output'].strip()).resolve(strict=True)
    compiler.relative_to((app/'rustup-home/toolchains').resolve(strict=True))
    env['RUSTC']=str(compiler)
    env['RUSTDOC']=str(compiler.with_name('rustdoc.exe' if os.name=='nt' else 'rustdoc'))
    version=run([*tool,'rustc','--version'],project,'actual-rust-compiler',env=env)['output'].strip()
    if not version.startswith('rustc '+TOOLCHAIN+' '):raise RuntimeError('Actual Rust compiler differs from selected exact version')
    package,binary_name=TARGETS[project]
    if clean_package:
        # Cargo can otherwise reuse a mutated binary when exact restoration
        # also restores the original older source mtime.
        run([*tool,'cargo','clean','-p',package],project,'invalidate-mutated-package-artifacts',
            env=env,cwd=source,timeout=90)
    cargo_action='rustc' if os.name=='nt' else 'build'
    command=[*tool,'cargo',cargo_action,'--locked','--release','-p',package,'--bin',binary_name]
    if os.name=='nt':
        # MSVC otherwise embeds the current wall-clock timestamp in the PE
        # header, preventing exact pristine-binary restoration evidence.
        command+=['--','-C','link-arg=/Brepro']
    run(command,
        project,'target-build',env=env,cwd=source,timeout=1200)
    suffix='.exe' if os.name=='nt' else ''
    built=app/'cargo-target/release'/(binary_name+suffix)
    executable=app/'bin'/(binary_name+suffix)
    executable.parent.mkdir(exist_ok=True)
    shutil.copyfile(built,executable)
    if os.name!='nt':executable.chmod(0o755)
    if project=='helix':
        runtime=app/'bin/runtime'
        if not runtime.exists():
            # The ordinary upstream runtime lookup includes this sibling path.
            # Copy only the pinned ordinary resources, never external grammars.
            shutil.copytree(source/'runtime',runtime,ignore=shutil.ignore_patterns('grammars'))
    identity.update(toolchain=version,requested_toolchain=TOOLCHAIN,binary=str(executable),
        compiler_path=str(compiler),
        binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
        build_profile='locked release; two jobs; no LTO/debug/incremental artifacts',
        reproducible_windows_link=os.name=='nt',
        helix_grammar_scope='disabled upstream auto-grammar build; plain text only' if project=='helix' else None)
    (app/'runtime.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
    return identity


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True,choices=TARGETS)
    parser.add_argument('--native-source',action='store_true')
    parser.add_argument('--rebuild',action='store_true')
    args=parser.parse_args();project=args.project
    candidate=next(c for c in json.loads((DOC/'candidates.json').read_text(encoding='utf-8'))
        if c['repo'].split('/')[-1]==project and c['disposition']=='selected')
    root=ROOT/'.cache/ten-new-project-apps'
    root.mkdir(parents=True,exist_ok=True)
    app=Path('/var/tmp')/('playtestr-adversarial-'+project) if args.native_source else root/project
    if not args.rebuild:
        markers=list(root.glob('*/task-owned.json'))
        if os.name!='nt':markers+=list(Path('/var/tmp').glob('playtestr-adversarial-*/task-owned.json'))
        for marker in markers:
            if json.loads(marker.read_text(encoding='utf-8'))['project']!=project:
                raise RuntimeError('Another owned application is still active')
    if app.is_symlink() or getattr(app,'is_junction',lambda:False)():raise RuntimeError('Linked application root')
    app.mkdir(parents=True,exist_ok=True)
    owner=dict(campaign='ten-new-project-adversarial-pass',workspace=str(ROOT),project=project,source_sha=candidate['sha'])
    marker=app/'task-owned.json'
    if marker.exists():
        if json.loads(marker.read_text(encoding='utf-8'))!=owner:raise RuntimeError('Unknown existing ownership')
    elif any(app.iterdir()):raise RuntimeError('Refuse adopting an unmarked nonempty application directory')
    marker.write_text(json.dumps(owner)+'\n',encoding='utf-8')
    source=app/'source'
    if not source.exists():
        run(['git','clone','--filter=blob:none','--no-checkout',candidate['url']+'.git',source],project,'source-acquisition',timeout=180)
        run(['git','-C',source,'checkout','--detach',candidate['sha']],project,'pinned-checkout',timeout=180)
    if subprocess.check_output(['git','-C',source,'rev-parse','HEAD'],text=True,timeout=15).strip()!=candidate['sha']:
        raise RuntimeError('Wrong pinned source')
    if not args.rebuild and subprocess.check_output(['git','-C',source,'status','--porcelain','--untracked-files=no'],text=True,timeout=15).strip():
        raise RuntimeError('Pristine setup cannot adopt modified source')
    package=DOC/project;package.mkdir(parents=True,exist_ok=True)
    if (package/'scenarios.json').exists():prepare(package)
    license_path=next((p for p in [source/'LICENSE',source/'LICENSE.md',source/'LICENSE.txt'] if p.is_file()),None)
    if license_path is None:raise RuntimeError('Missing reviewed upstream license')
    for name,output in [(license_path.name,'UPSTREAM-LICENSE.txt'),('Cargo.toml','target-Cargo.toml.txt'),('Cargo.lock','target-Cargo.lock.txt')]:
        blob=subprocess.check_output(['git','-C',source,'show',candidate['sha']+':'+name],timeout=15)
        if len(blob)>4*1024*1024:raise RuntimeError('Retained pinned metadata size bound')
        (package/output).write_bytes(blob)
    identity_path=app/'runtime.json'
    if not identity_path.exists():identity_path.write_text(json.dumps(dict(source=candidate['sha'],
        native_host=platform.platform(),app=str(app),source_path=str(source),path=str(app/'bin'),editable=False),indent=2)+'\n',encoding='utf-8')
    identity=build(app,project,clean_package=args.rebuild)
    if os.environ.get('GITHUB_PATH'):
        with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as output:output.write(str(app/'bin')+'\n')
    print(json.dumps(identity,indent=2))


if __name__=='__main__':main()
