"""Build the pinned real Rclone CLI using an owned SDK and dependency/cache roots."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256

PIN = 'd369079a1448c487d09d85bfe11382e16ea4e345'


def environment(target):
    env = {k: os.environ[k] for k in ['PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'LANG', 'LC_ALL'] if k in os.environ}
    for name, folder in [('HOME', 'home'), ('USERPROFILE', 'home'), ('APPDATA', 'home/appdata'),
                         ('LOCALAPPDATA', 'home/localappdata'), ('XDG_CONFIG_HOME', 'home/config'),
                         ('XDG_CACHE_HOME', 'home/cache'), ('TEMP', 'tmp'), ('TMP', 'tmp'), ('TMPDIR', 'tmp'),
                         ('GOTMPDIR', 'tmp'), ('GOCACHE', 'go-cache'), ('GOPATH', 'gopath'),
                         ('GOMODCACHE', 'gopath/pkg/mod')]:
        path = target / folder
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    env.update(GOTOOLCHAIN='local', GOWORK='off', CGO_ENABLED='0', GOMAXPROCS='2', GOMEMLIMIT='2GiB',
               GOENV=str(target / 'home/go-env'), GOTELEMETRY='off', GODEBUG='http2client=0',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=str(target / 'home/gitconfig'),
               GOPROXY='https://proxy.golang.org', GOSUMDB='sum.golang.org', GOAMD64='v1')
    return env


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    target = RAW / 'active/rclone'
    source = target / 'src'
    owner = json.loads((target / 'task-owned.json').read_text())
    if owner['workspace'] != str(ROOT) or owner['pin'] != PIN or owner['project'] != 'rclone/rclone':
        raise RuntimeError('unowned pinned Rclone target')
    prior_failures = []
    if args.resume:
        for path in (RAW/'events').glob('*-finished.json'):
            row = json.loads(path.read_text())
            if (row['project'] == 'rclone' and row['label'] == 'reviewed-native-full-cli-build'
                    and row['category'] != 'passed'):
                prior_failures.append(row['id'])
        if (not prior_failures or not (target/'toolchain/sdk.json').is_file()
                or any((target/name).exists() for name in ['build.json','runtime.json'])):
            raise RuntimeError('resume requires preserved failed build and no successful build receipts')
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass/rclone'
    review = json.loads((docs / 'source-review.json').read_text(encoding='utf-8-sig'))
    for name, digest in review['reviewed_inputs'].items():
        if sha256(source / name) != digest:
            raise RuntimeError('reviewed Rclone input changed')
    env = environment(target)
    sdk = target / 'toolchain/sdk.json'
    if not sdk.exists():
        await execute([sys.executable, 'scripts/acceptance/readiness_bootstrap_rclone_go.py'],
                      'rclone', 'official-owned-go127-sdk', env=env, timeout=300, campaign=Campaign())
    descriptor = json.loads(sdk.read_text())
    if descriptor['version'] != 'go1.27.0':
        raise RuntimeError('wrong target SDK')
    go = target / 'toolchain/go/bin' / ('go.exe' if os.name == 'nt' else 'go')
    settings = await execute([go, 'env', '-json', 'GOOS', 'GOARCH', 'GOVERSION', 'CGO_ENABLED', 'GOAMD64'],
                            'rclone', 'owned-native-go-settings', cwd=source, env=env, timeout=30, campaign=Campaign())
    native = json.loads(settings['output'])
    host = {'Linux': 'linux', 'Darwin': 'darwin', 'Windows': 'windows'}[platform.system()]
    arch = {'x86_64': 'amd64', 'amd64': 'amd64', 'arm64': 'arm64', 'aarch64': 'arm64'}[platform.machine().lower()]
    if native['GOOS'] != host or native['GOARCH'] != arch or native['GOVERSION'] != 'go1.27.0' or native['CGO_ENABLED'] != '0':
        raise RuntimeError('target would not use declared native pure-Go build')
    binary = target / 'bin' / ('rclone.exe' if os.name == 'nt' else 'rclone')
    binary.parent.mkdir(exist_ok=args.resume)
    if binary.exists():raise RuntimeError('refuse to replace an existing target binary')
    observations = []
    monitor_started = time.monotonic()
    last_notice = -60
    operation = asyncio.create_task(execute([go, 'build', '-p', '2', '-mod=readonly', '-trimpath', '-buildvcs=false',
        '-ldflags', '-s -w', '-o', binary, '.'], 'rclone', 'reviewed-native-full-cli-build',
        cwd=source, env=env, timeout=780, campaign=Campaign()))
    try:
        while not operation.done():
            size = await asyncio.to_thread(usage, target)
            observations.append(size)
            elapsed = time.monotonic()-monitor_started
            if elapsed-last_notice >= 60:
                print('Rclone build monitor:', round(elapsed), 'seconds;', size, 'active logical bytes', flush=True)
                last_notice = elapsed
            if size > 3840*1024**2:
                raise RuntimeError('stop before declared four-GiB active target limit')
            await asyncio.sleep(2)
        build = await operation
    finally:
        if not operation.done():
            operation.cancel()
            try:
                await operation
            except asyncio.CancelledError:
                pass
        immutable_json(target / ('build-storage-' + uuid.uuid4().hex + '.json'),
                       dict(observed_active_bytes=observations, measurement='Periodic logical bytes, not an exact peak or OS quota.'))
    for name, digest in review['reviewed_inputs'].items():
        if sha256(source / name) != digest:
            raise RuntimeError('target build changed reviewed source/lock')
    validation = target / 'validation'
    validation.mkdir()
    version = await execute([binary, '--config', str(validation / 'unused.conf'), 'version'],
                            'rclone', 'actual-pinned-cli-version', cwd=validation, env=env,
                            timeout=30, campaign=Campaign())
    if not version['output'].splitlines()[0].strip() == 'rclone v1.76.0-DEV':
        raise RuntimeError('actual source version differs')
    immutable_json(target / 'runtime.json', dict(go=str(go), compiler_sha256=sha256(go), sdk_sha256=sha256(sdk),
                   native_settings=native, version_attempt=version['id'], installed_globally=False))
    immutable_json(target / 'build.json', dict(pin=PIN, version='v1.76.0-DEV', binary_relative_path=binary.relative_to(target).as_posix(),
                   binary_sha256=sha256(binary), source_review_sha256=sha256(docs / 'source-review.json'),
                   go_mod_sha256=sha256(source / 'go.mod'), go_sum_sha256=sha256(source / 'go.sum'),
                   sdk_sha256=sha256(sdk), compiler_sha256=sha256(go), native_settings=native,
                   build_attempt=build['id'], settings_attempt=settings['id'], version_attempt=version['id'],
                   resumed_after_failed_attempts=sorted(prior_failures),
                   build_flags=['-p=2', '-mod=readonly', '-trimpath', '-buildvcs=false', '-ldflags=-s -w'],
                   cgo_enabled=False, target_hooks_executed=False, observed_active_bytes=usage(target)))
    print('Pinned native Rclone full CLI built; config wizard only, no cloud/network/mount qualification.')


if __name__ == '__main__':
    asyncio.run(main())
