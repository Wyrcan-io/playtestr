"""Run one reviewed project spec under bounded campaign evidence capture."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_rust_fetch import environment
from readiness_evidence import immutable_json, sha256


def isolated_env(project):
    target = RAW / 'active' / project
    env = environment(target)
    env['GOPROXY'] = 'off'
    env['GOTOOLCHAIN'] = 'local'
    env['GOWORK'] = 'off'
    env['GOCACHE'] = str(target / 'home' / 'go-cache')
    shared_modcache = os.environ.get('GOMODCACHE')
    if not shared_modcache:
        go = shutil.which('go')
        if not go:
            raise ValueError('installed Go prerequisite is unavailable')
        import subprocess
        result = subprocess.run([go, 'env', 'GOMODCACHE'], check=True, capture_output=True,
                                text=True, timeout=10)
        shared_modcache = result.stdout.strip()
    if not Path(shared_modcache).is_dir():
        raise ValueError('read-only existing Go module cache is unavailable')
    env['GOMODCACHE'] = shared_modcache
    return env


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--expected-runner-exit', type=int, default=0)
    parser.add_argument('spec')
    args = parser.parse_args()
    project = args.project
    target = RAW / 'active' / project
    spec = (ROOT / args.spec).resolve(strict=True)
    spec.relative_to(ROOT)
    spec_data = json.loads(spec.read_text(encoding='utf-8'))
    fixture = (spec.parent / spec_data['workspace']['fixture']).resolve(strict=True)
    fixture.relative_to(spec.parent.resolve())
    fixture_files = {}
    fixture_total = 0
    for path in sorted(fixture.rglob('*')):
        if path.is_symlink():
            raise ValueError('linked Skim case fixture is refused')
        if path.is_file():
            fixture_total += path.stat().st_size
            if path.stat().st_size > 64*1024 or fixture_total > 128*1024:
                raise ValueError('Skim case fixture size bound')
            fixture_files[path.relative_to(fixture).as_posix()] = sha256(path)
    adapter_hash = None
    if len(spec_data['command']) > 1 and Path(spec_data['command'][0]).name.lower() == 'python' and spec_data['command'][1] == 'skim_stdin_adapter.py':
        adapter_hash = sha256(ROOT / 'scripts/acceptance/skim_stdin_adapter.py')
        if fixture_files.get('skim_stdin_adapter.py') != adapter_hash:
            raise ValueError('case-owned stdin adapter differs from the reviewed source')
    elif Path(spec_data['command'][0]).name.lower() not in {'sk', 'sk.exe'}:
        raise ValueError('case must launch the exact pinned Skim binary or reviewed stdin adapter')
    case_id = uuid.uuid4().hex
    report_root = target / 'case-evidence' / case_id
    report_root.mkdir(parents=True)
    report = report_root / 'report.json'
    runner_evidence = report_root / 'runner-evidence'
    argv = [shutil.which('go') or 'go', 'run', '-mod=readonly', './cmd/playtestr', 'test',
            '--artifacts-dir', str(runner_evidence), '--report', str(report)]
    if args.update:
        argv.append('--update')
    argv.append(str(spec))
    record = dict(schema_version=1, case_attempt_id=case_id, project=project, label=args.label,
                  spec=str(spec.relative_to(ROOT)), spec_sha256=sha256(spec),
                  executable_sha256=json.loads((target/'build.json').read_text())['binary_sha256'],
                  adapter_sha256=adapter_hash, fixture_files=fixture_files,
                  host=os.name, expected_runner_exit=args.expected_runner_exit,
                  command=list(map(str, argv)), report_path=str(report.relative_to(ROOT)))
    immutable_json(report_root / 'started.json', record)
    result = None
    error = None
    try:
        env = isolated_env(project)
        env['SKIM_TEST_BINARY'] = str((target/'bin'/'sk.exe').resolve(strict=True))
        result = await execute(argv, project, 'playtestr-case-' + args.label,
            cwd=ROOT, env=env, timeout=240,
            expected=args.expected_runner_exit, campaign=NextCampaign(), output_cap=2*1024*1024)
    except Exception as exc:
        error = dict(type=type(exc).__name__, message=str(exc)[:2048],
                     attempt_id=getattr(exc, 'evidence_id', None),
                     evidence_directory=str(getattr(exc, 'evidence_directory', '')))
    report_row = json.loads(report.read_text(encoding='utf-8')) if report.is_file() else None
    outcome = dict(record, status='completed' if result else 'failed',
                   error=error, runner_attempt_id=result['id'] if result else (error or {}).get('attempt_id'),
                   report_sha256=sha256(report) if report.is_file() else None,
                   report=report_row, console=result['output'] if result else None)
    immutable_json(report_root / 'finished.json', outcome)
    if not result:
        raise RuntimeError('Playtestr case failed; see ' + str((report_root/'finished.json').relative_to(ROOT)))
    print('Case', args.label, 'runner exit', result['returncode'], 'report', sha256(report))


if __name__ == '__main__':
    asyncio.run(main())
