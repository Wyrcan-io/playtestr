"""Exercise Skim's public recorder, diagnosis, maintenance and relocation route."""
import asyncio
import copy
import json
import os
from pathlib import Path
import shutil

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256


PROJECT = 'skim'
PIN = '1ab47f6ba7f1bfc355273bbdd98d4b2056ef95a3'


def report_result(path, expected_status):
    value = json.loads(path.read_text(encoding='utf-8'))
    if len(value.get('results', [])) != 1:
        raise ValueError('Skim public route did not produce one ordinary result')
    result = value['results'][0]
    if result.get('status') != expected_status:
        raise ValueError(f'expected Skim public report status {expected_status}')
    if expected_status == 'passed':
        if any(step.get('status') != 'passed' for step in result.get('steps', [])):
            raise ValueError('passing Skim public route has a non-passing step')
        if not result.get('workspace', {}).get('cleaned') or not result.get('cleanup', {}).get('confirmed_exited'):
            raise ValueError('Skim public route did not confirm workspace/process cleanup')
    return result


async def main():
    target = RAW/'active'/PROJECT
    package = DOC/PROJECT
    output = RAW/PROJECT/'first-public-v1'
    if output.exists():
        raise ValueError('refusing existing Skim public route evidence root')
    build = json.loads((target/'build.json').read_text(encoding='utf-8'))
    provenance = json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
    if provenance.get('pin') != PIN or build.get('pin') != PIN:
        raise ValueError('Skim public route source pin mismatch')
    original_target = target/'bin/sk.exe'
    original_hash = sha256(original_target)
    if original_hash != build.get('binary_sha256'):
        raise ValueError('Skim public route target differs from reviewed native build')

    output.mkdir(parents=True)
    canonical = output/'project'
    (canonical/'bin').mkdir(parents=True)
    shutil.copy2(original_target, canonical/'bin'/original_target.name)
    shutil.copytree(package/'fixtures/N01', canonical/'fixture')
    runner = executable('native-exit-v1')
    campaign = NextCampaign(phase='public-authoring')
    env = dict(os.environ)
    attempts = []

    async def run(argv, label, *, input=None, expected=0, timeout=180):
        result = await execute(argv, PROJECT, label, cwd=ROOT, env=env, input=input,
                               expected=expected, timeout=timeout, campaign=campaign)
        attempts.append(dict(id=result['id'], label=label, returncode=result['returncode'],
                             seconds=round(result['seconds'], 3)))
        return result

    version = await run([runner, '--version'], 'skim-first-public-runner-version')
    if version['output'].strip() != 'playtestr v0.4.0-rc.6':
        raise ValueError('public Skim route did not use the exact private candidate')

    controls = [
        '/expect 1/3',
        '/key Enter',
        '/exit 0',
        '/expect cedar',
        '/snapshot selected.txt',
        '/review',
        '/replay',
        '/save',
    ]
    spec = canonical/'selection.json'
    command = [runner, 'record', '--output', spec.relative_to(ROOT),
               '--name', 'Select the unique cedar result', '--fixture', 'fixture',
               '--temporary-home', '--temporary-temp', '--width', '120', '--height', '24',
               '--timeout-ms', '10000', '--run-timeout-ms', '30000',
               '--env', 'SKIM_DEFAULT_COMMAND=python emit.py',
               '--env', 'TERM=xterm-256color', '--env', 'LANG=C.UTF-8', '--env', 'LC_ALL=C.UTF-8',
               '--inherit-env', 'PATH', '--inherit-env', 'SystemRoot', '--inherit-env', 'COMSPEC',
               '--', 'bin/sk.exe', '--no-sort', '--query=cedar']
    await run(command, 'skim-first-public-record-review-replay-export', input='\n'.join(controls)+'\n')
    recorded = json.loads(spec.read_text(encoding='utf-8'))
    if recorded.get('version') != 3 or recorded.get('command')[-2:] != ['--no-sort', '--query=cedar']:
        raise ValueError('public recorder export differs from the reviewed selection task')
    if recorded.get('workspace', {}).get('fixture') != 'fixture':
        raise ValueError('public recorder did not export the managed fixture route')
    snapshot = canonical/'snapshots/selected.txt'
    if not snapshot.is_file() or b'cedar' not in snapshot.read_bytes():
        raise ValueError('reviewed public snapshot does not contain the exact selection')

    first_report = output/'first-use-report.json'
    await run([runner, 'test', '--report', first_report.relative_to(ROOT),
               '--artifacts-dir', (output/'first-use-artifacts').relative_to(ROOT),
               spec.relative_to(ROOT)], 'skim-first-public-ordinary-test')
    first_result = report_result(first_report, 'passed')

    # Preserve the approved first use; diagnose an intentionally incorrect
    # candidate snapshot in an independent copy and require useful failure data.
    diagnosis = output/'diagnosis'
    shutil.copytree(canonical, diagnosis)
    wrong_snapshot = diagnosis/'snapshots/selected.txt'
    wrong = wrong_snapshot.read_bytes().replace(b'cedar', b'violet')
    if wrong == wrong_snapshot.read_bytes():
        raise ValueError('diagnostic mutation did not change the selected assertion')
    wrong_snapshot.write_bytes(wrong)
    diagnosis_report = output/'diagnosis-report.json'
    await run([runner, 'test', '--report', diagnosis_report.relative_to(ROOT),
               '--artifacts-dir', (output/'diagnosis-artifacts').relative_to(ROOT),
               (diagnosis/'selection.json').relative_to(ROOT)],
              'skim-first-public-seeded-snapshot-diagnosis', expected=1)
    diagnosed = report_result(diagnosis_report, 'failed')
    failure = diagnosed.get('failure') or {}
    if not failure.get('category') or not failure.get('message'):
        raise ValueError('seeded Skim assertion failure lacks a useful category/message')

    # Change the intended query, observe the old expectation fail, and update
    # only the named screen baseline through the documented public command.
    maintenance = output/'maintenance'
    shutil.copytree(canonical, maintenance)
    maintained_spec = maintenance/'selection.json'
    approved = json.loads(maintained_spec.read_text(encoding='utf-8'))
    original_command = copy.deepcopy(approved['command'])
    matches = [i for i, value in enumerate(approved['command']) if value == '--query=cedar']
    if len(matches) != 1:
        raise ValueError('public maintenance cannot identify the exact query argument')
    approved['command'][matches[0]] = '--query=amber'
    immutable_json(maintained_spec, approved)
    before_snapshot = sha256(maintenance/'snapshots/selected.txt')
    maintenance_fail_report = output/'maintenance-before-update-report.json'
    await run([runner, 'test', '--report', maintenance_fail_report.relative_to(ROOT),
               '--artifacts-dir', (output/'maintenance-before-update-artifacts').relative_to(ROOT),
               maintained_spec.relative_to(ROOT)],
              'skim-first-public-intended-change-before-maintenance', expected=1)
    report_result(maintenance_fail_report, 'failed')
    update_report = output/'maintenance-update-report.json'
    await run([runner, 'test', '--update', '--snapshot', 'selected.txt', '--report',
               update_report.relative_to(ROOT), '--artifacts-dir',
               (output/'maintenance-update-artifacts').relative_to(ROOT),
               maintained_spec.relative_to(ROOT)], 'skim-first-public-selected-snapshot-maintenance')
    report_result(update_report, 'passed')
    updated_snapshot = maintenance/'snapshots/selected.txt'
    if sha256(updated_snapshot) == before_snapshot or b'amber' not in updated_snapshot.read_bytes():
        raise ValueError('selected maintenance did not update to the intended amber result')
    if json.loads(maintained_spec.read_text(encoding='utf-8'))['command'] != approved['command']:
        raise ValueError('selected maintenance unexpectedly changed the approved command')
    for name in ['fixture/emit.py', 'fixture/items.txt', 'bin/sk.exe']:
        if sha256(maintenance/name) != sha256(canonical/name):
            raise ValueError('selected maintenance changed unrelated project bytes: '+name)

    relocated = output/'relocated space café'
    shutil.copytree(maintenance, relocated)
    relocation_report = output/'relocation-report.json'
    await run([runner, 'test', '--report', relocation_report.relative_to(ROOT), '--artifacts-dir',
               (output/'relocation-artifacts').relative_to(ROOT),
               (relocated/'selection.json').relative_to(ROOT)], 'skim-first-public-unicode-relocation')
    relocation_result = report_result(relocation_report, 'passed')

    # Remove only the four campaign-owned Skim executable copies; retain specs,
    # snapshots, reports and inventories as bounded review material.
    removed = []
    for copy_root in [canonical, diagnosis, maintenance, relocated]:
        binary = copy_root/'bin/sk.exe'
        if sha256(binary) != original_hash:
            raise ValueError('refuse to remove a Skim binary whose identity changed')
        binary.unlink()
        binary.parent.rmdir()
        if binary.exists():
            raise ValueError('owned Skim runtime removal was not confirmed')
        removed.append(dict(path=binary.relative_to(ROOT).as_posix(), sha256=original_hash, absent=True))

    receipt = dict(schema_version=1, status='public-agent-route-passed-not-admitted', project=PROJECT,
                   source_pin=PIN, candidate='v0.4.0-rc.6', runner_sha256=sha256(runner),
                   native_target_sha256=original_hash, first_use_target_version='sk 5.8.0',
                   initial_window=True, shell_invocations_to_first_reviewed_ordinary_pass=3,
                   first_window_controls=len(controls), handwritten_playtestr_json=False,
                   first_spec_sha256=sha256(spec), first_snapshot_sha256=sha256(snapshot),
                   first_report_sha256=sha256(first_report), first_invocation=first_result['invocation_id'],
                   diagnosis=dict(report_sha256=sha256(diagnosis_report), status='failed-as-seeded',
                                  category=failure['category'], message=failure['message']),
                   maintenance=dict(before_report_sha256=sha256(maintenance_fail_report),
                                    update_report_sha256=sha256(update_report),
                                    original_snapshot_sha256=before_snapshot,
                                    updated_snapshot_sha256=sha256(updated_snapshot),
                                    approved_command_unchanged=True, unrelated_fixture_and_runtime_unchanged=True),
                   relocation=dict(path='relocated space café', report_sha256=sha256(relocation_report),
                                   invocation=relocation_result['invocation_id'], passed=True),
                   target_copy_removal=removed, attempts=attempts, human_participants=0,
                   human_time='unmeasured', assistance='Prepared engineering route; no beginner inference.',
                   scope='Exact rc.6 public record/review/replay/save/test, seeded wrong-screen diagnosis, selected snapshot maintenance, and Unicode-path relocation. No admission asserted until independent oracle/control, delivery, full cleanup and final campaign gates close.')
    immutable_json(package/'first-public-route-v1.json', receipt)
    print('Skim public route passed: exact rc.6 first-use in 3 commands/'+str(len(controls))+
          ' controls, seeded failure diagnosed, selected snapshot maintained, Unicode relocation passed; no admission.')


if __name__ == '__main__':
    asyncio.run(main())
