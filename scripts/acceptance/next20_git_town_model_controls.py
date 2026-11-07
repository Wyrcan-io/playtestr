"""Reconstruct and tamper-test Git Town's audited exact-candidate cell models."""
import copy
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import uuid
import zipfile

from readiness_evidence import immutable_json, sha256

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'artifacts/runner-readiness-next-twenty-project-pass'
DOC = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass'
AUDIT = DOC / 'git-town/final-series-audit-v20.json'
CASES = {
    'N01-hack-feature', 'N02-append-child', 'N03-read-parent',
    'N04-display-branch-hierarchy', 'N05-hack-prototype', 'N06-prototype-existing',
    'N07-feature-existing', 'N09-park-existing', 'N11-switch-to-feature',
    'N12-cancel-branch-switch', 'N13-reject-invalid-branch-name',
    'N14-reject-duplicate-branch', 'N15-select-unicode-branch',
    'N16-create-nested-branch', 'N17-resize-cancel-selector',
    'N18-rename-local-branch', 'N19-filter-and-select-feature',
    'N20-empty-filtered-switcher', 'N21-display-offline-status',
    'N22-review-configuration',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_member(name):
    path = PurePosixPath(name)
    return (name and '\\' not in name and '\x00' not in name and not path.is_absolute()
            and all(part not in {'', '.', '..'} and ':' not in part for part in name.split('/')))


def packet_model(host, cell, audit, declaration, retained_cell):
    packet = RAW / retained_cell['retained_packet']
    require(packet.is_file() and sha256(packet) == retained_cell['retained_sha256'], 'curated retained packet identity differs')
    require(packet.stat().st_size == retained_cell['retained_bytes'], 'curated retained packet size differs')
    model = dict(schema_version=1, project='git-town', repository='git-town/git-town',
        pin='8d039892574d4852e1843020c31d423234042e78', candidate='v0.4.0-rc.6',
        host=host, artifact_sha256=cell['artifact_sha256'], artifact_bytes=cell['artifact_bytes'],
        archive_sha256=cell['candidate_archive_sha256'], runner_sha256=cell['runner_sha256'],
        source_archive_sha256=cell['source_archive_sha256'], source_files=cell['source_files_verified'],
        fault_matrix_sha256=cell['fault_matrix_sha256'], normal_scenarios=8, edge_scenarios=12,
        ordinary=[], fault_phases=9,
        fault_calibrations=9, distinct_faults=3, source_restored_exact=cell['source_restored_exact'])
    seen_names = set()
    with zipfile.ZipFile(packet) as archive:
        infos = archive.infolist()
        require(len(infos) <= 10000, 'retained member count exceeds cap')
        require(archive.testzip() is None, 'provider ZIP CRC validation failed')
        retention_bytes = archive.read('retention-index-v1.json')
        require(digest(retention_bytes) == retained_cell['retention_index_sha256'], 'retention index digest differs')
        retention = json.loads(retention_bytes)
        require(retention['provider_archive_sha256'] == cell['artifact_sha256'] and
                retention['provider_members'] == cell['artifact_members'] and
                len(retention['members']) == cell['artifact_members'], 'original provider identity/index differs')
        original = {item['path']: item for item in retention['members']}
        require(len(original) == cell['artifact_members'] and
                sum(item['bytes'] for item in original.values()) == cell['expanded_bytes'],
                'complete provider path/size inventory differs')
        retained_names = {name for name in archive.namelist() if name != 'retention-index-v1.json'}
        expected_retained = {name for name, item in original.items() if item['retained'] is True}
        require(retained_names == expected_retained, 'curated members differ from retention index')
        for name, item in original.items():
            require(safe_member(name) and len(item['sha256']) == 64 and item['bytes'] <= 64 * 1024 * 1024,
                    'unsafe or malformed original packet index member')
            if item['retained']:
                body = archive.read(name)
                require(len(body) == item['bytes'] and digest(body) == item['sha256'],
                        'retained packet member differs from the complete original-provider index')
        seen_names = retained_names
        base = 'artifacts/runner-readiness-next-twenty-project-pass/git-town/final-series-native-exit-v1/'
        root = 'artifacts/runner-readiness-next-twenty-project-pass/git-town/'
        build = json.loads(archive.read(root + 'retained-source/build.json'))
        require(build['build_succeeded'] is True and build['build_hooks_executed'] is False and
                build['pin'] == model['pin'] and build['host_os'] == host,
                'native target build receipt identity differs')
        baseline_binaries = [n for n in seen_names if n.startswith(root + 'retained-source/fault-binaries/F01-parent-output-pristine-') and n.endswith('/git-town' if host == 'linux' else '/git-town.exe')]
        indexed_binaries = [name for name in original if name.startswith(root + 'retained-source/fault-binaries/F01-parent-output-pristine-') and name.endswith('/git-town' if host == 'linux' else '/git-town.exe')]
        require(len(baseline_binaries) == 0 and len(indexed_binaries) == 1 and
                original[indexed_binaries[0]]['sha256'] == build['binary_sha256'] and
                original[indexed_binaries[0]]['retained'] is False,
                'omitted pristine binary does not match independently audited build hash/index')
        model.update(target_binary_sha256=build['binary_sha256'], target_build_go_version=build['go_version'])
        cell['target_binary_sha256'] = build['binary_sha256']
        summary = json.loads(archive.read(root + 'final-execution-summary.json'))
        require(summary['host'] == host and summary['ordinary_executions'] == 240 and summary['calibrations'] == 9,
                'final execution summary identity/count differs')
        require(summary['candidate_sha256'] == cell['runner_sha256'] and summary['project_admissions'] == 0,
                'final execution summary candidate/admission differs')
        for batch in range(12):
            summary_path = f'{base}{batch}/summary.json'
            summary_bytes = archive.read(summary_path)
            require(digest(summary_bytes) == summary['batches'][f'git-town/final-series-native-exit-v1/{batch}/summary.json'],
                    'summary index hash differs')
            batch_summary = json.loads(summary_bytes)
            require(batch_summary['host'] == host and batch_summary['batch'] == batch and
                    batch_summary['new_project_admissions'] == 0, 'batch identity differs')
            observations = batch_summary['observations']
            require(len(observations) == 20 and {o['case'] for o in observations} == CASES,
                    'batch case coverage differs')
            for observation in observations:
                case = observation['case']
                planned_path = f'{base}{batch}/{case}.planned.json'
                report_path = f'{base}{batch}/{case}.report.json'
                planned_bytes = archive.read(planned_path)
                report_bytes = archive.read(report_path)
                planned = json.loads(planned_bytes)
                report = json.loads(report_bytes)
                require(digest(report_bytes) == observation['report_sha256'] and
                        observation['spec_sha256'] == planned['spec_sha256'],
                        'report or executed contract hash differs')
                require(planned['case'] == case and planned['batch'] == batch and planned['host'] == host and
                        planned['phase'] == 'final-archive' and planned['archive_sha256'] == cell['candidate_archive_sha256'] and
                        planned['runner_sha256'] == cell['runner_sha256'], 'planned invocation identity differs')
                require(observation['passed'] is True and report['summary']['passed'] == 1 and
                        report['summary']['failed'] == 0 and report['summary']['cancelled'] == 0 and
                        len(report['results']) == 1, 'ordinary execution was not a positive pass')
                result = report['results'][0]
                cleanup = result['cleanup']
                require(result['status'] == 'passed' and cleanup['confirmed_exited'] is True,
                        'ordinary target result/cleanup is not positive')
                invocation = result['invocation_id']
                require(invocation == observation['invocation'] and invocation,
                        'ordinary invocation identity differs')
                model['ordinary'].append(dict(batch=batch, case=case, invocation=invocation,
                    planned_sha256=digest(planned_bytes), report_sha256=digest(report_bytes),
                    contract_sha256=planned['spec_sha256'], archive_sha256=planned['archive_sha256'],
                    runner_sha256=planned['runner_sha256'], phase=planned['phase'],
                    passed=result['status'] == 'passed', confirmed_exited=cleanup['confirmed_exited']))
    require(len(model['ordinary']) == 240, 'incomplete reconstructed ordinary matrix')
    return model


def validate(model, host, cell):
    require(model['project'] == 'git-town' and model['repository'] == 'git-town/git-town' and
            model['pin'] == '8d039892574d4852e1843020c31d423234042e78', 'canonical project identity differs')
    require(model['candidate'] == 'v0.4.0-rc.6' and model['host'] == host, 'candidate or native host differs')
    require(model['artifact_sha256'] == cell['artifact_sha256'] and model['artifact_bytes'] == cell['artifact_bytes'] and
            model['archive_sha256'] == cell['candidate_archive_sha256'] and model['runner_sha256'] == cell['runner_sha256'],
            'provider/candidate identity differs')
    require(model['target_binary_sha256'] == cell['target_binary_sha256'] and model['target_build_go_version'],
            'native target build identity differs')
    require(model['source_archive_sha256'] == cell['source_archive_sha256'] and model['source_files'] == 4533 and
            model['source_restored_exact'] is True, 'pinned source or restoration evidence differs')
    require(model['fault_matrix_sha256'] == cell['fault_matrix_sha256'] and model['distinct_faults'] == 3 and
            model['fault_phases'] == 9 and model['fault_calibrations'] == 9, 'fault/calibration matrix differs')
    require(model['normal_scenarios'] == 8 and model['edge_scenarios'] == 12,
            'normal/edge scenario partition differs')
    rows = model['ordinary']
    require(len(rows) == 240, 'ordinary matrix is incomplete')
    invocations = set()
    for batch in range(12):
        current = [r for r in rows if r['batch'] == batch]
        require(len(current) == 20 and {r['case'] for r in current} == CASES, 'scenario coverage missing/duplicated')
        for row in current:
            require(row['phase'] == 'final-archive' and row['archive_sha256'] == model['archive_sha256'] and
                    row['runner_sha256'] == model['runner_sha256'] and row['passed'] and row['confirmed_exited'],
                    'mixed phase/candidate or nonpositive ordinary result')
            require(all(len(row[k]) == 64 for k in ('planned_sha256', 'report_sha256', 'contract_sha256')),
                    'malformed immutable report/contract identity')
            require(row['invocation'] not in invocations, 'duplicate execution identity')
            invocations.add(row['invocation'])
    require(len(invocations) == 240, 'ordinary execution identity count differs')
    return dict(canonical_scenarios=20, native_cells=1, ordinary=240, calibrations=9,
                distinct_real_faults=3, all_ordinary_positive=True)


def main():
    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    declaration = json.loads((DOC / 'git-town/final-series-declaration-native-exit-v20.json').read_text(encoding='utf-8'))
    require(audit['run_id'] == '41994487910' and audit['run_conclusion'] == 'success' and
            audit['candidate'] == 'v0.4.0-rc.6/native-exit-v1', 'independent final audit identity differs')
    require(audit['qualification_credit']['project_admission'] is False, 'do not mutate the admitted final audit receipt')
    output = RAW / 'git-town/audit-controls' / ('v20-reconstructed-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    cells = []
    controls = []
    retained_readback = json.loads((RAW / 'retained/git-town-final-v20-v2/readback-v1.json').read_text(encoding='utf-8'))
    retained_hosts = {item['host']: item for item in retained_readback['hosts']}
    for cell in audit['hosts']:
        host = cell['host']
        model = packet_model(host, cell, audit, declaration, retained_hosts[host])
        baseline = validate(model, host, cell)
        patches = [
                ('wrong-project', ['project'], 'jrnl'),
                ('wrong-repository', ['repository'], 'git-town/fork'),
                ('wrong-source-pin', ['pin'], '0' * 40),
                ('mixed-candidate', ['candidate'], 'v0.4.0-rc.5'),
                ('wrong-host', ['host'], 'macos'),
                ('missing-scenario', ['ordinary'], model['ordinary'][:-1]),
                ('wrong-phase', ['ordinary', 0, 'phase'], 'development'),
                ('false-green', ['ordinary', 0, 'passed'], False),
                ('duplicate-invocation', ['ordinary', 1, 'invocation'], model['ordinary'][0]['invocation']),
                ('unconfirmed-cleanup', ['ordinary', 0, 'confirmed_exited'], False),
                ('missing-fault-calibration', ['fault_calibrations'], 0),
                ('altered-retained-artifact', ['artifact_sha256'], '0' * 64),
        ]
        for name, path, replacement in patches:
            altered = copy.deepcopy(model)
            parent = altered
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = replacement
            try:
                validate(altered, host, cell)
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                controls.append(dict(host=host, control=name, rejected=True, reason=str(exc), path=path,
                    mutation='truncate' if name == 'missing-scenario' else 'replace',
                    value=len(replacement) if name == 'missing-scenario' else replacement))
            else:
                raise ValueError('tampered actual Git Town model was accepted: ' + host + ' ' + name)
        encoded = json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('utf-8')
        packed = lzma.compress(encoded, preset=6)
        model_path = output / f'{host}-actual-model.json.xz'
        model_path.write_bytes(packed)
        restored = json.loads(lzma.decompress(packed, memlimit=64 * 1024 * 1024))
        require(restored == model and validate(restored, host, cell) == baseline, 'positive model roundtrip failed')
        cells.append(dict(host=host, run_id=audit['run_id'], source_revision=audit['head_sha'],
            candidate_archive_sha256=cell['candidate_archive_sha256'], runner_sha256=cell['runner_sha256'],
            target_binary_sha256=cell['target_binary_sha256'],
            execution_host='ubuntu-24.04' if host == 'linux' else 'windows-2025',
            counts=baseline, model=model_path.relative_to(RAW).as_posix(),
            model_sha256=sha256(model_path), model_bytes=len(encoded)))
    result = dict(schema_version=1, project='git-town', source_audit='git-town/final-series-audit-v20.json',
        run_id=audit['run_id'], candidate=audit['candidate'], cells=cells, controls=controls,
        controls_count=len(controls), application_scenario_credit=0, new_project_credit=0,
        scope='Reconstructible exact-candidate cell-model controls over the verified original V20 provider packets. No campaign admission is issued until this receipt and ledger cross-check are independently reviewed.')
    immutable_json(output / 'results.json', result)
    print('Git Town model controls passed:', len(controls), 'tamper rejections; two actual cell models restored and positive.')


if __name__ == '__main__':
    main()
