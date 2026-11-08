"""Prepare and execute Skim's frozen twelve-batch exact-archive series."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import uuid

from next20_check import RAW, ROOT
from next20_candidate import executable
from next20_jrnl_final import segmented_steps
from readiness_evidence import immutable_json, sha256


PROJECT = 'skim'
PIN = '1ab47f6ba7f1bfc355273bbdd98d4b2056ef95a3'
CASES = [f'N{i:02d}' for i in range(1, 9)] + [f'E{i:02d}' for i in range(1, 13)]
RELATIVE_TARGETS = {
    0: 'final-series-copies-v12/cold-warm-a/sk.exe',
    1: 'final-series-copies-v12/cold-warm-a/sk.exe',
    2: 'final-series-copies-v12/cold-warm-b/sk.exe',
    3: 'final-series-copies-v12/cold-warm-b/sk.exe',
    4: 'bin/sk.exe',
    5: 'final-series-copies-v12/relocated café 雪/sk.exe',
    6: 'bin/sk.exe',
    7: 'bin/sk.exe',
    8: 'bin/sk.exe',
    9: 'bin/sk.exe',
    10: 'bin/sk.exe',
    11: 'bin/sk.exe',
}
BATCHES = [
    {'id': 0, 'name': 'ordinary-cold-1', 'change': 'First logical use of fresh SHA-256-verified owned target copy A.'},
    {'id': 1, 'name': 'ordinary-warm-1', 'change': 'Reuse exact target copy A from batch 0; no OS cache eviction claim.'},
    {'id': 2, 'name': 'ordinary-cold-2', 'change': 'First logical use of independent fresh SHA-256-verified owned target copy B.'},
    {'id': 3, 'name': 'ordinary-warm-2', 'change': 'Reuse exact target copy B from batch 2; no OS cache eviction claim.'},
    {'id': 4, 'name': 'viewport', 'change': 'Increase width by 10 and height by 2 on N01-N07, E01-E02, E07-E12; preserve N08 exact wrapping snapshot and explicit parser, small-screen, and resize boundaries.'},
    {'id': 5, 'name': 'spaced-unicode-path', 'change': 'Run exact target copy B from an owned path containing spaces and café 雪; no contract assertions retuned.'},
    {'id': 6, 'name': 'ordinary-input-readiness', 'change': 'Frozen supported input and positive checkpoints unchanged.'},
    {'id': 7, 'name': 'segmented-printable-input', 'change': 'Split printable text writes longer than three Unicode code points into bounded ordered chunks.'},
    {'id': 8, 'name': 'bounded-contention-1', 'change': 'One owned 2-second 8-MiB SHA-256 worker per invocation.'},
    {'id': 9, 'name': 'bounded-contention-2', 'change': 'A second independent bounded 2-second 8-MiB SHA-256 worker window.'},
    {'id': 10, 'name': 'highest-risk-small-completion', 'change': 'N01 height reduced to 12; other frozen risk boundaries remain unchanged.'},
    {'id': 11, 'name': 'highest-risk-startup-boundary', 'change': 'Set positive-output startup deadline to 2000 ms; exact-first-exit parser cases retain startup gate 0.'},
]


def declared_harness_sha256(path):
    """Hash declared text harnesses independent of Windows checkout newlines."""
    data = path.read_bytes()
    if path.suffix.lower() in {'.py', '.ps1', '.yml', '.yaml'}:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def host_name():
    value = platform.system()
    if value == 'Windows':
        return 'windows'
    if value == 'Linux':
        return 'linux'
    raise ValueError('Skim final series is declared only for native Linux and Windows')


def require_plain(path):
    path.resolve(strict=True).relative_to(RAW.resolve(strict=True))
    cursor = path
    while cursor != RAW:
        if cursor.is_symlink() or getattr(cursor, 'is_junction', lambda: False)():
            raise ValueError('linked target/contract path is refused: ' + str(cursor))
        cursor = cursor.parent


def scenario_rows(package):
    base_path = package / 'scenario-declaration-v5.json'
    revision_path = package / 'scenario-declaration-v6.json'
    base = json.loads(base_path.read_text(encoding='utf-8'))
    revision = json.loads(revision_path.read_text(encoding='utf-8'))
    if (revision.get('base_declaration') != base_path.name or
            revision.get('base_sha256') != sha256(base_path) or
            base.get('pin') != PIN or revision.get('scenario_count') != 20):
        raise ValueError('Skim source scenarios are not the reviewed frozen declaration')
    rows = {row['id']: row for row in base['scenarios']}
    rows.update({row['id']: row for row in revision.get('replacements', [])})
    if set(rows) != set(CASES):
        raise ValueError('Skim declaration is not exactly eight normal and twelve edge cases')
    return base_path, revision_path, rows


def checked_target(target, binary, digest):
    resolved = binary.resolve(strict=True)
    require_plain(resolved)
    if resolved.stat().st_size > 128 * 1024 * 1024 or sha256(resolved) != digest:
        raise ValueError('prepared Skim target copy differs from exact build SHA-256')
    return resolved


def transform_contract(batch_id, case_id, original):
    value = copy.deepcopy(original)
    if batch_id == 4 and case_id not in {'N08', 'E03', 'E04', 'E05', 'E06'}:
        value['width'] += 10
        value['height'] += 2
    if batch_id == 7:
        value['steps'] = segmented_steps(value['steps'])
    if batch_id == 10 and case_id == 'N01':
        value['height'] = 12
    if batch_id == 11 and case_id not in {'E03', 'E04'}:
        value['startup_timeout_ms'] = 2000
    return value


def prepare(host):
    if host not in {'linux', 'windows'} or host != host_name():
        raise ValueError('preparation must run on the declared native host')
    package = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass/skim'
    declaration_path = package / 'final-series-declaration-native-exit-v32.json'
    declaration = json.loads(declaration_path.read_text(encoding='utf-8'))
    base_path, revision_path, rows = scenario_rows(package)
    candidate = executable('native-exit-v1', host)
    candidate_record = json.loads((candidate.parent / 'installed.json').read_text(encoding='utf-8'))
    target_root = RAW / 'active' / 'skim'
    build_path = target_root / 'build.json'
    build = json.loads(build_path.read_text(encoding='utf-8'))
    source = json.loads((package / 'source-provenance.json').read_text(encoding='utf-8'))
    if build.get('pin') != PIN or source.get('pin') != PIN:
        raise ValueError('Skim build/source pin mismatch')
    original_binary = checked_target(target_root, target_root / 'bin/sk.exe', build['binary_sha256'])
    if (declaration.get('candidate_freeze_sha256') != sha256(
            ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass/replacement-candidate-freeze-native-exit-v1.json') or
            declaration.get('scenario_base_sha256') != sha256(base_path) or
            declaration.get('scenario_revision_sha256') != sha256(revision_path) or
            declaration.get('candidate_provider_runs') != {'linux': '40424475362', 'windows': '40425810038'} or
            declaration.get('hosts') != ['linux', 'windows'] or declaration.get('batches') != BATCHES or
            declaration.get('ordinary_required_per_host') != 240 or
            declaration.get('calibration_required_per_host') != 9):
        raise ValueError('frozen Skim final declaration changed or is incomplete')
    if declaration.get('fault_declaration_sha256') != sha256(package / 'fault-declaration-final-v1.json'):
        raise ValueError('Skim final fault declaration changed')
    for name, digest in declaration.get('harness_files', {}).items():
        if declared_harness_sha256(ROOT/name) != digest:
            raise ValueError('Skim final harness changed after declaration: '+name)

    copy_root = target_root / 'final-series-copies-v12'
    first = copy_root / 'cold-warm-a'
    second = copy_root / 'cold-warm-b'
    if copy_root.exists():
        if copy_root.is_symlink() or getattr(copy_root, 'is_junction', lambda: False)():
            raise ValueError('linked Skim target-copy root')
        expected = {'cold-warm-a', 'cold-warm-a/sk.exe', 'cold-warm-b', 'cold-warm-b/sk.exe'}
        actual = {path.relative_to(copy_root).as_posix() for path in copy_root.rglob('*')}
        if actual != expected or any(path.is_symlink() or getattr(path, 'is_junction', lambda: False)()
                                     for path in copy_root.rglob('*')):
            raise ValueError('existing Skim target-copy root is not the exact two-file layout')
        for path in (first / 'sk.exe', second / 'sk.exe'):
            if sha256(path) != build['binary_sha256']:
                raise ValueError('existing Skim target copy differs from exact native build SHA-256')
    else:
        first.mkdir(parents=True)
        second.mkdir(parents=True)
        shutil.copy2(original_binary, first / 'sk.exe')
        shutil.copy2(original_binary, second / 'sk.exe')
    if host == 'linux':
        source_mode = original_binary.stat().st_mode
        for copied in (first / 'sk.exe', second / 'sk.exe'):
            copied.chmod((copied.stat().st_mode & 0o777) | (source_mode & 0o111))
            if not copied.stat().st_mode & 0o111:
                raise ValueError('Linux Skim target copy is missing executable permission')
    copy_hashes = {name: sha256(path / 'sk.exe') for name, path in [('a', first), ('b', second)]}
    if any(digest != build['binary_sha256'] for digest in copy_hashes.values()):
        raise ValueError('fresh target preparation copy is not byte-identical')

    contract_root = RAW / 'skim' / 'final-contracts' / 'native-exit-v26' / host
    if contract_root.exists():
        raise ValueError('refuse existing Skim final contract root')
    contract_root.mkdir(parents=True)
    planned = []
    for batch in BATCHES:
        batch_id = batch['id']
        folder = contract_root / f"batch-{batch_id:02d}"
        (folder / 'fixtures').mkdir(parents=True)
        (folder / 'snapshots').mkdir()
        target_binary = target_root / RELATIVE_TARGETS[batch_id]
        if batch_id != 5:
            checked_target(target_root, target_binary, build['binary_sha256'])
        cases = []
        for case_id in CASES:
            row = rows[case_id]
            canonical = package / row['contract']
            if sha256(canonical) != row['contract_sha256']:
                raise ValueError('canonical Skim case changed: ' + case_id)
            value = json.loads(canonical.read_text(encoding='utf-8'))
            original_fixture = (canonical.parent / value['workspace']['fixture']).resolve(strict=True)
            if original_fixture.is_symlink() or not original_fixture.is_dir():
                raise ValueError('linked or missing frozen Skim fixture')
            fixture_name = f"fixtures/{case_id}"
            shutil.copytree(original_fixture, folder / fixture_name)
            for path in (folder / fixture_name).rglob('*'):
                if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
                    raise ValueError('copied Skim fixture unexpectedly contains a link')
            value['workspace']['fixture'] = fixture_name
            command = list(value['command'])
            if Path(command[0]).name.lower() in {'sk.exe', 'sk'}:
                command[0] = str(target_binary.resolve())
            value['command'] = command
            value = transform_contract(batch_id, case_id, value)

            snapshots = []
            for step in value['steps']:
                snapshot = step.get('snapshot')
                if snapshot and snapshot not in snapshots:
                    snapshots.append(snapshot)
            for snapshot in snapshots:
                source_snapshot = package / 'snapshots' / snapshot
                if not source_snapshot.is_file() or source_snapshot.is_symlink():
                    raise ValueError('missing or linked frozen Skim snapshot: ' + snapshot)
                shutil.copyfile(source_snapshot, folder / 'snapshots' / snapshot)
            spec_path = folder / f'{case_id}.json'
            immutable_json(spec_path, value)
            cases.append(dict(case=case_id, canonical_contract=row['contract'],
                canonical_sha256=row['contract_sha256'], contract=spec_path.relative_to(ROOT).as_posix(),
                contract_sha256=sha256(spec_path), target_binary=target_binary.relative_to(ROOT).as_posix(),
                target_binary_sha256=build['binary_sha256'], contention=batch_id in {8, 9}))
        planned.append(dict(batch=batch, cases=cases))

    plan_path = RAW / 'skim' / 'final-series-plan-native-exit-v26' / host / 'plan.json'
    immutable_json(plan_path, dict(schema_version=1, project=PROJECT, host=host, source_pin=PIN,
        candidate_series='native-exit-v1', candidate_sha256=sha256(candidate),
        candidate_archive_sha256=candidate_record['archive_sha256'], candidate_run=declaration['candidate_provider_runs'][host],
        declaration_sha256=sha256(declaration_path), scenario_base_sha256=sha256(base_path),
        scenario_revision_sha256=sha256(revision_path), build_sha256=sha256(build_path),
        target_sha256=build['binary_sha256'], copy_sha256=copy_hashes,
        batches=planned, expected_ordinary=240, expected_calibrations=9,
        scope='Prepared plan only; no case executed. Fresh logical copies do not imply OS cache eviction.'))
    print('Prepared frozen Skim exact-candidate plan:', plan_path.relative_to(ROOT),
          '240 contracts; zero cases executed.')
    return plan_path


def relocate_warm_copy(target_root):
    source = target_root / 'final-series-copies-v12/cold-warm-b'
    destination = target_root / 'final-series-copies-v12/relocated café 雪'
    if destination.exists() or source.is_symlink() or getattr(source, 'is_junction', lambda: False)():
        raise ValueError('Skim Unicode relocation target exists or source is linked')
    source.rename(destination)
    expected = json.loads((target_root / 'build.json').read_text(encoding='utf-8'))['binary_sha256']
    if sha256(destination / 'sk.exe') != expected:
        raise ValueError('relocated target copy changed')
    return destination


def run(host, plan_path):
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    if plan.get('host') != host or plan.get('source_pin') != PIN or len(plan.get('batches', [])) != 12:
        raise ValueError('Skim plan host/pin/batch mismatch')
    target_root = RAW / 'active' / 'skim'
    output_root = RAW / 'skim' / 'final-series-native-exit-v1' / host
    if output_root.exists():
        raise ValueError('refuse existing Skim final-series output window')
    output_root.mkdir(parents=True)
    receipts = []
    for item in plan['batches']:
        batch = item['batch']
        if batch['id'] == 5:
            relocate_warm_copy(target_root)
        rows = []
        for case in item['cases']:
            label = f"skim-final-{host}-b{batch['id']:02d}-{case['case']}"
            command = [sys.executable, '-B', 'scripts/acceptance/next20_playtestr_case.py',
                '--project', 'skim', '--label', label, '--candidate-series', 'native-exit-v1',
                '--target-binary', case['target_binary']]
            if case['contention']:
                command.append('--contention')
            command.extend(['--', case['contract']])
            result = subprocess.run(command, cwd=ROOT, check=False, timeout=360,
                capture_output=True, text=True, encoding='utf-8', errors='replace', env=os.environ.copy())
            evidence = RAW / 'active/skim/case-evidence'
            matches = []
            for path in evidence.glob('*/finished.json'):
                record = json.loads(path.read_text(encoding='utf-8'))
                if record.get('label') == label:
                    matches.append((path, record))
            if len(matches) != 1:
                row = dict(case=case['case'], label=label, process_exit=result.returncode,
                    status='missing-or-duplicate-finished-event', stdout=result.stdout[-8192:],
                    stderr=result.stderr[-8192:], candidate_sha256=plan['candidate_sha256'])
            else:
                path, finished = matches[0]
                report = finished.get('report') or {}
                result_row = (report.get('results') or [{}])[0]
                failure = result_row.get('failure') or {}
                row = dict(case=case['case'], label=label, process_exit=result.returncode,
                    status=finished.get('status'), finished_path=path.relative_to(ROOT).as_posix(),
                    finished_sha256=sha256(path), report_sha256=finished.get('report_sha256'),
                    candidate_series=finished.get('runner_candidate_series'),
                    candidate_sha256=finished.get('runner_candidate_sha256'),
                    target_sha256=finished.get('target_binary_sha256'),
                    target_exit=(result_row.get('target') or {}).get('exit_code'),
                    step_statuses=[step.get('status') for step in result_row.get('steps', [])],
                    failure_category=failure.get('category'), failure_message=failure.get('message'),
                    workspace_cleaned=(result_row.get('workspace') or {}).get('cleaned'),
                    cleanup_confirmed=(result_row.get('cleanup') or {}).get('confirmed_exited'),
                    stdout=result.stdout[-8192:], stderr=result.stderr[-8192:])
            rows.append(row)
            print(json.dumps({key: row.get(key) for key in ('case','status','failure_category','workspace_cleaned')}, ensure_ascii=True), flush=True)
        passed = sum(r.get('status') == 'completed' and r.get('process_exit') == 0 and
                     r.get('workspace_cleaned') is True and r.get('cleanup_confirmed') is True and
                     r.get('candidate_sha256') == plan['candidate_sha256'] and
                     all(s == 'passed' for s in r.get('step_statuses', [])) for r in rows)
        batch_path = output_root / f"batch-{batch['id']:02d}.json"
        receipt = dict(schema_version=1, project=PROJECT, host=host, batch=batch,
            plan_sha256=sha256(plan_path), candidate_sha256=plan['candidate_sha256'],
            expected_cases=20, completed=len(rows), passing=passed, failed=len(rows)-passed,
            outcomes=rows)
        immutable_json(batch_path, receipt)
        receipts.append(batch_path)
        if len(rows) != 20 or passed != 20:
            raise RuntimeError('Skim final batch failed; preserved receipt: ' + str(batch_path.relative_to(ROOT)))
        print('Completed Skim batch', batch['id'] + 1, 'of 12;', host, flush=True)
    summary = output_root / 'summary.json'
    immutable_json(summary, dict(schema_version=1, project=PROJECT, host=host,
        plan_sha256=sha256(plan_path), candidate_sha256=plan['candidate_sha256'],
        batches={path.relative_to(ROOT).as_posix(): sha256(path) for path in receipts},
        ordinary_executions=240, calibrations=0,
        scope='Ordinary executions only; source-fault calibration, independent audit, public journeys and cleanup remain separate gates.'))
    print('Completed 240 exact-candidate Skim ordinary cases on', host, 'with zero faults/calibrations.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['linux', 'windows'], required=True)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--plan')
    args = parser.parse_args()
    if args.prepare_only:
        prepare(args.host)
    else:
        plan = Path(args.plan).resolve(strict=True) if args.plan else (
            RAW / 'skim' / 'final-series-plan-native-exit-v26' / args.host / 'plan.json')
        plan.relative_to(RAW.resolve(strict=True))
        run(args.host, plan)


if __name__ == '__main__':
    main()
