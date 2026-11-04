"""Run one bounded Git Town scenario through the public Playtestr CLI."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

from adversarial_process import execute
from next20_check import DOC, RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256


PROJECT = 'git-town'


def isolated_env(target):
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC',
                              'SYSTEMDRIVE', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PROGRAMW6432'}}
    home = target / 'home'
    temp = target / 'tmp'
    folders = {'HOME': home, 'USERPROFILE': home, 'APPDATA': home / 'appdata',
        'LOCALAPPDATA': home / 'localappdata', 'TEMP': temp, 'TMP': temp, 'TMPDIR': temp,
        'XDG_CONFIG_HOME': home / 'config', 'XDG_CACHE_HOME': home / 'cache',
        'XDG_DATA_HOME': home / 'data'}
    for key, path in folders.items():
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    global_config = home / 'empty.gitconfig'
    if not global_config.exists():
        global_config.write_bytes(b'')
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=str(global_config),
        GIT_TERMINAL_PROMPT='0', GIT_CEILING_DIRECTORIES=str(target),
        GOPROXY='off', GOSUMDB='off', GOTOOLCHAIN='local', GOWORK='off',
        CGO_ENABLED='0', GOCACHE=str(home / 'go-cache'), GOTMPDIR=str(temp))
    # Playtestr itself is the product under test. Reuse only the already
    # populated host module cache, read-only (GOPROXY=off); Go build output and
    # temporary files remain below this target's owned home/temp roots.
    cache = subprocess.run(['go', 'env', 'GOMODCACHE'], check=True, capture_output=True,
                           text=True, timeout=10).stdout.strip()
    if not Path(cache).is_dir():
        raise ValueError('pre-existing Go module cache for the Playtestr CLI is unavailable')
    env['GOMODCACHE'] = cache
    binary = target / 'bin' / ('git-town.exe' if os.name == 'nt' else 'git-town')
    if not binary.is_file() or binary.is_symlink():
        raise ValueError('exact reviewed Git Town executable is missing or linked')
    env['PATH'] = str(binary.parent) + os.pathsep + env.get('PATH', '')
    return env, binary


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--expected-runner-exit', type=int, default=0)
    parser.add_argument('spec')
    args = parser.parse_args()
    target = RAW / 'active' / PROJECT
    spec = (ROOT / args.spec).resolve(strict=True)
    spec.relative_to(ROOT)
    data = json.loads(spec.read_text(encoding='utf-8'))
    if data.get('version') != 3 or data.get('command', [None])[0] != 'git-town':
        raise ValueError('case must use public spec v3 and the installed Git Town PATH command')
    fixture = (spec.parent / data['workspace']['fixture']).resolve(strict=True)
    fixture.relative_to(spec.parent.resolve(strict=True))
    manifest_path = target / 'fixture-source.json'
    manifest = json.loads(manifest_path.read_text())
    files = {}
    total = 0
    for path in sorted(fixture.rglob('*')):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('linked Git Town case fixture')
        if path.is_file():
            payload = path.read_bytes()
            total += len(payload)
            files[path.relative_to(fixture).as_posix()] = {
                'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
    if files != manifest['files'] or total != manifest['total_bytes']:
        raise ValueError('Git Town source fixture changed before scenario execution')
    env, binary = isolated_env(target)
    case_id = uuid.uuid4().hex
    report_root = target / 'case-evidence' / case_id
    report_root.mkdir(parents=True, exist_ok=False)
    report = report_root / 'report.json'
    artifacts = report_root / 'runner-evidence'
    argv = [shutil.which('go') or 'go', 'run', '-mod=readonly', './cmd/playtestr', 'test',
            '--artifacts-dir', str(artifacts), '--report', str(report), str(spec)]
    started = dict(schema_version=1, project=PROJECT, label=args.label,
        spec=str(spec.relative_to(ROOT)), spec_sha256=sha256(spec),
        fixture_manifest_sha256=sha256(manifest_path),
        executable_sha256=sha256(binary), command=list(map(str, argv)),
        host=os.name, expected_runner_exit=args.expected_runner_exit,
        environment_policy='isolated HOME/APPDATA/XDG/Git config; no system/global Git config, forge credentials, or remote')
    immutable_json(report_root / 'started.json', started)
    result = None
    error = None
    try:
        result = await execute(argv, PROJECT, 'playtestr-git-town-' + args.label,
            cwd=ROOT, env=env, timeout=300, expected=args.expected_runner_exit,
            campaign=NextCampaign(phase='development'), output_cap=2 * 1024 * 1024)
    except Exception as exc:
        error = dict(type=type(exc).__name__, message=str(exc)[:2048],
            attempt_id=getattr(exc, 'evidence_id', None),
            evidence_directory=str(getattr(exc, 'evidence_directory', '')))
    report_data = json.loads(report.read_text(encoding='utf-8')) if report.is_file() else None
    outcome = dict(started, status='completed' if result else 'failed', error=error,
        runner_attempt_id=result['id'] if result else (error or {}).get('attempt_id'),
        report_sha256=sha256(report) if report.is_file() else None,
        report=report_data, console=result['output'] if result else None)
    immutable_json(report_root / 'finished.json', outcome)
    if not result:
        summary = report_data.get('summary') if isinstance(report_data, dict) else None
        results = report_data.get('results', []) if isinstance(report_data, dict) else []
        failed_results = [dict(name=item.get('name'), status=item.get('status'),
            failure=item.get('failure'), target=item.get('target'), steps=item.get('steps'))
            for item in results if item.get('status') != 'passed']
        evidence_output = ''
        evidence_directory = Path((error or {}).get('evidence_directory', ''))
        console_path = evidence_directory / 'console.log'
        if console_path.is_file():
            evidence_output = console_path.read_bytes()[-4096:].decode('utf-8', 'replace')
        print('Git Town case failure detail:', json.dumps(dict(
            label=args.label, error=error, runner_attempt_id=outcome['runner_attempt_id'],
            report_summary=summary, report_sha256=outcome['report_sha256'],
            report_failures=failed_results,
            console_tail=evidence_output[-4096:]),
            ensure_ascii=True), flush=True)
        raise RuntimeError('Git Town Playtestr case failed; inspect ' +
                           str((report_root / 'finished.json').relative_to(ROOT)))
    print('Git Town case', args.label, 'runner exit', result['returncode'],
          'report', sha256(report))


if __name__ == '__main__':
    asyncio.run(main())
