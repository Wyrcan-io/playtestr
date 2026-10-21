"""Acquire one pinned target; use installed Linux Ruby or owned Windows Ruby."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target-only',action='store_true');args=parser.parse_args()
    candidate=ROOT/'.playtestr-bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    if not args.target_only:
        binary=RAW/'bin'/candidate.name;binary.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(candidate,binary)
        if os.name!='nt':binary.chmod(0o755)
        immutable_json(RAW/'rubygems-native-runner.json',dict(source_revision=os.environ.get('SOURCE_REVISION','e7b5f29e575e44babe7fdaa2e83e55b62d318305'),
            candidate_sha256=sha256(candidate),copied_sha256=sha256(binary)))
    if os.name!='nt':
        immutable_json(RAW/'rubygems-runtime-baseline.json',await runtime_inventory('rubygems','runtime-baseline-before-acquisition'))
    await execute([sys.executable,'scripts/acceptance/readiness_acquire_rubygems.py'],
        'rubygems','native-pinned-acquisition',timeout=180,campaign=Campaign())
    active=RAW/'active/rubygems'
    reviewed=json.loads((ROOT/'docs/validation/runner-readiness-ten-project-pass/rubygems/source-review.json').read_text())
    if sha256(active/'source.tar.gz')!=reviewed['archive_sha256'] or sha256(active/'src/MIT.txt')!=reviewed['license_sha256']:
        raise RuntimeError('native acquisition differs from the canonical reviewed pinned source/license')
    if os.name=='nt':
        await execute([sys.executable,'scripts/acceptance/readiness_bootstrap_ruby.py'],
            'rubygems','native-owned-ruby-runtime',timeout=360,campaign=Campaign())
        runtime=json.loads((active/'runtime.json').read_text());ruby=active/runtime['ruby_relative_path']
    else:
        located=shutil.which('ruby')
        if not located:raise RuntimeError('installed supported native Ruby missing; no global installation authorized')
        ruby=Path(located).resolve()
        env={k:v for k,v in os.environ.items() if k in ['PATH','LANG','LC_ALL','TMPDIR']}
        for key,folder in [('HOME','home'),('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config')]:
            path=active/folder;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
        env.update(RUBYLIB=str(active/'src/lib'),GEMRC=os.devnull,GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
        version=await execute([ruby,'-e','abort "Ruby >=3.2 required" if Gem::Version.new(RUBY_VERSION) < Gem::Version.new("3.2"); puts RUBY_DESCRIPTION; puts Gem::Platform.local'],
            'rubygems','native-installed-ruby-runtime',env=env,timeout=30,campaign=Campaign())
        lines=version['output'].splitlines()
        if len(lines)!=2:raise RuntimeError('unexpected native Ruby prerequisite result')
        built=await execute([ruby,active/'src/exe/bundle','--version'],'rubygems','native-pinned-bundler-version',
            env=env,timeout=30,campaign=Campaign())
        if '4.1.0.beta2' not in built['output']:raise RuntimeError('wrong pinned Bundler loaded')
        runtime=dict(installed_ruby_executable=str(ruby),ruby_sha256=sha256(ruby),ruby_version=lines[0],
            native_platform=lines[1],runtime_version_attempt=version['id'],installed_globally=False,
            prerequisite='read/execute preinstalled native Ruby and its installed standard library; no new global files')
        immutable_json(active/'runtime.json',runtime)
        owner=json.loads((active/'task-owned.json').read_text())
        immutable_json(active/'build.json',dict(pin=owner['pin'],source_runtime_interpreted=True,
            bundled_cli_version=built['output'].strip(),version_attempt=built['id'],license_sha256=sha256(active/'src/MIT.txt'),
            runtime_sha256=sha256(active/'runtime.json'),build_hooks_executed=False,dependency_installation=False))
    from readiness_rubygems_profiles import main as profiles
    profiles()
    for key in ['GITHUB_PATH','GITHUB_ENV']:
        if not os.environ.get(key):raise RuntimeError('native prepare requires owned workflow environment files')
    with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as output:
        output.write(str(ruby.parent)+'\n'+str(active/'src/exe')+'\n')
    with Path(os.environ['GITHUB_ENV']).open('a',encoding='utf-8') as output:
        output.write('RUBYLIB='+str(active/'src/lib')+'\n')
    print('Pinned Bundler native runtime and twenty-case profile prepared.')


if __name__=='__main__':asyncio.run(main())
