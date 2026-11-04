"""Run three pinned Git Town source mutations through unchanged public specs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = 'git-town'
PIN = '8d039892574d4852e1843020c31d423234042e78'
FAULTS = [
    dict(id='F01-parent-output', file='internal/cmd/config/get_parent.go',
         old=b'fmt.Print(parent)', new=b'fmt.Print(childBranch)',
         spec='N03-read-parent.json', expected_runner_exit=1,
         expected_failure_category='assertion_timeout',
         requirement='The configured parent command must print the configured parent.'),
    dict(id='F02-feature-refusal', file='internal/cmd/hack.go',
         old=b'if branchesSnapshot.Branches.HasLocalBranch(targetBranch) {',
         new=b'if !branchesSnapshot.Branches.HasLocalBranch(targetBranch) {',
         spec='N01-hack-feature.json', expected_runner_exit=1,
         expected_failure_category='assertion_timeout',
         requirement='Creating a new local branch must create the requested branch.'),
    dict(id='F03-prototype-persistence', file='internal/cmd/prototype.go',
         old=b'gitconfig.SetBranchTypeOverride(repo.Backend, configdomain.BranchTypePrototypeBranch, branchNames...)',
         new=b'gitconfig.SetBranchTypeOverride(repo.Backend, configdomain.BranchTypeFeatureBranch, branchNames...)',
         spec='N06-prototype-existing.json', expected_runner_exit=1,
         expected_failure_category='state_assertion_failure',
         requirement='A prototype classification must persist as prototype in Git config.'),
]


def digest_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def run(argv, *, cwd, env, timeout=300, cap=2 * 1024 * 1024):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                           timeout=timeout, check=False)
    stdout, stderr = result.stdout, result.stderr
    if len(stdout) > cap or len(stderr) > cap:
        raise ValueError('bounded Git Town fault command exceeded output cap')
    return result


def write_event(target, event):
    event_id = uuid.uuid4().hex
    path = target / 'fault-events' / (event_id + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    immutable_json(path, dict(schema_version=1, event_id=event_id, **event))
    return path


def verify_source(source, provenance, acquisition, target):
    git_metadata = source / '.git'
    if git_metadata.is_dir() or git_metadata.is_file():
        git_env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
        commit = run(['git', 'rev-parse', 'HEAD'], cwd=source, env=git_env, timeout=20)
        status = run(['git', 'status', '--porcelain=v1', '--untracked-files=all'],
                     cwd=source, env=git_env, timeout=30)
        if (commit.returncode != 0 or commit.stdout.decode().strip() != PIN or
                status.returncode != 0 or status.stdout):
            raise ValueError('pinned Git Town Git checkout is not at the exact clean source pin')
        return dict(source_mode='pinned Git checkout', source_commit=PIN,
                    source_tree_sha256=provenance['primary_tree_sha256'], buildvcs=True)

    # Local source archives do not contain .git. Verify every file and the exact
    # archive before using the supported no-VCS stamping build variant.
    archive = target / 'source.tar.gz'
    if not archive.is_file() or sha256(archive) != acquisition['archive_sha256']:
        raise ValueError('source archive is absent or differs from the pinned acquisition receipt')
    actual = {}
    for path in source.rglob('*'):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('pinned Git Town source archive materialization contains a link')
        if path.is_file():
            rel = path.relative_to(source).as_posix()
            actual[rel] = sha256(path)
    if actual != provenance['files']:
        raise ValueError('source archive materialization differs from complete pinned provenance')
    return dict(source_mode='verified immutable archive without Git metadata', source_commit=None,
                source_tree_sha256=provenance['primary_tree_sha256'], buildvcs=False)


def build(target, source, host, fault_id, phase):
    home = target / 'home'
    temp = target / 'tmp'
    binary = target / 'fault-binaries' / (fault_id + '-' + phase + '-' + uuid.uuid4().hex) / ('git-town.exe' if os.name == 'nt' else 'git-town')
    binary.parent.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    env.update(GOTOOLCHAIN='local', GOWORK=str(source / 'go.work'), GOPROXY='off',
               GOSUMDB='off', CGO_ENABLED='0', GOENV='off',
               GOMODCACHE=str(target / 'go-mod-cache'), GOCACHE=str(home / 'go-cache'),
               GOPATH=str(home / 'go-path'), HOME=str(home), USERPROFILE=str(home),
               APPDATA=str(home / 'appdata'), LOCALAPPDATA=str(home / 'localappdata'),
               TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    buildvcs = source.joinpath('.git').exists()
    argv = ['go', 'build', '-mod=vendor', '-trimpath']
    if not buildvcs:
        argv.append('-buildvcs=false')
    argv.extend(['-o', str(binary), '.'])
    result = run(argv, cwd=source, env=env, timeout=600)
    if result.returncode != 0 or not binary.is_file() or binary.is_symlink():
        raise RuntimeError('Git Town fault build failed: ' + result.stderr[-2048:].decode('utf-8', 'replace'))
    version = run([str(binary), '--version'], cwd=source, env=env, timeout=30)
    version_text = version.stdout.decode('utf-8', 'replace').strip()
    if version.returncode != 0 or version_text != 'Git Town 24.1.0':
        raise RuntimeError('fault build version check failed: ' + version_text)
    receipt = dict(project=PROJECT, pin=PIN, fault_id=fault_id, phase=phase,
        host_os=platform.system().lower(), host_arch=platform.machine().lower(),
        go_version=run(['go', 'version'], cwd=ROOT, env=env, timeout=20).stdout.decode().strip(),
        command=' '.join(argv).replace(str(binary), '<owned-bin>/git-town' + ('.exe' if os.name == 'nt' else '')),
        buildvcs_enabled=buildvcs,
        network_module_resolution='disabled', version=version_text,
        executable_relative=binary.relative_to(target).as_posix(),
        executable_sha256=sha256(binary), source_file_sha256={
            fault['file']: sha256(source / fault['file']) for fault in FAULTS})
    path = target / 'fault-builds' / (fault_id + '-' + phase + '-' + uuid.uuid4().hex + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    immutable_json(path, receipt)
    return receipt


def run_case(target, source, fault, phase, expected_exit, binary):
    case_helper = ROOT / 'scripts/acceptance/next20_git_town_case.py'
    spec = DOC / PROJECT / fault['spec']
    label = f"{fault['id']}-{phase}-{platform.system().lower()}"
    journal_phase = {'pristine-baseline': 'source-fault-baseline',
                     'corrupted': 'source-fault-corrupted',
                     'restored-recovery': 'source-fault-restored'}[phase]
    argv = [sys.executable, '-B', str(case_helper), '--label', label, '--phase',
            journal_phase,
            '--executable', str(binary),
            '--expected-runner-exit', str(expected_exit), str(spec.relative_to(ROOT))]
    before = {p.name for p in (target / 'case-evidence').glob('*') if p.is_dir()}
    result = run(argv, cwd=ROOT, env=os.environ, timeout=480)
    after = {p.name for p in (target / 'case-evidence').glob('*') if p.is_dir()}
    added = sorted(after - before)
    if len(added) != 1:
        raise RuntimeError('fault case did not create exactly one owned evidence directory')
    outcome_path = target / 'case-evidence' / added[0] / 'finished.json'
    if not outcome_path.is_file():
        raise RuntimeError('fault case finished receipt is missing')
    outcome = json.loads(outcome_path.read_text(encoding='utf-8'))
    report = outcome.get('report') or {}
    summary = report.get('summary') or {}
    report_results = report.get('results') or []
    failed_steps = [dict(name=x.get('name'), status=x.get('status'), failure=x.get('failure'))
                    for x in report_results if x.get('status') != 'passed']
    result_failure = ((report_results[0].get('failure') or {}) if report_results else {})
    expected_failure = expected_exit != 0
    if result.returncode != 0 or outcome.get('status') != 'completed':
        raise RuntimeError('fault case harness invocation failed: ' + result.stderr[-2048:].decode('utf-8', 'replace'))
    if expected_failure and (len(failed_steps) != 1 or summary.get('failed') != 1 or
                             summary.get('passed') != 0 or summary.get('total') != 1 or
                             result_failure.get('category') != fault['expected_failure_category']):
        raise RuntimeError('mutated source did not create an observable unchanged-contract failure')
    if not expected_failure and (failed_steps or summary.get('passed') != 1 or
                                 summary.get('failed') != 0 or summary.get('total') != 1 or
                                 report_results[0].get('cleanup', {}).get('confirmed_exited') is False or
                                 report_results[0].get('workspace', {}).get('cleaned') is False):
        raise RuntimeError('pristine/restored source did not pass its unchanged public contract')
    if fault['id'] == 'F03-prototype-persistence' and expected_failure:
        steps = report_results[0].get('steps', [])
        if (len(steps) != 3 or [step.get('status') for step in steps] !=
                ['passed', 'passed', 'failed']):
            raise RuntimeError('saved-state mutation was not rejected after terminal and exit evidence passed')
    return dict(label=label, phase=phase, expected_runner_exit=expected_exit,
        target_exit_code=(report_results[0].get('exit_code') if report_results else None),
        runner_attempt_id=outcome.get('runner_attempt_id'),
        report_sha256=outcome.get('report_sha256'), summary=summary,
        failed_steps=failed_steps, failure_category=result_failure.get('category'),
        evidence_directory=outcome_path.parent.relative_to(target).as_posix(),
        stdout_sha256=digest_bytes(result.stdout), stderr_sha256=digest_bytes(result.stderr))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['linux', 'windows'], required=True)
    args = parser.parse_args()
    target = RAW / 'active' / PROJECT
    source = target / 'src'
    provenance_path = DOC / PROJECT / 'source-provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    acquisition_path = target / 'acquisition.json'
    acquisition = json.loads(acquisition_path.read_text(encoding='utf-8'))
    if provenance.get('pin') != PIN or not source.is_dir() or source.is_symlink():
        raise ValueError('fault target is not the reviewed immutable Git Town checkout')
    if acquisition.get('pin') != PIN or acquisition.get('repository') != 'git-town/git-town':
        raise ValueError('pinned Git Town acquisition receipt is missing or mismatched')
    source_identity = verify_source(source, provenance, acquisition, target)
    selected_source = {fault['file']: sha256(source / fault['file']) for fault in FAULTS}
    expected_source = {fault['file']: provenance['files'].get(fault['file']) for fault in FAULTS}
    if selected_source != expected_source:
        refusal = dict(schema_version=1, project=PROJECT, phase='prelaunch-refusal',
            source_pin_expected=PIN, source_identity=source_identity,
            selected_source_hashes=selected_source, expected_source_hashes=expected_source,
            target_process_launched=False, qualification_credit=0,
            reason='fault suite requires the clean exact pinned Git Town checkout and source bytes')
        refusal_path = target / ('fault-prelaunch-refusal-' + uuid.uuid4().hex + '.json')
        immutable_json(refusal_path, refusal)
        raise ValueError('Git Town source fault suite refused before build: checkout/source identity mismatch')
    if (target / 'build.json').is_file():
        initial = json.loads((target / 'build.json').read_text(encoding='utf-8'))
        if initial.get('pin') != PIN or not initial.get('build_succeeded'):
            raise ValueError('initial native source build receipt is missing or mismatched')
    started = dict(schema_version=1, project=PROJECT, host=args.host,
        runner_os=platform.system().lower(), runner_arch=platform.machine().lower(),
        source_pin=PIN, source_archive_sha256=acquisition['archive_sha256'],
        source_identity=source_identity,
        matrix_id=uuid.uuid4().hex,
        source_provenance_sha256=sha256(provenance_path),
        scenario_catalog_sha256=sha256(DOC / PROJECT / 'scenario-catalog-v3.json'),
        unchanged_specs=[dict(path=fault['spec'], sha256=sha256(DOC / PROJECT / fault['spec']))
                         for fault in FAULTS],
        fault_declarations=[dict(id=f['id'], file=f['file'], requirement=f['requirement'],
                                 expected_runner_exit=f['expected_runner_exit'],
                                 expected_failure_category=f['expected_failure_category']) for f in FAULTS],
        status='started; no qualification credit until independent audit')
    start_path = target / ('fault-matrix-started-' + started['matrix_id'] + '.json')
    immutable_json(start_path, started)
    results = []
    try:
        for fault in FAULTS:
            source_file = source / fault['file']
            original = source_file.read_bytes()
            expected_hash = provenance['files'].get(fault['file'])
            if expected_hash is None or digest_bytes(original) != expected_hash:
                raise ValueError(f"{fault['id']}: exact pinned baseline source hash mismatch")
            if original.count(fault['old']) != 1:
                raise ValueError(f"{fault['id']}: expected exactly one patch anchor in reviewed source")
            baseline_build = build(target, source, args.host, fault['id'], 'pristine-baseline')
            baseline = run_case(target, source, fault, 'pristine-baseline', 0,
                                target / baseline_build['executable_relative'])
            write_event(target, dict(project=PROJECT, fault_id=fault['id'], phase='pristine-baseline',
                source_sha256=expected_hash, executable_sha256=baseline_build['executable_sha256'],
                case=baseline, status='passed'))
            corrupted_bytes = original.replace(fault['old'], fault['new'], 1)
            source_file.write_bytes(corrupted_bytes)
            mutated_hash = sha256(source_file)
            mutated_build = None
            corrupted = None
            corruption_error = None
            try:
                if mutated_hash == expected_hash:
                    raise ValueError('mutation did not change the selected pinned source file')
                mutated_build = build(target, source, args.host, fault['id'], 'corrupted')
                corrupted = run_case(target, source, fault, 'corrupted', fault['expected_runner_exit'],
                                     target / mutated_build['executable_relative'])
                write_event(target, dict(project=PROJECT, fault_id=fault['id'], phase='corrupted',
                    baseline_source_sha256=expected_hash, corrupted_source_sha256=mutated_hash,
                    executable_sha256=mutated_build['executable_sha256'], case=corrupted,
                    status='unchanged contract detected source mutation'))
            except Exception as exc:
                corruption_error = exc
            finally:
                source_file.write_bytes(original)
            restored_hash = sha256(source_file)
            if restored_hash != expected_hash:
                raise RuntimeError(f"{fault['id']}: exact source restoration failed")
            verify_source(source, provenance, acquisition, target)
            restored_build = build(target, source, args.host, fault['id'], 'restored-rebuild')
            restored = run_case(target, source, fault, 'restored-recovery', 0,
                                target / restored_build['executable_relative'])
            write_event(target, dict(project=PROJECT, fault_id=fault['id'], phase='restored-recovery',
                source_sha256=restored_hash, executable_sha256=restored_build['executable_sha256'],
                case=restored, status='exact source restored, rebuilt, and unchanged contract passed'))
            if corruption_error:
                raise RuntimeError(f"{fault['id']}: corrupted phase did not produce its required detection evidence: {corruption_error}") from corruption_error
            results.append(dict(id=fault['id'], baseline=baseline, corrupted=corrupted,
                restored=restored, baseline_source_sha256=expected_hash,
                corrupted_source_sha256=mutated_hash, restored_source_sha256=restored_hash,
                baseline_executable_sha256=baseline_build['executable_sha256'],
                corrupted_executable_sha256=mutated_build['executable_sha256'],
                restored_executable_sha256=restored_build['executable_sha256']))
        record = dict(schema_version=1, project=PROJECT, host=args.host,
            source_pin=PIN, source_provenance_sha256=sha256(provenance_path),
            scenario_catalog_sha256=started['scenario_catalog_sha256'],
            started_sha256=sha256(start_path), faults=results,
            totals=dict(distinct_faults=len(results), phases=len(results) * 3,
                        baseline_passes=len(results), mutations_detected=len(results),
                        restored_recovery_passes=len(results)),
            admission_credit=0,
            disposition='Three source mutations were detected by unchanged public contracts and exactly restored/rebuilt. Independent evidence audit and final-candidate qualification remain required.')
        out = DOC / PROJECT / f"fault-matrix-{args.host}-v1.json"
        immutable_json(out, record)
        print('Git Town source fault matrix passed:', args.host, 'faults', len(results),
              'phases', len(results) * 3, 'receipt', out.relative_to(ROOT))
    except Exception as exc:
        write_event(target, dict(project=PROJECT, phase='matrix-aborted', error_type=type(exc).__name__,
                                 error=str(exc)[:2048], completed_faults=len(results), status='failed'))
        raise


if __name__ == '__main__':
    main()

