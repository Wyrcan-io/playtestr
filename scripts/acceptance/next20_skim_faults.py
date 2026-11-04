"""Build bounded Skim source mutants and require frozen cases to detect them."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from adversarial_process import execute
from next20_check import RAW, ROOT, NextCampaign
from next20_rust_fetch import environment, short_owned_path
from readiness_evidence import immutable_json, sha256
from readiness_build_plop import usage


async def main():
    raw = RAW / 'active' / 'skim'
    source = raw / 'src'
    docs = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass/skim'
    build = json.loads((raw / 'build.json').read_text(encoding='utf-8'))
    pin = build['pin']
    faults = [
        dict(id='SKIM-EXIT-EMPTY-01', source='src/bin/main.rs',
             old='Ok(i32::from(result.selected_items.is_empty()))', new='Ok(0)',
             case='E02', spec='E02-v2.json',
             claim='A no-match run incorrectly exits zero instead of its documented nonzero status.'),
        dict(id='SKIM-MATCH-COUNT-01', source='src/tui/input.rs',
             old='write!(parts, "{}/{}", self.matched, self.total)', new='write!(parts, "0/0")',
             case='N01', spec='N01-v2.json',
             claim='The interactive match count is falsely rendered as zero.'),
        dict(id='SKIM-MULTI-COUNT-01', source='src/tui/input.rs',
             old='write!(parts, " [{}]", self.selected)', new='write!(parts, " [0]")',
             case='N04', spec='N04-v2.json',
             claim='The multi-selection status indicator hides selected items.'),
    ]
    for fault in faults:
        fault['path'] = source / fault['source']
        original = fault['path'].read_bytes()
        fault['original_bytes'] = original
        fault['original_sha256'] = hashlib.sha256(original).hexdigest()
        text = original.decode('utf-8')
        count = text.count(fault['old'])
        expected = 1 if fault['id'] == 'SKIM-EXIT-EMPTY-01' else 2
        if count != expected:
            raise ValueError(f"{fault['id']} source anchor count {count}, expected {expected}")
        fault['mutated_bytes'] = text.replace(fault['old'], fault['new']).encode('utf-8')
        fault['mutated_sha256'] = hashlib.sha256(fault['mutated_bytes']).hexdigest()

    rows = []
    fault_root = RAW / 'active'
    cargo = Path(build['cargo_path'])
    rustc = Path(build['compiler_path'])
    env = environment(raw)
    env.update(RUSTC=str(rustc), RUSTDOC=str(rustc.with_name('rustdoc.exe')),
               CARGO_NET_OFFLINE='true', SOURCE_DATE_EPOCH='1793030400',
               CARGO_HOME=str(raw / 'cargo-home'),
               CARGO_TARGET_DIR=str(raw / 'cargo-target'))
    env['PATH'] = str(rustc.parent) + os.pathsep + env['PATH']
    for key in ['CARGO_HOME', 'CARGO_TARGET_DIR', 'TEMP', 'TMP', 'TMPDIR']:
        env[key] = short_owned_path(env[key])
    command = [str(cargo), 'build', '--release', '--locked', '--offline', '--target',
               'x86_64-pc-windows-msvc', '--no-default-features', '--features',
               'cli,frizbee', '--bin', 'sk']
    campaign = NextCampaign(phase='development')
    try:
        for fault in faults:
            project = fault['id'].lower() + '-v5'
            target = fault_root / project
            target.mkdir(exist_ok=False)
            binary_dir = target / 'bin'
            binary_dir.mkdir()
            start = dict(schema_version=1, project='skim', fault=fault['id'],
                         source_pin=pin, source_path=fault['source'],
                         original_sha256=fault['original_sha256'],
                         mutant_sha256=fault['mutated_sha256'], case=fault['case'],
                         spec=fault['spec'], claim=fault['claim'], started_before_build=True,
                         target_executed=False)
            immutable_json(target / 'fault-started.json', start)
            fault['path'].write_bytes(fault['mutated_bytes'])
            build_task = asyncio.create_task(execute(command, 'skim', 'build-' + fault['id'],
                cwd=source, env=env, timeout=1800, output_cap=2 * 1024 * 1024,
                campaign=campaign))
            build_observations = []
            try:
                while not build_task.done():
                    active_bytes = await asyncio.to_thread(usage, RAW)
                    build_observations.append(active_bytes)
                    if active_bytes > 3 * 1024 ** 3:
                        raise RuntimeError('Skim mutant build exceeded the 3 GiB campaign bound')
                    await asyncio.sleep(2)
                attempt = await build_task
            finally:
                if not build_task.done():
                    build_task.cancel()
                    try:
                        await build_task
                    except asyncio.CancelledError:
                        pass
            built = raw / 'cargo-target' / 'x86_64-pc-windows-msvc' / 'release' / 'sk.exe'
            if not built.is_file():
                raise ValueError('mutant Cargo build omitted sk.exe')
            binary = binary_dir / 'sk.exe'
            shutil.copyfile(built, binary)
            digest = sha256(binary)
            immutable_json(target / 'task-owned.json', dict(
                campaign='runner-readiness-next-twenty-project-pass', project=project,
                parent_project='skim', source_pin=pin, source_mutation=fault['id'],
                target_executed=False, installed_globally=False))
            immutable_json(target / 'build.json', dict(
                schema_version=1, project=project, source_project='skim', pin=pin,
                runtime_kind='native', binary_relative_path='bin/sk.exe',
                binary_sha256=digest, build_attempt=attempt['id'],
                command=list(map(str, command)), features=['cli', 'frizbee'],
                source_path=fault['source'], source_before_sha256=fault['original_sha256'],
                source_mutant_sha256=fault['mutated_sha256'], installed_globally=False,
                observed_active_bytes=build_observations,
                build_hooks_reviewed=53, build_hooks_executed=True,
                dependency_fetch_review_sha256=sha256(raw / 'dependency-fetch-review.json')))
            immutable_json(target / 'runtime.json', dict(
                schema_version=1, kind='native', native=str(binary),
                native_sha256=digest, binary=str(binary), source_pin=pin))

            base_spec = json.loads((docs / fault['spec']).read_text(encoding='utf-8'))
            spec = dict(base_spec)
            spec['name'] = f"Skim {fault['id']} fault-detection case"
            spec['command'] = list(base_spec['command'])
            spec_dir = docs / 'faults'
            spec_dir.mkdir(exist_ok=True)
            # Commands in these specs resolve from the spec's directory. Compute
            # the mutant binary path from that location instead of replacing a
            # substring whose traversal depth changes under faults/.
            spec['command'][0] = os.path.relpath(binary, spec_dir)
            fixture_source = docs / base_spec['workspace']['fixture']
            fixture_dir = spec_dir / 'fixtures' / fault['id']
            if fixture_dir.exists():
                expected = {p.relative_to(fixture_source).as_posix(): sha256(p)
                            for p in fixture_source.rglob('*') if p.is_file()}
                observed = {p.relative_to(fixture_dir).as_posix(): sha256(p)
                            for p in fixture_dir.rglob('*') if p.is_file()}
                if observed != expected:
                    raise ValueError('existing fault fixture differs from reviewed control: ' + str(fixture_dir))
            else:
                for path in fixture_source.rglob('*'):
                    if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
                        raise ValueError('linked frozen fixture is refused')
                shutil.copytree(fixture_source, fixture_dir)
            spec['workspace'] = dict(base_spec['workspace'],
                fixture='fixtures/' + fault['id'],
                home='temporary', temp='temporary')
            for step in spec['steps']:
                snapshot = step.get('snapshot')
                if snapshot:
                    source_snapshot = docs / 'snapshots' / snapshot
                    if not source_snapshot.is_file():
                        raise ValueError('fault control snapshot is missing: ' + snapshot)
                    snapshot_dir = spec_dir / 'snapshots'
                    snapshot_dir.mkdir(exist_ok=True)
                    destination = snapshot_dir / snapshot
                    if destination.exists():
                        if sha256(destination) != sha256(source_snapshot):
                            raise ValueError('existing fault snapshot differs from its control')
                    else:
                        shutil.copyfile(source_snapshot, destination)
            spec_path = spec_dir / f"{fault['id']}-v7.json"
            immutable_json(spec_path, spec)
            label = f"skim-fault-{fault['id'].lower()}-v5"
            proc = subprocess.run([sys.executable, '-B',
                'scripts/acceptance/next20_playtestr_case.py', '--project', project,
                '--label', label, '--', str(spec_path.relative_to(ROOT))],
                cwd=ROOT, env=os.environ.copy(), capture_output=True, text=True,
                encoding='utf-8', errors='replace', timeout=360)
            evidence = RAW / 'active' / project / 'case-evidence'
            matches = []
            for path in evidence.glob('*/finished.json'):
                record = json.loads(path.read_text(encoding='utf-8'))
                if record.get('label') == label:
                    matches.append((path, record))
            if len(matches) != 1:
                raise ValueError(f"{fault['id']} expected one immutable case result, found {len(matches)}; "
                    f"child exit={proc.returncode}; stdout={proc.stdout[-2000:]!r}; stderr={proc.stderr[-2000:]!r}")
            finished_path, finished = matches[0]
            report = finished.get('report') or {}
            results = report.get('results') or []
            steps = results[0].get('steps', []) if results else []
            failed_steps = [step for step in steps if step.get('status') == 'failed']
            if proc.returncode == 0 or finished.get('status') != 'failed' or not failed_steps:
                raise ValueError(f"{fault['id']} mutant escaped its expected public-contract failure")
            finished_event = json.loads((RAW / 'events' /
                f"{finished.get('runner_attempt_id')}-finished.json").read_text(encoding='utf-8'))
            receipt = dict(start, target_executed=True, binary_sha256=digest,
                build_attempt=attempt['id'], build_output_sha256=hashlib.sha256(
                    attempt['output'].encode('utf-8')).hexdigest(),
                case_exit=proc.returncode, case_label=label,
                case_finished=str(finished_path.relative_to(ROOT)),
                case_finished_sha256=sha256(finished_path),
                report_sha256=finished.get('report_sha256'),
                failure_category=(failed_steps[0].get('failure') or {}).get('category'),
                failure_message=(failed_steps[0].get('failure') or {}).get('message'),
                failed_step_statuses=[step.get('status') for step in steps],
                detected=True, harness_cleanup=finished_event.get('harness_cleanup'),
                cleanup_errors=finished_event.get('cleanup_errors', []))
            immutable_json(target / 'fault-finished.json', receipt)
            rows.append(receipt)
            fault['path'].write_bytes(fault['original_bytes'])
            restored_sha = sha256(fault['path'])
            if restored_sha != fault['original_sha256']:
                raise ValueError(f"{fault['id']} source restoration failed")
            print(f"Detected {fault['id']} via {fault['case']}; failed step captured.")
    finally:
        for fault in faults:
            fault['path'].write_bytes(fault['original_bytes'])
    if len(rows) != len(faults):
        raise ValueError('not all declared Skim source faults completed')
    check = subprocess.run([sys.executable, '-B', 'scripts/acceptance/next20_skim_source_verify.py',
                            '--verify-only'], cwd=ROOT, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=60)
    if check.returncode:
        raise RuntimeError('restored Skim source failed provenance verification: ' + check.stdout + check.stderr)
    out = fault_root / 'fault-matrix-v1.json'
    immutable_json(out, dict(schema_version=1, project='skim', source_pin=pin,
        source_provenance_sha256=sha256(docs / 'source-provenance.json'),
        declared=3, detected=len(rows), source_restored=True,
        post_run_source_verification=check.stdout.strip(), faults=rows))
    print('Skim fault matrix:', out.relative_to(ROOT), '3/3 source faults detected; exact source restored.')


if __name__ == '__main__':
    asyncio.run(main())
