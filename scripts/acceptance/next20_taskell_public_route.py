"""Exercise Taskell through the exact candidate's documented public authoring route."""
import asyncio
import base64
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256


PROJECT = 'taskell'
PIN = 'a2df95f26762fc3e78d6f131cea7fc1f3b13bd47'


def report_result(path, expected_status):
    value = json.loads(path.read_text(encoding='utf-8'))
    if len(value.get('results', [])) != 1:
        raise ValueError('Taskell public route did not produce one ordinary result')
    result = value['results'][0]
    if result.get('status') != expected_status:
        raise ValueError(f'expected Taskell public report status {expected_status}')
    if not result.get('workspace', {}).get('cleaned') or not result.get('cleanup', {}).get('confirmed_exited'):
        raise ValueError('Taskell public route did not confirm process/workspace cleanup')
    if expected_status == 'passed':
        if any(step.get('status') != 'passed' for step in result.get('steps', [])):
            raise ValueError('passing Taskell public report has a non-passing step')
    return result


async def main():
    target = RAW/'active'/PROJECT
    package = DOC/PROJECT
    output = RAW/PROJECT/'public-route-native-exit-v1'
    if output.exists():
        raise ValueError('refusing existing Taskell public-route evidence root')
    runtime_lock = json.loads((package/'native-runtime-lock-native-exit-v1.json').read_text(encoding='utf-8'))
    build = json.loads((target/'build.json').read_text(encoding='utf-8'))
    if runtime_lock.get('source_pin') != PIN or build.get('source_pin') != PIN:
        raise ValueError('Taskell public route source pin mismatch')
    original_target = Path(target/build['binary_relative_path']).resolve(strict=True)
    original_hash = sha256(original_target)
    if original_hash != build.get('binary_sha256'):
        raise ValueError('Taskell public route target differs from reviewed native build')

    output.mkdir(parents=True)
    canonical = output/'project'
    (canonical/'bin').mkdir(parents=True)
    shutil.copy2(original_target, canonical/'bin'/('taskell.exe' if os.name == 'nt' else 'taskell'))
    shutil.copytree(package/'host-contracts/fixtures', canonical/'fixtures')
    fixture_hashes = {p.relative_to(canonical/'fixtures').as_posix(): sha256(p)
                      for p in sorted((canonical/'fixtures').rglob('*')) if p.is_file()}
    frozen_fixture_hashes = json.loads((package/'host-contracts/fixtures-manifest.json').read_text(encoding='utf-8'))['files']
    if fixture_hashes != frozen_fixture_hashes:
        raise ValueError('Taskell public-route fixture bytes differ from the reviewed fixture manifest')
    public_case_path = package/'host-contracts/taskell-create-task.json'
    public_case = json.loads(public_case_path.read_text(encoding='utf-8'))
    frozen_states = [step['state'] for step in public_case.get('steps', [])
                     if step.get('state', {}).get('path') == 'board-basic.md']
    if len(frozen_states) != 1 or frozen_states[0].get('kind') != 'file':
        raise ValueError('Taskell public scenario lacks one exact frozen board-state oracle')
    expected_board = frozen_states[0]['bytes_base64']
    runner = executable('native-exit-v1')
    installed = json.loads((runner.parent/'installed.json').read_text(encoding='utf-8'))
    campaign = NextCampaign(phase='public-authoring')
    env = dict(os.environ)
    env['PATH'] = str(canonical/'bin') + os.pathsep + env.get('PATH', '')
    env['LC_ALL'] = 'C.UTF-8'
    env['LANG'] = 'C.UTF-8'
    attempts = []
    controls = [
        '/expect To Do',
        '/expect Review sample',
        '/text "a"',
        '/text "New regression task"',
        '/key Enter',
        '/expect New regression task',
        '/expect INSERT',
        '/key Escape',
        '/absent INSERT',
        '/text "q"',
        '/exit 0',
        '/file board-basic.md',
        '/review',
        '/replay',
        '/save',
    ]
    immutable_json(output/'planned.json', dict(
        schema_version=1, project=PROJECT, phase='public-authoring', source_pin=PIN,
        candidate='v0.4.0-rc.6', candidate_archive_sha256=installed['archive_sha256'],
        runner_sha256=sha256(runner), target_binary_sha256=original_hash,
        host=platform.platform(), architecture=platform.machine(),
        public_case='docs/validation/runner-readiness-next-twenty-project-pass/taskell/host-contracts/taskell-create-task.json',
        public_case_sha256=sha256(public_case_path),
        fixture_hashes=fixture_hashes, no_handwritten_first_use_spec=True,
        initial_shell_invocations_expected=3, first_use_controls=controls,
        expected_first_run='record, review, fresh replay, save, then ordinary candidate test passes and cleans its managed workspace',
        seeded_diagnosis='deliberately wrong rendered-screen expectation fails with category and evidence',
        maintenance='change the intended task text, observe the old saved-state expectation fail, then rerecord only that state through the documented public route',
        relocation='move the complete spec, fixture and target bundle beneath a spaced Unicode path and rerun',
        delivered_workflow='generate and review a source-pinned free-workflow preview; do not dispatch or create a PR',
        command_timeout_seconds=180, route_timeout_seconds=1200,
        storage_root=output.relative_to(ROOT).as_posix()))

    async def run(argv, label, *, input=None, expected=0, timeout=180):
        result = await execute(argv, PROJECT, label, cwd=ROOT, env=env, input=input,
                               expected=expected, timeout=timeout, campaign=campaign)
        attempts.append(dict(id=result['id'], label=label, returncode=result['returncode'],
                             seconds=round(result['seconds'], 3)))
        return result

    version = await run([runner, '--version'], 'taskell-public-route-runner-version')
    if version['output'].strip() != 'playtestr v0.4.0-rc.6':
        raise ValueError('Taskell public route did not use the exact private candidate')

    spec = canonical/'create-task.json'
    command = [runner, 'record', '--output', spec.relative_to(ROOT),
               '--name', 'Create and save a Taskell board item', '--fixture', 'fixtures',
               '--temporary-home', '--temporary-temp', '--width', '80', '--height', '24',
               '--timeout-ms', '5000', '--run-timeout-ms', '60000',
               '--env', 'TERM=xterm-256color', '--env', 'LANG=C.UTF-8', '--env', 'LC_ALL=C.UTF-8',
               '--inherit-env', 'PATH',
               '--', 'bin/taskell', 'board-basic.md']
    await run(command, 'taskell-first-public-record-review-replay-save', input='\n'.join(controls)+'\n', timeout=240)
    recorded = json.loads(spec.read_text(encoding='utf-8'))
    if recorded.get('version') != 3 or recorded.get('command')[-2:] != ['bin/taskell', 'board-basic.md']:
        raise ValueError('Taskell public recorder export differs from the reviewed create-task interaction')
    if recorded.get('steps') != public_case.get('steps'):
        raise ValueError('Taskell public recorder checkpoints differ from the frozen create-task interaction')
    if recorded.get('workspace', {}).get('fixture') != 'fixtures':
        raise ValueError('Taskell public recorder did not export the managed fixture route')
    state_steps = [step for step in recorded.get('steps', []) if step.get('state', {}).get('path') == 'board-basic.md']
    if len(state_steps) != 1 or state_steps[0]['state'].get('kind') != 'file':
        raise ValueError('Taskell recorder did not export exactly one reviewed saved-board expectation')
    approved_board = state_steps[0]['state']['bytes_base64']
    if approved_board != expected_board:
        raise ValueError('Taskell public recorder saved bytes differ from the independently frozen intended board')
    screen_count_before = sum(1 for step in recorded.get('steps', []) if step.get('expect') == 'New regression task')
    if screen_count_before != 1:
        raise ValueError('Taskell first-use route lacks the unique positive task checkpoint')
    if (sum(1 for step in recorded.get('steps', []) if step.get('expect') == 'INSERT') != 1 or
            sum(1 for step in recorded.get('steps', []) if step.get('expect_not') == 'INSERT') != 1):
        raise ValueError('Taskell first-use route lacks positive insert-mode entry and Escape-exit checkpoints')
    first_report = output/'first-use-report.json'
    await run([runner, 'test', '--report', first_report.relative_to(ROOT), '--artifacts-dir',
               (output/'first-use-artifacts').relative_to(ROOT), spec.relative_to(ROOT)],
              'taskell-first-public-ordinary-test')
    first_result = report_result(first_report, 'passed')

    diagnosis = output/'diagnosis'
    shutil.copytree(canonical, diagnosis)
    wrong_spec = diagnosis/'create-task.json'
    broken = json.loads(wrong_spec.read_text(encoding='utf-8'))
    wrong_expectations = [step for step in broken['steps'] if step.get('expect') == 'New regression task']
    if len(wrong_expectations) != 1:
        raise ValueError('Taskell diagnostic mutation cannot identify the exact screen expectation')
    wrong_expectations[0]['expect'] = 'Wrong task text'
    wrong_spec.write_text(json.dumps(broken, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    diagnosis_report = output/'diagnosis-report.json'
    await run([runner, 'test', '--report', diagnosis_report.relative_to(ROOT), '--artifacts-dir',
               (output/'diagnosis-artifacts').relative_to(ROOT), wrong_spec.relative_to(ROOT)],
              'taskell-first-public-seeded-screen-diagnosis', expected=1)
    diagnosed = report_result(diagnosis_report, 'failed')
    failure = diagnosed.get('failure') or {}
    if not failure.get('category') or not failure.get('message'):
        raise ValueError('seeded Taskell assertion failure lacks a useful category/message')

    maintenance = output/'maintenance'
    shutil.copytree(canonical, maintenance)
    maintenance_spec = maintenance/'create-task.json'
    maintained = json.loads(maintenance_spec.read_text(encoding='utf-8'))
    text_steps = [step for step in maintained['steps'] if step.get('text') == 'New regression task']
    screen_steps = [step for step in maintained['steps'] if step.get('expect') == 'New regression task']
    if len(text_steps) != 1 or len(screen_steps) != 1:
        raise ValueError('Taskell maintenance cannot identify the exact intended task input')
    text_steps[0]['text'] = 'Updated regression task'
    screen_steps[0]['expect'] = 'Updated regression task'
    maintenance_spec.write_text(json.dumps(maintained, sort_keys=True, indent=2)+'\n',
                                encoding='utf-8', newline='\n')
    maintenance_fail_report = output/'maintenance-before-update-report.json'
    await run([runner, 'test', '--report', maintenance_fail_report.relative_to(ROOT), '--artifacts-dir',
               (output/'maintenance-before-update-artifacts').relative_to(ROOT),
               maintenance_spec.relative_to(ROOT)], 'taskell-first-public-intended-change-before-state-maintenance', expected=1)
    maintenance_failure_result = report_result(maintenance_fail_report, 'failed')
    maintenance_failure = maintenance_failure_result.get('failure') or {}
    if not maintenance_failure.get('category') or not maintenance_failure.get('message'):
        raise ValueError('Taskell selected maintenance preflight lacks a useful saved-state failure')
    state_index = next(i for i, step in enumerate(maintained['steps'], 1)
                       if step.get('state', {}).get('path') == 'board-basic.md')
    edit_controls = [f'/update-state {state_index}', '/review', '/replay', '/save']
    await run([runner, 'record', '--edit', maintenance_spec.relative_to(ROOT)],
              'taskell-first-public-selected-file-state-maintenance', input='\n'.join(edit_controls)+'\n', timeout=240)
    revised = json.loads(maintenance_spec.read_text(encoding='utf-8'))
    revised_steps = [step for step in revised['steps'] if step.get('state', {}).get('path') == 'board-basic.md']
    if len(revised_steps) != 1 or revised_steps[0]['state'].get('bytes_base64') == approved_board:
        raise ValueError('Taskell selected maintenance did not replace the intended saved-board expectation')
    original_state_bytes = base64.b64decode(expected_board, validate=True)
    if original_state_bytes.count(b'New regression task') != 1:
        raise ValueError('frozen Taskell public scenario does not have a unique intended task value')
    expected_updated = base64.b64encode(original_state_bytes.replace(
        b'New regression task', b'Updated regression task', 1)).decode('ascii')
    expected_maintained = json.loads(json.dumps(recorded))
    expected_text_step = [step for step in expected_maintained['steps'] if step.get('text') == 'New regression task']
    expected_screen_step = [step for step in expected_maintained['steps'] if step.get('expect') == 'New regression task']
    expected_state_step = [step['state'] for step in expected_maintained['steps']
                           if step.get('state', {}).get('path') == 'board-basic.md']
    if len(expected_text_step) != 1 or len(expected_screen_step) != 1 or len(expected_state_step) != 1:
        raise ValueError('Taskell maintenance baseline has ambiguous intended fields')
    expected_text_step[0]['text'] = 'Updated regression task'
    expected_screen_step[0]['expect'] = 'Updated regression task'
    expected_state_step[0]['bytes_base64'] = expected_updated
    if revised != expected_maintained:
        raise ValueError('Taskell selected maintenance changed unrelated spec fields')
    maintenance_report = output/'maintenance-after-update-report.json'
    await run([runner, 'test', '--report', maintenance_report.relative_to(ROOT), '--artifacts-dir',
               (output/'maintenance-after-update-artifacts').relative_to(ROOT),
               maintenance_spec.relative_to(ROOT)], 'taskell-first-public-maintained-ordinary-test')
    report_result(maintenance_report, 'passed')
    if revised_steps[0]['state']['bytes_base64'] != expected_updated:
        raise ValueError('Taskell maintenance saved bytes differ from the independently declared intended board')
    for name in ['fixtures/board-basic.md', 'bin/'+('taskell.exe' if os.name == 'nt' else 'taskell')]:
        if sha256(maintenance/name) != sha256(canonical/name):
            raise ValueError('Taskell selected maintenance changed unrelated fixture/runtime bytes')

    relocated = output/'relocated space café'
    shutil.copytree(maintenance, relocated)
    relocation_report = output/'relocation-report.json'
    await run([runner, 'test', '--report', relocation_report.relative_to(ROOT), '--artifacts-dir',
               (output/'relocation-artifacts').relative_to(ROOT),
               (relocated/'create-task.json').relative_to(ROOT)], 'taskell-first-public-unicode-relocation')
    relocation_result = report_result(relocation_report, 'passed')

    source_revision = os.environ.get('GITHUB_SHA', '')
    if len(source_revision) != 40 or any(c not in '0123456789abcdef' for c in source_revision):
        source_revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                                         capture_output=True, text=True, timeout=10).stdout.strip()
    if len(source_revision) != 40 or any(c not in '0123456789abcdef' for c in source_revision):
        raise ValueError('cannot bind generated workflow to an exact source revision')
    source = ('mkdir -p artifacts/runner-readiness-next-twenty-project-pass/active/taskell '
              '&& git clone --no-checkout https://github.com/smallhadroncollider/taskell.git '
              'artifacts/runner-readiness-next-twenty-project-pass/active/taskell/source '
              '&& git -C artifacts/runner-readiness-next-twenty-project-pass/active/taskell/source '
              'checkout --detach '+PIN)
    build_command = ('cd artifacts/runner-readiness-next-twenty-project-pass/active/taskell/source '
                     '&& stack install taskell --local-bin-path '
                     '"$GITHUB_WORKSPACE/artifacts/runner-readiness-next-twenty-project-pass/active/taskell/native-build/bin"')
    suite = 'docs/validation/runner-readiness-next-twenty-project-pass/taskell/host-contracts/taskell-create-task.json'
    generated = await run([runner, 'workflow', '--source-revision', source_revision,
                           '--os', 'macos' if platform.system() == 'Darwin' else 'linux',
                           '--suite', suite, '--setup', source, '--build', build_command, '--print'],
                          'taskell-first-public-delivered-workflow-preview')
    workflow_file = output/'delivered-workflow-preview.yml'
    workflow_file.write_text(generated['output'], encoding='utf-8', newline='\n')
    workflow_text = workflow_file.read_text(encoding='utf-8')
    if (source_revision not in workflow_text or suite not in workflow_text or source not in workflow_text or
            build_command not in workflow_text or 'pull_request:' not in workflow_text):
        raise ValueError('generated Taskell workflow omitted its source, suite, setup, build or trigger route')

    removed = []
    binary_name = 'taskell.exe' if os.name == 'nt' else 'taskell'
    for copy_root in [canonical, diagnosis, maintenance, relocated]:
        binary = copy_root/'bin'/binary_name
        if sha256(binary) != original_hash:
            raise ValueError('refuse to remove a Taskell executable whose identity changed')
        binary.unlink()
        binary.parent.rmdir()
        if binary.exists():
            raise ValueError('owned Taskell runtime removal was not confirmed')
        removed.append(dict(path=binary.relative_to(ROOT).as_posix(), sha256=original_hash, absent=True))

    receipt = dict(schema_version=1, status='public-agent-route-passed-not-admitted', project=PROJECT,
                   source_pin=PIN, candidate='v0.4.0-rc.6', runner_sha256=sha256(runner),
                   planned_sha256=sha256(output/'planned.json'), native_target_sha256=original_hash,
                   first_use_target_version=build.get('version_output'), initial_window=True,
                   shell_invocations_to_first_reviewed_ordinary_pass=3,
                   first_window_controls=len(controls), handwritten_first_use_json=False,
                   first_spec_sha256=sha256(spec), first_report_sha256=sha256(first_report),
                   first_invocation=first_result['invocation_id'],
                   diagnosis=dict(report_sha256=sha256(diagnosis_report), status='failed-as-seeded',
                                  category=failure['category'], message=failure['message']),
                   maintenance=dict(before_report_sha256=sha256(maintenance_fail_report),
                                    update_report_sha256=sha256(maintenance_report),
                                    intended_text='Updated regression task', exact_state_bytes_verified=True,
                                    unrelated_fixture_and_runtime_unchanged=True),
                   relocation=dict(path='relocated space café', report_sha256=sha256(relocation_report),
                                   invocation=relocation_result['invocation_id'], passed=True),
                   delivered_workflow=dict(source_revision=source_revision,
                                           os='macos' if platform.system() == 'Darwin' else 'linux',
                                           suite=suite, setup=source, build=build_command,
                                           preview_sha256=sha256(workflow_file), provider_run='not-dispatched',
                                           scope='Generated with the public CLI and reviewed locally; no PR or external repository mutation.'),
                   target_copy_removal=removed, attempts=attempts, human_participants=0,
                   human_time='unmeasured', assistance='Agent engineering route; no beginner inference.',
                   scope='Exact rc.6 public record/review/replay/save/test, seeded screen diagnosis, selected file-state maintenance, Unicode relocation and free-workflow preview. Admission remains gated on independent oracle, controls and complete campaign closure.')
    immutable_json(output/'receipt.json', receipt)
    print(json.dumps(dict(status=receipt['status'], output=str(output), attempts=len(attempts)), sort_keys=True))


if __name__ == '__main__':
    asyncio.run(main())
