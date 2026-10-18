"""Install frozen production dependencies without hooks; run pinned tracked dist."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import tarfile
import uuid
import urllib.request

from adversarial_process import execute
from readiness_acquire_plop import extract_source
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256

PIN = '26f76d8dede565b2bf38d0b9e9f3009ee2c8f9ae'


def environment(target):
    env = {k: os.environ[k] for k in ['PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'LANG', 'LC_ALL'] if k in os.environ}
    for name, folder in [('HOME', 'home'), ('USERPROFILE', 'home'), ('APPDATA', 'home/appdata'),
                         ('LOCALAPPDATA', 'home/localappdata'), ('TEMP', 'tmp'), ('TMP', 'tmp'),
                         ('TMPDIR', 'tmp'), ('YARN_CACHE_FOLDER', 'yarn-cache'),
                         ('YARN_GLOBAL_FOLDER', 'yarn-global'), ('XDG_CACHE_HOME', 'home/cache'),
                         ('XDG_CONFIG_HOME', 'home/config'), ('npm_config_cache', 'npm-cache'),
                         ('npm_config_prefix', 'npm-prefix')]:
        path = target / folder
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    env.update(YARN_ENABLE_TELEMETRY='0', npm_config_update_notifier='false',
               npm_config_audit='false', npm_config_fund='false', NODE_NO_WARNINGS='1')
    return env


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    target = RAW / 'active/hygen'
    source = target / 'src'
    owner = json.loads((target / 'task-owned.json').read_text())
    if owner['workspace'] != str(ROOT) or owner['pin'] != PIN or owner['project'] != 'jondot/hygen':
        raise RuntimeError('unowned Hygen target')
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass/hygen'
    review = json.loads((docs / 'source-review.json').read_text())
    if any(sha256(source / name) != digest for name, digest in review['reviewed_inputs'].items()):
        raise RuntimeError('reviewed Hygen source changed')
    tooling = target / 'tooling'
    if args.resume:
        receipt=json.loads((tooling/'acquisition.json').read_text())
        archive=tooling/'yarn-1.22.22.tgz'
        if sha256(archive)!=receipt['archive_sha256']:raise RuntimeError('changed package-manager archive')
        with tarfile.open(archive,'r:gz') as bundle:
            for name in ['bin/yarn.js','lib/cli.js','LICENSE']:
                expected=bundle.extractfile('package/'+name).read(8*1024**2+1)
                if (tooling/'yarn'/name).read_bytes()!=expected:raise RuntimeError('changed package-manager executable')
    else:
        tooling.mkdir(exist_ok=False)
        request = urllib.request.Request('https://registry.npmjs.org/yarn/1.22.22', headers={'User-Agent': 'Playtestr-validation'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(1024**2 + 1)
        if len(raw) > 1024**2:
            raise RuntimeError('Yarn metadata bound')
        metadata = json.loads(raw)
        if metadata['name'] != 'yarn' or metadata['version'] != '1.22.22' or metadata['license'] != 'BSD-2-Clause':
            raise RuntimeError('unreviewed package-manager identity/license')
        url = metadata['dist']['tarball']
        if url != 'https://registry.npmjs.org/yarn/-/yarn-1.22.22.tgz':
            raise RuntimeError('unexpected package-manager origin')
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read(4*1024**2 + 1)
        if len(data) > 4*1024**2 or metadata['dist']['integrity'] != 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode():
            raise RuntimeError('package-manager integrity/size mismatch')
        archive = tooling / 'yarn-1.22.22.tgz'
        archive.write_bytes(data)
        extract_source(data, tooling / 'yarn', expanded_limit=16*1024**2, entry_limit=100, member_limit=8*1024**2)
        license_file = tooling / 'yarn/LICENSE'
        if 'Redistribution and use in source and binary forms' not in license_file.read_text():
            raise RuntimeError('package-manager license differs')
        immutable_json(tooling / 'acquisition.json', dict(version='1.22.22', url=url, integrity=metadata['dist']['integrity'],
                       archive_sha256=sha256(archive), license_sha256=sha256(license_file), install_hooks_executed=False))
    env = environment(target)
    node = Path(shutil.which('node', path=env['PATH'])).resolve()
    version = await execute([node, '--version'], 'hygen', 'reviewed-native-node-version', env=env, timeout=30, campaign=Campaign())
    if not re.fullmatch(r'v(?:22|24)\.\d+\.\d+',version['output'].strip()):
        raise RuntimeError('reviewed Node 22 or 24 native runtime required')
    runtime=dict(node=str(node),node_sha256=sha256(node),version=version['output'].strip(),version_attempt=version['id'],installed_globally=False)
    immutable_json(target/('runtime.json' if not (target/'runtime.json').exists() else 'runtime-resume-'+uuid.uuid4().hex+'.json'),runtime)
    lock=source/'yarn.lock';original_lock=lock.read_bytes()
    transport_lock=original_lock.replace(b'https://registry.yarnpkg.com/',b'https://registry.npmjs.org/')
    immutable_json(target/('transport-'+uuid.uuid4().hex+'.json'),dict(original_lock_sha256=hashlib.sha256(original_lock).hexdigest(),transport_lock_sha256=hashlib.sha256(transport_lock).hexdigest(),change='Only tarball origin maps Yarn registry to npm registry; versions, package paths and all integrity values unchanged. Original lock restored after command.'))
    lock.write_bytes(transport_lock)
    observations = []
    operation = asyncio.create_task(execute([node, tooling / 'yarn/bin/yarn.js', '--no-default-rc',
        'install', '--frozen-lockfile', '--production=true', '--ignore-scripts', '--no-bin-links', '--non-interactive',
        '--registry','https://registry.npmjs.org','--network-timeout','10000','--network-concurrency','4',
        '--cache-folder', target / 'yarn-cache'], 'hygen', 'frozen-production-install-no-hooks', cwd=source,
        env=env, timeout=300, campaign=Campaign()))
    try:
        while not operation.done():
            size = await asyncio.to_thread(usage, target)
            observations.append(size)
            if size > 512*1024**2:
                raise RuntimeError('declared active Hygen 512 MiB setup forecast exceeded')
            await asyncio.sleep(2)
        installed = await operation
    finally:
        lock.write_bytes(original_lock)
        if not operation.done():
            operation.cancel()
            try:
                await operation
            except asyncio.CancelledError:
                pass
        immutable_json(target / ('build-storage-'+uuid.uuid4().hex+'.json'), dict(observed_active_bytes=observations,
                       measurement='Periodic logical bytes, not exact peak or quota.'))
    # Stop upward config discovery at a reviewed owned file during direct checks.
    validation = target / 'validation'
    validation.mkdir()
    (validation / '.hygen.js').write_text('module.exports = {};\n', encoding='utf-8')
    help_result = await execute([node, source / 'dist/bin.js', '--help'], 'hygen', 'actual-pinned-cli-help',
                                cwd=validation, env=env, timeout=30, campaign=Campaign())
    if 'hygen [option] GENERATOR ACTION' not in help_result['output']:
        raise RuntimeError('actual pinned CLI help differs')
    launchers = target / 'bin'
    launchers.mkdir()
    (launchers / 'hygen.cmd').write_bytes(b'@echo off\r\nnode "%~dp0..\\src\\dist\\bin.js" %*\r\n')
    launcher = launchers / 'hygen'
    launcher.write_text('#!/bin/sh\nexec node "$(dirname "$0")/../src/dist/bin.js" "$@"\n', encoding='utf-8')
    if os.name != 'nt':
        launcher.chmod(0o755)
    packages = {}
    for package in (source / 'node_modules').rglob('package.json'):
        packages[package.relative_to(source).as_posix()] = sha256(package)
    immutable_json(target / 'dependencies.json', dict(installed_package_manifests=packages,
                   lock_sha256=sha256(source / 'yarn.lock'), scripts_disabled=True, production_only=True))
    immutable_json(target / 'build.json', dict(pin=PIN, version='6.2.11', executed_tree='dist',
                   tracked_upstream_dist=True, typescript_rebuilt=False, install_attempt=installed['id'],
                   help_attempt=help_result['id'], scripts_disabled=True, yarn_lock_sha256=sha256(source / 'yarn.lock'),
                   dependencies_sha256=sha256(target / 'dependencies.json'), observed_active_bytes=usage(target)))
    print('Pinned Hygen tracked dist ready with frozen production dependencies; no lifecycle hooks.')


if __name__ == '__main__':
    asyncio.run(main())
