"""Exercise public maintenance against actual compiled peco output changes."""
import asyncio
import base64
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

from adversarial_process import execute
from next20_candidate import executable
from next20_cargo_faults import NativeFaultCampaign
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_python_setup import environment
from readiness_build_rclone import environment as build_environment
from readiness_evidence import immutable_json, sha256


async def main():
    if os.name != 'nt':
        raise ValueError('this maintenance window is explicitly native Windows')
    canonical = DOC/'peco'
    target = RAW/'active/peco'
    runner = executable('native-exit-v1')
    runtime = json.loads((target/'runtime.json').read_text())
    build = json.loads((target/'build.json').read_text())
    review = json.loads((canonical/'dependency-source-review-declaration.json').read_text())
    fetch = json.loads((target/'module-fetch.json').read_text())
    primary = json.loads((canonical/'source-provenance.json').read_text())['files']
    catalog = json.loads((target/'dependency-source-catalog.json').read_text())
    package_inputs = json.loads((target/'native-package-inputs.json').read_text())
    app = Path(runtime['target'])
    capture = Path(runtime['native'])
    source = target/'src/peco.go'
    original = source.read_bytes()
    anchor = b'buf.WriteString(line.Output())'
    if original.count(anchor) != 1:
        raise ValueError('selected-output writer anchor is not unique')
    root = RAW/'peco'/('maintenance-'+uuid.uuid4().hex)
    package = root/'reviewed route'
    package.mkdir(parents=True)
    variants = target/'maintenance-builds'/root.name
    variants.mkdir(parents=True)
    backup = variants/('original-'+app.name)
    shutil.copyfile(app, backup)
    baseline_metadata = {p: sha256(p) for p in [target/'runtime.json', target/'build.json', target/'installed-inventory.json']}
    shutil.copytree(canonical/'fixture', package/'fixture')
    shutil.copytree(canonical/'snapshots', package/'snapshots')
    snapshot = package/'snapshots/normal-selection.txt'
    snapshot_hash = sha256(snapshot)
    approved = json.loads((canonical/'normal-selection.json').read_text())
    approved['command'][0] = os.path.relpath(capture, package).replace('\\', '/')
    spec = package/'maintained.json'
    immutable_json(spec, approved)
    index = next(i for i, s in enumerate(approved['steps']) if s.get('state', {}).get('path') == 'selected.txt')
    selected = base64.b64decode(approved['steps'][index]['state']['bytes_base64'], validate=True)
    if selected != b'beta draft\n':
        raise ValueError('unexpected independent original selected bytes')
    immutable_json(root/'planned.json', dict(schema_version=1, canonical_spec_sha256=sha256(canonical/'normal-selection.json'),
        intended_selected_utf8='Reviewed: beta draft\n', cancelled_selected_utf8='Cancelled: beta draft\n',
        diagnosis_selected_utf8='wrong:beta draft\n', suffix_selected_utf8='gamma release\n', selected_state_number=index+1,
        source_and_binary_restoration_required=True, scope='Prepared-agent public maintenance with three actual source-compiled output variants. No beginner timing or final qualification credit.'))
    env = environment(target)
    build_env = build_environment(target)
    build_env.update(GOENV='off', GOPROXY='off', GOSUMDB='off', GONOPROXY='none', GONOSUMDB='none')
    attempts = []
    reports = []
    campaign = NextCampaign()

    def verify(changed=False):
        for name, digest in primary.items():
            if name != 'peco.go' or not changed:
                if sha256(target/'src'/name) != digest:
                    raise ValueError('primary source restoration differs')
        for name, digest in catalog['files'].items():
            if not name.startswith('src/') and sha256(target/name) != digest:
                raise ValueError('reviewed Go module source changed')
        if any(sha256(p) != digest for p, digest in baseline_metadata.items()) or sha256(capture) != build['binary_sha256']:
            raise ValueError('immutable pristine metadata/capture changed')
        if sha256(fetch['compiler']) != build['compiler_sha256'] or any(sha256(p) != digest for p, digest in build['compiler_tools'].items()):
            raise ValueError('reviewed native compiler tools changed')
        if sha256(target/'build-inputs/pinned.mod') != package_inputs['go_mod_sha256'] or sha256(target/'build-inputs/pinned.sum') != package_inputs['go_sum_sha256']:
            raise ValueError('reviewed effective module inputs changed')
        if not changed and sha256(app) != build['actual_target_sha256']:
            raise ValueError('ordinary target binary not restored')

    async def run(argv, label, expected=0, input=None):
        result = await execute(argv, 'peco', label, cwd=ROOT, env=env, timeout=180, expected=expected, input=input, campaign=campaign)
        attempts.append(dict(id=result['id'], label=label, seconds=result['seconds']))
        return result

    async def test(path, label, expected=0):
        report = root/(label+'.report.json')
        await run([runner, 'test', '--report', report.relative_to(ROOT), '--artifacts-dir', (root/(label+'-evidence')).relative_to(ROOT), path.relative_to(ROOT)], label, expected)
        row = json.loads(report.read_text())['results'][0]
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:
            raise ValueError('maintenance target/workspace cleanup incomplete')
        if expected == 0 and (row['status'] != 'passed' or any(s['status'] != 'passed' for s in row['steps'])):
            raise ValueError('maintenance positive case incomplete')
        reports.append(dict(label=label, report=report.relative_to(ROOT).as_posix(), sha256=sha256(report), invocation=row['invocation_id'], category=row.get('failure', {}).get('category')))
        return report, row

    compiled = {}
    verify()
    for name, prefix in [('diagnosis', 'wrong:'), ('reviewed', 'Reviewed: '), ('cancelled', 'Cancelled: ')]:
        variant = variants/(name+'-'+app.name)
        receipt = root/(name+'-compiled.json')
        modified = original.replace(anchor, ('buf.WriteString('+json.dumps(prefix)+' + line.Output())').encode())
        try:
            source.write_bytes(modified)
            verify(True)
            command = [fetch['compiler'], 'build', *review['build_flags'], '-modfile='+str(target/'build-inputs/pinned.mod'), '-o', str(variant), review['main_package']]
            result = await execute(command, 'peco', 'peco-maintenance-compile-'+name, cwd=target/'src', env=build_env, timeout=180, campaign=NextCampaign())
            inputs = {(target/'src'/p).relative_to(ROOT).as_posix(): sha256(target/'src'/p) for p in primary}
            inputs.update({(target/p).relative_to(ROOT).as_posix(): sha256(target/p) for p in catalog['actual_native_compile_inputs']})
            inputs[capture.relative_to(ROOT).as_posix()] = sha256(capture)
            for module_name in ['pinned.mod', 'pinned.sum']:
                inputs[(target/'build-inputs'/module_name).relative_to(ROOT).as_posix()] = sha256(target/'build-inputs'/module_name)
            immutable_json(receipt, dict(schema_version=1, compile_attempt=result['id'], command=command, binary=variant.relative_to(ROOT).as_posix(),
                binary_sha256=sha256(variant), source_inputs=inputs, compiler_sha256=build['compiler_sha256'], compiler_tools=build['compiler_tools'],
                dependency_source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),
                pristine_build_sha256=sha256(target/'build.json'), changed_source='src/peco.go', changed_source_sha256=sha256(source), intended_prefix=prefix))
            compiled[name] = (variant, receipt, modified)
        finally:
            source.write_bytes(original)
            verify()

    def activate(name):
        nonlocal campaign
        variant, receipt, modified = compiled[name]
        source.write_bytes(modified)
        shutil.copyfile(variant, app)
        verify(True)
        campaign = NativeFaultCampaign(app, receipt, [spec, snapshot, root/'planned.json'])

    def restore():
        nonlocal campaign
        source.write_bytes(original)
        shutil.copyfile(backup, app)
        verify()
        campaign = NextCampaign()

    try:
        activate('diagnosis')
        report, row = await test(spec, 'peco-diagnosis-real-selected-output', 1)
        if row['failure']['category'] != 'state_assertion_failure' or not all(s['status'] == 'passed' for s in row['steps'][:index]):
            raise ValueError('saved-output fault not behind positive UI/snapshot/exact exit')
        html = root/'diagnosis.html'
        await run([runner, 'report', '--input', report.relative_to(ROOT), '--evidence-root', root.relative_to(ROOT), '--output', html.relative_to(ROOT)], 'peco-diagnosis-offline-html')
        if 'state_assertion_failure' not in html.read_text(encoding='utf-8') or 'selected.txt' not in html.read_text(encoding='utf-8'):
            raise ValueError('useful saved-file diagnosis missing')
        restore()
        await test(spec, 'peco-diagnosis-restored-recovery')
        activate('reviewed')
        _, row = await test(spec, 'peco-maintenance-intended-prefix', 1)
        if row['failure']['category'] != 'state_assertion_failure' or not all(s['status'] == 'passed' for s in row['steps'][:index]):
            raise ValueError('intended output change not isolated')
        await run([runner, 'record', '--edit', spec.relative_to(ROOT)], 'peco-maintenance-selected-update', input=f'/update-state {index+1}\n/review\n/replay\n/save\n')
        expected = copy.deepcopy(approved)
        expected['steps'][index]['state']['bytes_base64'] = base64.b64encode(b'Reviewed: beta draft\n').decode()
        if json.loads(spec.read_text()) != expected or sha256(snapshot) != snapshot_hash:
            raise ValueError('selected update changed unrelated approvals or unexpected bytes')
        await test(spec, 'peco-maintenance-selected-replay')
        saved = spec.read_bytes()
        activate('cancelled')
        await run([runner, 'record', '--edit', spec.relative_to(ROOT)], 'peco-maintenance-cancelled-update', 130, input=f'/update-state {index+1}\n/quit\n')
        if spec.read_bytes() != saved or sha256(snapshot) != snapshot_hash:
            raise ValueError('cancelled update changed approved bytes')
        activate('reviewed')
        await test(spec, 'peco-maintenance-cancel-restored-replay')
        relocated = root/'relocated caf\u00e9 \u96ea'
        shutil.copytree(package, relocated)
        if sha256(relocated/spec.name) != sha256(spec):
            raise ValueError('relocation changed maintained spec')
        await test(relocated/spec.name, 'peco-relocated-maintained')
    finally:
        restore()

    suffix = package/'suffix.json'
    controls = ['/expect gamma release', '/expect alpha notes', '/text "beta"', '/expect Select> beta', '/absent alpha notes',
        '/snapshot discarded-beta.txt', '/key Enter', '/exit 0', '/rerecord 2', '/text "gamma"', '/expect Select> gamma', '/absent alpha notes',
        '/snapshot replacement-gamma.txt', '/key Enter', '/exit 0', '/file selected.txt', '/file candidates.txt', '/file config.json', '/file sentinel.txt', '/entries .', '/review', '/replay', '/save']
    argv = [runner, 'record', '--output', suffix.relative_to(ROOT), '--fixture', 'fixture', '--temporary-home', '--temporary-temp',
        '--width', '100', '--height', '24', '--timeout-ms', '10000', '--run-timeout-ms', '120000']
    for name, value in approved['env'].items():
        argv += ['--env', name+'='+value]
    argv += ['--', *approved['command']]
    await run(argv, 'peco-maintenance-fresh-suffix-rerecord', input='\n'.join(controls+['']))
    rerecorded = json.loads(suffix.read_text())
    state = next(s['state'] for s in rerecorded['steps'] if s.get('state', {}).get('path') == 'selected.txt')
    if base64.b64decode(state['bytes_base64'], validate=True) != b'gamma release\n' or any(s.get('text') == 'beta' or s.get('snapshot') == 'discarded-beta.txt' for s in rerecorded['steps']):
        raise ValueError('rerecord retained discarded suffix or wrong selected bytes')
    if (package/'snapshots/discarded-beta.txt').exists():
        raise ValueError('rerecord exported discarded candidate snapshot')
    await test(suffix, 'peco-maintenance-suffix-ordinary')
    shutil.copyfile(suffix, relocated/'suffix.json')
    shutil.copyfile(package/'snapshots/replacement-gamma.txt', relocated/'snapshots/replacement-gamma.txt')
    await test(relocated/'suffix.json', 'peco-relocated-suffix')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    workflow = root/'generated-workflow.yml'
    await run([runner, 'workflow', '--source-revision', revision, '--os', 'linux', '--suite', 'artifacts/'+RAW.name+'/peco/host-contracts/normal-selection.json',
        '--build', 'python -B scripts/acceptance/next20_go_native_prepare.py --project peco', '--output', workflow.relative_to(ROOT)], 'peco-public-free-workflow-generation')
    verify()
    for name, digest in json.loads((canonical/'development-test-freeze.json').read_text())['inputs'].items():
        if sha256(canonical/name) != digest:
            raise ValueError('canonical frozen input changed')
    immutable_json(root/'journey.json', dict(schema_version=1, attempts=attempts, reports=reports, runner_sha256=sha256(runner),
        diagnostic_commands=2, html_sha256=sha256(html), selected_state_number=index+1, selected_update_controls=4, cancelled_update_controls=2,
        unrelated_approved_bytes_preserved=True, snapshot_sha256=snapshot_hash, suffix_controls=len(controls), suffix_sha256=sha256(suffix),
        maintained_spec_sha256=sha256(spec), relocated_spec_sha256=sha256(relocated/spec.name), generated_workflow_sha256=sha256(workflow), workflow_dispatched=False,
        source_restored=True, binary_restored=True, compiled_variants={name: sha256(value[1]) for name, value in compiled.items()},
        human_time='unmeasured', human_participants=0, project_admissions=0, final_ordinary_credit=0))
    print('Peco compiled-fault diagnosis, selected/cancelled updates, suffix rerecord, Unicode relocation and workflow generation passed; exact source/binary restored.')


if __name__ == '__main__':
    asyncio.run(main())
