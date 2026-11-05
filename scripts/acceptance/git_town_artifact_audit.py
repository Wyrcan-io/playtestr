"""Download and independently audit both native Git Town evidence packets."""
import argparse
import hashlib
import io
import json
import os
from pathlib import PurePosixPath
import re
import stat
import subprocess
import zipfile


REPO = 'Wyrcan-io/playtestr'
PACKAGE = 'docs/validation/runner-readiness-next-twenty-project-pass/git-town/'
RAW = 'artifacts/runner-readiness-next-twenty-project-pass/active/git-town/'
IDS = [
    'N01-hack-feature', 'N02-append-child', 'N03-read-parent',
    'N04-display-branch-hierarchy', 'N05-hack-prototype',
    'N06-prototype-existing', 'N07-feature-existing', 'N09-park-existing',
    'N11-switch-to-feature', 'N12-cancel-branch-switch',
    'N13-reject-invalid-branch-name', 'N14-reject-duplicate-branch',
    'N15-create-unicode-branch', 'N16-create-nested-branch',
    'N17-resize-cancel-selector', 'N18-rename-local-branch',
    'N19-filter-and-select-feature', 'N20-empty-filtered-switcher',
    'N21-display-offline-status', 'N22-review-configuration',
]
FAULT_SPECS = {
    'F01-parent-output': ('N03-read-parent.json', 0, 'unexpected_exit', 'internal/cmd/config/get_parent.go'),
    'F02-feature-refusal': ('N01-hack-feature.json', 1, 'unexpected_exit', 'internal/cmd/hack.go'),
    'F03-prototype-persistence': ('N06-prototype-existing.json', 0, 'state_assertion_failure', 'internal/cmd/prototype.go'),
}
ZIP_LIMIT = 512 * 1024 * 1024
EXPANDED_LIMIT = 768 * 1024 * 1024
MEMBER_LIMIT = 10000
SOURCE_PIN = '8d039892574d4852e1843020c31d423234042e78'
SOURCE_ARCHIVE_SHA256 = '2a47fe65b7f21f6a99bfeefd00dfeffce394dd7db733b47e5b87904c9947ab8a'


def digest(body):
    return hashlib.sha256(body).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def bounded_json(command, limit=2 * 1024 * 1024):
    process = subprocess.run(command, check=False, capture_output=True, timeout=45)
    if process.returncode != 0 or len(process.stdout) > limit:
        raise RuntimeError('GitHub API read failed or exceeded its response bound')
    return json.loads(process.stdout.decode('utf-8'))


def read_archive(payload):
    require(0 < len(payload) <= ZIP_LIMIT, 'provider ZIP exceeded its declared bound')
    files = {}
    expanded = 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        rows = archive.infolist()
        require(0 < len(rows) <= MEMBER_LIMIT, 'provider ZIP member count is invalid')
        for row in rows:
            name = row.filename.rstrip('/')
            if row.is_dir():
                continue
            path = PurePosixPath(name)
            require(not path.is_absolute() and name and '\\' not in name and '\x00' not in name and
                    all(part not in {'', '.', '..'} and ':' not in part for part in name.split('/')),
                    'unsafe provider ZIP member path')
            require(row.flag_bits & 1 == 0 and not stat.S_ISLNK(row.external_attr >> 16),
                    'encrypted or linked provider ZIP member')
            require(name not in files and row.file_size <= 64 * 1024 * 1024,
                    'duplicate or oversized provider ZIP member')
            expanded += row.file_size
            require(expanded <= EXPANDED_LIMIT, 'provider ZIP expansion exceeded its bound')
            body = archive.read(row)
            require(len(body) == row.file_size, 'provider ZIP member was truncated')
            files[name] = body
    return files


def value(files, name):
    require(name in files, 'required artifact member is absent: ' + name)
    return files[name]


def json_value(files, name):
    return json.loads(value(files, name).decode('utf-8-sig'))


def audit_source_archive(files, acquisition):
    archive_sha = acquisition.get('source_archive_sha256') or acquisition.get('archive_sha256')
    require(archive_sha == SOURCE_ARCHIVE_SHA256,
            'acquired pinned-source archive identity differs from the reviewed source pin')
    archive_name = RAW + 'source.tar.gz'
    archive_retained = archive_name in files
    if archive_retained:
        require(digest(files[archive_name]) == archive_sha,
                'retained pinned-source archive digest differs')
    return dict(source_archive_sha256=archive_sha,
                source_archive_payload_retained=archive_retained)


def audit_source(files):
    provenance = json_value(files, PACKAGE + 'source-provenance.json')
    require(provenance.get('pin') == SOURCE_PIN, 'Git Town source pin differs')
    expected = provenance.get('files')
    require(isinstance(expected, dict) and len(expected) == 4533,
            'pinned source manifest must enumerate all 4,533 files')
    prefix = RAW + 'src/'
    observed = {}
    for name, body in files.items():
        if not name.startswith(prefix):
            continue
        relative = name[len(prefix):]
        if '.git' in PurePosixPath(relative).parts:
            continue
        observed[relative] = digest(body)
    require(observed == expected, 'artifact source bytes differ from the complete pinned tree')
    acquisition = json_value(files, RAW + 'acquisition.json')
    archive = audit_source_archive(files, acquisition)
    return dict(pin=SOURCE_PIN, source_files=len(observed), source_tree_verified=True,
                **archive,
                source_provenance_sha256=digest(value(files, PACKAGE + 'source-provenance.json')))


def target_result(finished):
    report = finished.get('report') or {}
    results = report.get('results') or []
    require(len(results) == 1, 'case must retain one target result')
    return report, results[0]


def audit_case(files, case_id, host, expected_phase='development', expected_executable_sha256=None):
    label = f'{case_id}-{host}-{expected_phase}'
    roots = [n for n in files if n.startswith(RAW + 'case-evidence/') and n.endswith('/finished.json')]
    found = []
    for name in roots:
        finish = json.loads(files[name].decode('utf-8-sig'))
        if finish.get('label') == label:
            found.append((name, finish))
    require(len(found) == 1, 'public case must have exactly one retained execution: ' + label)
    finish_name, finished = found[0]
    require(finished.get('status') == 'completed' and finished.get('runner_attempt_id'),
            'case target launch/completion evidence is missing: ' + label)
    report, target = target_result(finished)
    report_name = str(PurePosixPath(finish_name).parent / 'report.json')
    require(finished.get('report_sha256') == digest(value(files, report_name)),
            'case report bytes differ from their recorded digest')
    started = json_value(files, str(PurePosixPath(finish_name).parent / 'started.json'))
    require(started.get('spec_sha256') == digest(value(files, PACKAGE + case_id + '.json')),
            'case did not run the exact frozen public spec: ' + label)
    if expected_executable_sha256:
        require(started.get('executable_sha256') == expected_executable_sha256,
                'case executable differs from its audited native build: ' + label)
    require(target.get('status') == 'passed' and target.get('failure') is None,
            'public scenario did not pass: ' + label)
    require(target.get('cleanup', {}).get('confirmed_exited') is True and
            target.get('workspace', {}).get('cleaned') is True,
            'public scenario process/workspace cleanup is unconfirmed: ' + label)
    spec = json_value(files, PACKAGE + case_id + '.json')
    exits = [step.get('exit') for step in spec.get('steps', [])
             if isinstance(step, dict) and 'exit' in step]
    require(len(exits)==1 and target.get('target', {}).get('exit_code') == exits[0],
            'target exit evidence differs from its frozen public contract: ' + label)
    require((target.get('steps') or []) and all(step.get('status') == 'passed' for step in target['steps']),
            'positive public-case step evidence is incomplete: ' + label)
    summary = report.get('summary') or {}
    require(summary.get('passed') == 1 and summary.get('failed') == 0 and summary.get('total') == 1 and
            summary.get('not_run') == 0 and summary.get('cancelled') == 0,
            'public-case summary differs from one passing target')
    return dict(id=case_id, label=label, spec_sha256=digest(value(files, PACKAGE + case_id + '.json')),
                report_sha256=finished.get('report_sha256'),
                runner_attempt_id=finished.get('runner_attempt_id'), target_exit_code=exits[0],
                target_exited=target['cleanup']['confirmed_exited'], workspace_cleaned=target['workspace']['cleaned'])


def audit_faults(files, host):
    matrix = json_value(files, PACKAGE + f'fault-matrix-{host}-v1.json')
    require(matrix.get('project') == 'git-town' and matrix.get('source_pin') == SOURCE_PIN,
            'fault matrix project/source binding differs')
    require(matrix.get('totals') == dict(distinct_faults=3, phases=9, baseline_passes=3,
            mutations_detected=3, restored_recovery_passes=3), 'fault matrix phase totals differ')
    faults = matrix.get('faults') or []
    require({row.get('id') for row in faults} == set(FAULT_SPECS), 'fault matrix IDs differ')
    events = []
    for name, body in files.items():
        if name.startswith(RAW + 'fault-events/') and name.endswith('.json'):
            events.append(json.loads(body.decode('utf-8-sig')))
    for fault in faults:
        fault_id = fault['id']
        spec_name, target_exit, category, source_file = FAULT_SPECS[fault_id]
        for phase, key in [('pristine-baseline', 'baseline'), ('corrupted', 'corrupted'),
                           ('restored-recovery', 'restored')]:
            case = fault.get(key) or {}
            require(case.get('phase') == phase and case.get('report_sha256'),
                    f'{fault_id} {phase} case receipt is missing')
            require(case.get('expected_runner_exit') == (1 if phase == 'corrupted' else 0),
                    f'{fault_id} {phase} runner expectation differs')
            evidence_dir = case.get('evidence_directory')
            require(isinstance(evidence_dir, str) and evidence_dir.startswith('case-evidence/'),
                    f'{fault_id} {phase} evidence path is not owned')
            receipt = json_value(files, RAW + evidence_dir + '/finished.json')
            report, target = target_result(receipt)
            require(digest(value(files, RAW + evidence_dir + '/report.json')) == case['report_sha256'],
                    f'{fault_id} {phase} report bytes differ')
            require(receipt.get('runner_attempt_id') == case.get('runner_attempt_id'),
                    f'{fault_id} {phase} runner attempt identity differs')
            require(target.get('cleanup', {}).get('confirmed_exited') is True and
                    target.get('workspace', {}).get('cleaned') is True,
                    f'{fault_id} {phase} cleanup is unconfirmed')
            require(receipt.get('spec_sha256') == digest(value(files, PACKAGE + spec_name)),
                    f'{fault_id} {phase} frozen spec identity differs')
            if phase == 'corrupted':
                require(target.get('status') == 'failed' and
                        (target.get('failure') or {}).get('category') == category,
                        f'{fault_id} unchanged contract missed its declared fault')
                if fault_id in {'F01-parent-output', 'F02-feature-refusal'}:
                    require(target.get('target', {}).get('exit_code') == target_exit,
                            f'{fault_id} corrupted target exit differs')
                if fault_id == 'F03-prototype-persistence':
                    steps = target.get('steps') or []
                    require(target.get('target', {}).get('exit_code') == target_exit and
                            [step.get('status') for step in steps] == ['passed', 'passed', 'failed'] and
                            steps[1].get('action') == 'exit', 'F03 did not fail at the same-run saved-state check')
            else:
                require(target.get('status') == 'passed' and target.get('target', {}).get('exit_code') == 0,
                        f'{fault_id} {phase} unchanged contract did not pass')
    build_rows=[]
    for name, body in files.items():
        if name.startswith(RAW + 'fault-builds/') and name.endswith('.json'):
            build_rows.append(json.loads(body.decode('utf-8-sig')))
    require(len(build_rows)==9, 'expected one native build receipt per fault phase')
    provenance=json_value(files, PACKAGE + 'source-provenance.json')['files']
    by_key={(row.get('fault_id'),row.get('phase')):row for row in build_rows}
    require(len(by_key)==9, 'fault build receipt identities are duplicated')
    executable_hashes={}
    for row in faults:
        fault_id=row['id']; _,_,_,source_file=FAULT_SPECS[fault_id]
        phases=[('pristine-baseline','baseline'),('corrupted','corrupted'),('restored-rebuild','restored')]
        for build_phase, fault_phase in phases:
            receipt=by_key.get((fault_id,build_phase))
            require(receipt is not None, f'{fault_id} {build_phase} build receipt is missing')
            require(receipt.get('pin')==SOURCE_PIN and receipt.get('network_module_resolution')=='disabled',
                    f'{fault_id} {build_phase} build identity/network policy differs')
            executable=RAW+receipt.get('executable_relative','')
            binary=value(files,executable)
            require(digest(binary)==receipt.get('executable_sha256'),
                    f'{fault_id} {build_phase} binary bytes differ from build receipt')
            source_hashes=receipt.get('source_file_sha256') or {}
            require(set(source_hashes)=={item[3] for item in FAULT_SPECS.values()},
                    f'{fault_id} {build_phase} source input hashes differ')
            expected=provenance[source_file]
            if fault_phase=='corrupted':
                expected=row.get('corrupted_source_sha256')
                require(expected and expected!=provenance[source_file], f'{fault_id} mutation did not change its exact source file')
            for path, actual_hash in source_hashes.items():
                expected_hash = expected if path == source_file and fault_phase == 'corrupted' else provenance[path]
                require(actual_hash==expected_hash, f'{fault_id} {build_phase} read unexpected source bytes: {path}')
            require(source_hashes[source_file]==expected,
                    f'{fault_id} {build_phase} source bytes do not match the reviewed phase')
            executable_hashes[fault_phase]=receipt['executable_sha256']
        for phase,key in [('pristine-baseline','baseline'),('corrupted','corrupted'),('restored-recovery','restored')]:
            case=row[key]
            case_path=RAW+case['evidence_directory']+'/started.json'
            started=json_value(files,case_path)
            require(started.get('executable_sha256')==executable_hashes[key],
                    f'{fault_id} {phase} used a different executable than its build receipt')
    required_events={(fault,phase) for fault in FAULT_SPECS for phase in
                     ('pristine-baseline','corrupted','restored-recovery')}
    observed_events={(event.get('fault_id'),event.get('phase')) for event in events
                     if event.get('status') in {'passed','unchanged contract detected source mutation',
                                                'exact source restored, rebuilt, and unchanged contract passed'}}
    require(required_events <= observed_events, 'immutable per-phase fault event coverage is incomplete')
    return dict(distinct_faults=3, phases=9, cleanup_confirmed=9,
                unchanged_contracts_detected=3, restoration_rebuilds_passed=3,
                fault_matrix_sha256=digest(value(files, PACKAGE + f'fault-matrix-{host}-v1.json')))


def curate_packet(files, host, output_path):
    """Retain audited reports and inputs while deduplicating source and omitting rebuilt binaries."""
    rows = []
    kept = 0
    with zipfile.ZipFile(output_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(files):
            reason = None
            if name.startswith(RAW + 'bin/') or name.startswith(RAW + 'fault-binaries/'):
                reason = 'binary bytes independently hashed against build and launch receipts'
            elif host == 'windows' and name.startswith(RAW + 'src/'):
                reason = 'canonical source payload retained once in Linux packet'
            elif host == 'windows' and name.startswith(PACKAGE):
                reason = 'frozen project contracts retained once in Linux packet'
            row = dict(path=name, bytes=len(files[name]), sha256=digest(files[name]), retained=reason is None)
            if reason is not None:
                row['omitted_after_independent_verification'] = reason
            else:
                archive.writestr(name, files[name])
                kept += 1
            rows.append(row)
        index = dict(schema_version=1, project='git-town', host=host,
                     source_payload_retained_in='linux' if host == 'windows' else host,
                     input_artifact_members=len(files), retained_members=kept,
                     omitted_members=len(files) - kept, members=rows)
        archive.writestr('retention-index-v1.json',
                         json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8'))
    with open(output_path, 'rb') as stream:
        packet_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    packet_bytes = os.path.getsize(output_path)
    require(packet_bytes <= 64 * 1024 * 1024,
            'curated per-host evidence packet exceeded the 64 MiB project cap')
    return dict(path=os.path.basename(output_path), sha256=packet_sha,
                bytes=packet_bytes, retained_members=kept, indexed_members=len(files))


def audit_packet(payload, host, run_id, expected_head, retention_root):
    files = read_archive(payload)
    common = audit_source(files)
    build=json_value(files,RAW+'build.json')
    binary=value(files,RAW+build['binary_relative_path'])
    require(digest(binary)==build.get('binary_sha256'),'initial native target executable differs from its build receipt')
    public = [audit_case(files, case_id, host, expected_executable_sha256=build['binary_sha256'])
              for case_id in IDS]
    require(len({case['id'] for case in public}) == 20, 'public suite identity count differs')
    source = json_value(files, RAW + 'task-owned.json')
    require((source.get('project') == 'git-town' or source.get('slug') == 'git-town') and source.get('pin') == SOURCE_PIN,
            'campaign-owned target identity differs')
    matrix = audit_faults(files, host)
    retained = curate_packet(files, host, os.path.join(retention_root, f'retained-{host}-v1.zip'))
    return dict(host=host,artifact_members=len(files),expanded_bytes=sum(map(len, files.values())),
                public_cases=public,public_case_count=len(public),source=common,faults=matrix,
                retained_packet=retained,
                task_owned_sha256=digest(value(files, RAW + 'task-owned.json')),
                run_id=str(run_id),head_sha=expected_head)


def get_bytes(command, limit):
    env = dict(os.environ)
    env['GH_TOKEN'] = os.environ['GITHUB_TOKEN']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    chunks = bytearray()
    try:
        while True:
            block = process.stdout.read(min(65536, limit + 1 - len(chunks)))
            if not block:
                break
            chunks.extend(block)
            if len(chunks) > limit:
                raise ValueError('GitHub response exceeded the declared byte bound')
        error = process.stderr.read(8192)
        if process.wait(timeout=15) != 0:
            raise RuntimeError('bounded GitHub artifact acquisition failed: ' + error.decode('utf-8', 'replace')[-1024:])
        return bytes(chunks)
    finally:
        if process.poll() is None:
            process.kill(); process.wait(timeout=10)
        process.stdout.close(); process.stderr.close()


def acquire(run_id, expected_head):
    require(re.fullmatch(r'[0-9]{1,20}', str(run_id)) is not None and
            re.fullmatch(r'[0-9a-f]{40}', expected_head) is not None,
            'audit request run/head identity is malformed')
    run = json.loads(get_bytes(['gh','api',f'repos/{REPO}/actions/runs/{run_id}'], 512*1024))
    require(run.get('head_sha') == expected_head and run.get('head_branch') == 'work/p0-p2-implementation' and
            run.get('status') == 'completed' and run.get('conclusion') == 'success',
            'native provider run/source/conclusion differs from the reviewed request')
    jobs = json.loads(get_bytes(['gh','api',f'repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100'], 2*1024*1024))
    required_jobs = {'native-development (linux, ubuntu-24.04)',
                     'native-development (windows, windows-2025)'}
    successful_jobs = {job['name'] for job in jobs.get('jobs', []) if job.get('conclusion') == 'success'}
    require(required_jobs <= successful_jobs, 'native provider lacks a successful Linux/Windows job')
    artifacts = json.loads(get_bytes(['gh','api',f'repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100'], 512*1024))
    rows = [row for row in artifacts.get('artifacts', []) if not row.get('expired')]
    packets = {}
    for host in ('linux','windows'):
        name = f'next20-git-town-{host}-development'
        matches = [row for row in rows if row.get('name') == name]
        require(len(matches) == 1, 'native provider artifact is missing/ambiguous: ' + host)
        row = matches[0]
        size = row.get('size_in_bytes')
        require(isinstance(size, int) and 0 < size <= ZIP_LIMIT, 'provider artifact size is out of bounds')
        payload = get_bytes(['gh','api',f'repos/{REPO}/actions/artifacts/{row["id"]}/zip'], ZIP_LIMIT)
        expected_digest = (row.get('digest') or '').removeprefix('sha256:')
        require(len(payload) == size and digest(payload) == expected_digest,
                'provider artifact ZIP size/digest differs from GitHub metadata')
        packets[host] = (row, payload)
    return run, packets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    request = json.load(open(args.request, encoding='utf-8'))
    require(request.get('schema_version') == 1 and request.get('project') == 'git-town',
            'audit request schema/project differs')
    require(os.environ.get('GITHUB_TOKEN'), 'workflow token is unavailable')
    run, packets = acquire(request['run_id'], request['expected_head_sha'])
    result = dict(schema_version=1, project='git-town', run_id=str(run['id']),
        head_sha=run['head_sha'], conclusion=run['conclusion'], source_fault_credit=0,
        native_cells=[], audit_method='Separate GitHub-hosted Linux audit job downloaded both original artifact ZIPs, verified provider size/SHA-256, then independently checked exact source, public reports, fault reports, target exits and cleanup.')
    for host, (artifact, payload) in packets.items():
        cell = audit_packet(payload, host, run['id'], run['head_sha'], os.path.dirname(args.output))
        cell['artifact_id'] = artifact['id']
        cell['artifact_sha256'] = digest(payload)
        cell['artifact_bytes'] = len(payload)
        result['native_cells'].append(cell)
        del payload
    result['all_native_packets_passed'] = len(result['native_cells']) == 2
    result['all_packets_share_source_pin'] = all(cell['source']['pin'] == SOURCE_PIN for cell in result['native_cells'])
    result['all_packets_share_archive_and_provenance'] = (
        len({cell['source']['source_archive_sha256'] for cell in result['native_cells']}) == 1 and
        len({cell['source']['source_provenance_sha256'] for cell in result['native_cells']}) == 1)
    result['all_packets_share_frozen_specs'] = (
        len({tuple((case['id'], case['spec_sha256']) for case in cell['public_cases'])
             for cell in result['native_cells']}) == 1)
    require(result['all_native_packets_passed'] and result['all_packets_share_source_pin'],
            'independent native artifact audit is incomplete')
    require(result['all_packets_share_archive_and_provenance'] and result['all_packets_share_frozen_specs'],
            'Linux and Windows artifacts do not share exact source and scenario contracts')
    require(sum(cell['retained_packet']['bytes'] for cell in result['native_cells']) <= 64 * 1024 * 1024,
            'combined retained Git Town evidence exceeds the 64 MiB project cap')
    with open(args.output, 'x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('GIT_TOWN_INDEPENDENT_AUDIT=' + json.dumps(result, ensure_ascii=True, separators=(',', ':')))


if __name__ == '__main__':
    main()

