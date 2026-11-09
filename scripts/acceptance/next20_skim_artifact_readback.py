"""Independently read back one provider Skim native artifact."""
import argparse
import hashlib
import json
import ntpath
from pathlib import Path, PurePosixPath
import posixpath
import zipfile

from next20_skim_final_plan_audit import reconstruct as reconstruct_skim


ROOT = 'artifacts/runner-readiness-next-twenty-project-pass/skim/'
DOC = 'docs/validation/runner-readiness-next-twenty-project-pass/skim/'
MAX_MEMBER = 256 * 1024**2
MAX_TOTAL = 2 * 1024**3


def digest(data):
    return hashlib.sha256(data).hexdigest()


def find_hash_bound_document(payloads, prefix, expected_sha256):
    """Select one declared campaign document by its frozen content hash."""
    matches = [(name, data) for name, data in payloads.items()
               if name.startswith(DOC + prefix) and name.endswith('.json') and
               digest(data) == expected_sha256]
    if len(matches) != 1:
        raise ValueError('artifact lacks one uniquely hash-bound document: ' + prefix)
    name, data = matches[0]
    return name[len(DOC):], data


def audit(archive, provider_sha256, provider_bytes, host, run_id, revision, freeze_path):
    archive = Path(archive)
    raw_digest = hashlib.sha256()
    with archive.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            raw_digest.update(block)
    if archive.stat().st_size != provider_bytes or raw_digest.hexdigest() != provider_sha256:
        raise ValueError('retrieved ZIP differs from provider artifact bytes/digest')

    with zipfile.ZipFile(archive) as stream:
        infos = stream.infolist()
        names = [row.filename for row in infos]
        if len(names) != len(set(names)):
            raise ValueError('artifact contains duplicate ZIP paths')
        total = 0
        payloads = {}
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or info.flag_bits & 1:
                raise ValueError('artifact contains unsafe or encrypted ZIP member')
            if info.file_size > MAX_MEMBER:
                raise ValueError('artifact member exceeds bounded readback size')
            total += info.file_size
            if total > MAX_TOTAL:
                raise ValueError('artifact expanded size exceeds bounded readback size')
            if not info.is_dir():
                payload = stream.read(info)
                if len(payload) != info.file_size:
                    raise ValueError('short ZIP member read')
                payloads[name] = payload
        if stream.testzip() is not None:
            raise ValueError('ZIP CRC validation failed')

    def get(suffix):
        path = ROOT + suffix
        if path not in payloads:
            raise ValueError('artifact member missing: ' + path)
        return payloads[path]

    def obj(suffix):
        try:
            value = json.loads(get(suffix))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError('invalid UTF-8 JSON member: ' + suffix) from error
        if not isinstance(value, dict):
            raise ValueError('JSON evidence is not an object: ' + suffix)
        return value

    def doc(name):
        path = DOC + name
        if path not in payloads:
            raise ValueError('artifact documentation member missing: ' + path)
        return payloads[path]

    suffix = 'final-series-native-exit-v1/' + host + '/'
    build = obj('retained-source/build.json')
    runtime = obj('retained-source/runtime.json')
    install_path = 'artifacts/runner-readiness-next-twenty-project-pass/candidate-native-exit-v1/' + host + '/installed.json'
    if install_path not in payloads:
        raise ValueError('exact candidate install receipt missing')
    installed = json.loads(payloads[install_path])
    freeze = json.loads(Path(freeze_path).read_text(encoding='utf-8'))
    cells = [row for row in freeze.get('cells', []) if row.get('host') == host]
    if len(cells) != 1:
        raise ValueError('exact candidate freeze does not declare one host cell')
    frozen = cells[0]
    if (installed.get('series') != 'native-exit-v1' or installed.get('version') != 'v0.4.0-rc.6' or
            installed.get('host') != host or installed.get('binary_sha256') != build.get('candidate_sha256', installed.get('binary_sha256')) or
            installed.get('binary_sha256') != frozen.get('binary_sha256') or
            installed.get('archive_sha256') != frozen.get('archive_sha256') or
            runtime.get('source_pin') != build.get('pin') or
            runtime.get('native_sha256') != build.get('binary_sha256')):
        raise ValueError('retained target/candidate build identities do not bind the frozen host archive')
    archive_path = installed.get('archive')
    archive_raw = payloads.get(archive_path)
    if (archive_raw is None or digest(archive_raw) != frozen.get('archive_sha256') or
            len(archive_raw) != frozen.get('archive_bytes')):
        raise ValueError('actual archived runner bytes differ from frozen candidate')
    series = obj(suffix + 'summary.json')
    if series.get('project') != 'skim' or series.get('host') != host or series.get('ordinary_executions') != 240:
        raise ValueError('ordinary series scope/count/host mismatch')
    batch_paths = series.get('batches')
    if not isinstance(batch_paths, dict) or len(batch_paths) != 12:
        raise ValueError('ordinary series does not bind exactly twelve batches')
    ordinary = 0
    candidates = set()
    targets = set()
    reports = set()
    invocations = set()
    finished_by_batch_case = {}
    result_by_batch_case = {}
    execution_model = []
    fault_model = []

    def report_identity(report, result, should_pass):
        if (report.get('runner_version') != 'v0.4.0-rc.6' or len(report.get('results', [])) != 1 or
                report.get('summary', {}).get('total') != 1):
            raise ValueError('report version/result denominator mismatch')
        if result.get('status') != ('passed' if should_pass else 'failed'):
            raise ValueError('report result differs from the expected positive/mutated phase')
        steps = result.get('steps', [])
        statuses = [step.get('status') for step in steps]
        if not steps or any(status not in {'passed', 'failed', 'not_run'} for status in statuses):
            raise ValueError('report has no observed steps or contains invalid step status')
        if should_pass and any(status != 'passed' for status in statuses):
            raise ValueError('positive report contains a failed step')
        failed = [index for index, status in enumerate(statuses) if status == 'failed']
        if not should_pass and (len(failed) != 1 or any(status != 'passed' for status in statuses[:failed[0]]) or
                                any(status != 'not_run' for status in statuses[failed[0] + 1:])):
            raise ValueError('mutated report lacks a concrete failed assertion')
        if (result.get('cleanup', {}).get('confirmed_exited') is not True or
                result.get('workspace', {}).get('cleaned') is not True):
            raise ValueError('report lacks target/workspace cleanup evidence')
        invocation = result.get('invocation_id')
        workspace = result.get('workspace', {}).get('id')
        if not invocation or invocation in invocations or (workspace and workspace != invocation):
            raise ValueError('report has missing/duplicate or cross-invocation state identity')
        invocations.add(invocation)
        for step in steps:
            state = step.get('state')
            if state and (state.get('invocation_id') != invocation or state.get('workspace_id') != workspace):
                raise ValueError('report saved state belongs to a different invocation/workspace')
        return result

    per_batch = []
    for batch_path, expected_hash in sorted(batch_paths.items()):
        if not batch_path.startswith(ROOT + 'final-series-native-exit-v1/' + host + '/batch-'):
            raise ValueError('batch path escapes the exact native series')
        raw = payloads.get(batch_path)
        if raw is None or digest(raw) != expected_hash:
            raise ValueError('ordinary batch summary hash mismatch: ' + batch_path)
        batch = json.loads(raw)
        rows = batch.get('outcomes')
        if (batch.get('host') != host or batch.get('expected_cases') != 20 or
                batch.get('completed') != 20 or batch.get('failed') != 0 or
                not isinstance(rows, list) or len(rows) != 20):
            raise ValueError('ordinary batch incomplete or failed: ' + batch_path)
        cases = set()
        for row in rows:
            if (row.get('status') != 'completed' or row.get('process_exit') != 0 or
                    row.get('cleanup_confirmed') is not True or
                    row.get('workspace_cleaned') is not True or
                    not row.get('step_statuses') or any(x != 'passed' for x in row['step_statuses'])):
                raise ValueError('ordinary invocation lacks positive pass and cleanup evidence')
            candidates.add(row.get('candidate_sha256'))
            targets.add(row.get('target_sha256'))
            cases.add(row.get('case'))
            reports.add(row.get('report_sha256'))
            receipt_path = row.get('finished_path', '')
            if '/case-evidence/' not in receipt_path:
                raise ValueError('ordinary finished receipt path missing')
            relative = receipt_path.split('/case-evidence/', 1)[1]
            retained = ROOT + 'retained-source/case-evidence/' + relative
            finished_bytes = payloads.get(retained)
            report_bytes = payloads.get(retained.rsplit('/', 1)[0] + '/report.json')
            if (finished_bytes is None or digest(finished_bytes) != row.get('finished_sha256') or
                    report_bytes is None or digest(report_bytes) != row.get('report_sha256')):
                raise ValueError('ordinary report/finished receipt bytes differ from batch binding')
            finished = json.loads(finished_bytes)
            report = json.loads(report_bytes)
            if (finished.get('status') != 'completed' or finished.get('project') != 'skim' or
                    finished.get('runner_candidate_series') != 'native-exit-v1' or
                    finished.get('runner_candidate_sha256') != row.get('candidate_sha256') or
                    finished.get('target_binary_sha256') != row.get('target_sha256') or
                    finished.get('report_sha256') != digest(report_bytes)):
                raise ValueError('ordinary finished receipt candidate/report identity differs')
            contract_path = finished.get('spec', '')
            contract_bytes = payloads.get(contract_path.replace('\\', '/'))
            if contract_bytes is None or digest(contract_bytes) != finished.get('spec_sha256'):
                raise ValueError('ordinary executed spec bytes differ from the finished receipt')
            contract = json.loads(contract_bytes)
            batch_id = int(PurePosixPath(batch_path).stem.removeprefix('batch-'))
            finished_by_batch_case[(batch_id, row.get('case'))] = finished
            expected_exit = next((step['exit'] for step in contract.get('steps', [])
                                  if isinstance(step, dict) and 'exit' in step), 0)
            if row.get('target_exit') != expected_exit:
                raise ValueError('ordinary target exit differs from its executed exact contract')
            result = report_identity(report, report['results'][0], True)
            result_by_batch_case[(batch_id, row.get('case'))] = result
            ordinary += 1
        if len(cases) != 20:
            raise ValueError('duplicate or missing scenario in ordinary batch')
        per_batch.append(dict(batch_path=batch_path, sha256=expected_hash, outcomes=len(rows)))
    if ordinary != 240 or len(reports) != 240 or len(invocations) != 240 or len(candidates) != 1 or len(targets) != 1:
        raise ValueError('ordinary exact candidate identities or execution totals are not unique/complete')
    candidate_sha = next(iter(candidates)); target_sha = next(iter(targets))
    if (candidate_sha != installed.get('binary_sha256') or target_sha != build.get('binary_sha256') or
            runtime.get('native_sha256') != target_sha):
        raise ValueError('ordinary reports differ from retained build or exact archive binary')
    ordinary_invocations = len(invocations)

    plan_prefix = ROOT + 'final-series-plan-native-exit-'
    plan_paths = [name for name in payloads if name.startswith(plan_prefix) and
                  name.endswith('/' + host + '/plan.json')]
    if len(plan_paths) != 1:
        raise ValueError('artifact does not contain one unique frozen plan for the native host')
    plan_path = plan_paths[0]
    plan_raw = payloads.get(plan_path)
    plan_audit_path = plan_path.rsplit('/', 1)[0] + '/plan-audit.json'
    plan_audit_raw = payloads.get(plan_audit_path)
    if plan_raw is None or plan_audit_raw is None:
        raise ValueError('frozen plan or independent plan-audit receipt missing')
    plan = json.loads(plan_raw)
    plan_audit = json.loads(plan_audit_raw)
    if (plan.get('project') != 'skim' or plan.get('host') != host or plan.get('source_pin') != build.get('pin') or
            plan.get('candidate_sha256') != candidate_sha or plan.get('target_sha256') != target_sha or
            plan.get('expected_ordinary') != 240 or len(plan.get('batches', [])) != 12 or
            plan_audit.get('plan_sha256') != digest(plan_raw) or plan_audit.get('contracts_verified') != 240 or
            plan_audit.get('scenario_count') != 20 or plan_audit.get('executed_cases') != 0 or
            plan_audit.get('candidate_sha256') != candidate_sha or plan_audit.get('target_sha256') != target_sha):
        raise ValueError('frozen plan/audit receipts differ from actual host candidate or expected scope')
    _, declaration_raw = find_hash_bound_document(payloads, 'final-series-declaration-native-exit-v',
                                                  plan.get('declaration_sha256'))
    _, base_raw = find_hash_bound_document(payloads, 'scenario-declaration-v',
                                           plan.get('scenario_base_sha256'))
    _, revision_raw = find_hash_bound_document(payloads, 'scenario-declaration-v',
                                               plan.get('scenario_revision_sha256'))
    declaration = json.loads(declaration_raw)
    base_scenarios = json.loads(base_raw)
    revision_scenarios = json.loads(revision_raw)
    scenario_rows = {row['id']: row for row in base_scenarios['scenarios']}
    scenario_rows.update({row['id']: row for row in revision_scenarios['replacements']})
    if (declaration.get('scenario_base_sha256') != digest(base_raw) or
            declaration.get('scenario_revision_sha256') != digest(revision_raw) or
            declaration.get('candidate_freeze_sha256') != digest(Path(freeze_path).read_bytes()) or
            len(scenario_rows) != 20 or sum(row.get('kind') == 'normal' for row in scenario_rows.values()) != 8 or
            sum(row.get('kind') == 'edge' for row in scenario_rows.values()) != 12):
        raise ValueError('exact frozen scenario declaration or 8+12 breadth differs')

    contracts_verified = 0
    path_marker = '\\artifacts\\' if host == 'windows' else '/artifacts/'
    path_module = ntpath if host == 'windows' else posixpath
    source_path = runtime.get('source_path', '')
    if path_marker not in source_path:
        raise ValueError('retained runtime does not bind the hosted checkout root')
    checkout_root = source_path.split(path_marker, 1)[0]
    for batch_id, batch_plan in enumerate(plan['batches']):
        cases = batch_plan.get('cases', [])
        if len(cases) != 20 or batch_plan.get('batch', {}).get('id') != batch_id:
            raise ValueError('frozen plan batch has wrong case count or sequence')
        for planned in cases:
            case = planned.get('case')
            if case not in scenario_rows:
                raise ValueError('frozen plan references an undeclared scenario')
            contract_path = planned.get('contract', '').replace('\\', '/')
            contract_raw = payloads.get(contract_path)
            canonical_path = DOC + planned.get('canonical_contract', '')
            canonical_raw = payloads.get(canonical_path)
            finished = finished_by_batch_case.get((batch_id, case))
            if (contract_raw is None or canonical_raw is None or finished is None or
                    digest(contract_raw) != planned.get('contract_sha256') or
                    digest(canonical_raw) != planned.get('canonical_sha256') or
                    finished.get('spec', '').replace('\\', '/') != contract_path or
                    planned.get('target_binary_sha256') != target_sha):
                raise ValueError('actual plan, executed contract, or target identity mismatch')
            canonical_contract = json.loads(canonical_raw)
            target_relative = planned.get('target_binary', '')
            normalized_receipt_target = finished.get('target_binary_path', '').replace('\\', '/')
            if normalized_receipt_target != target_relative:
                raise ValueError('finished receipt target path differs from frozen plan')
            target_absolute = path_module.join(checkout_root, target_relative.replace('/', path_module.sep))
            expected_contract = reconstruct_skim(batch_id, case, canonical_contract,
                                                  target_absolute)
            observed_contract = json.loads(contract_raw)
            if observed_contract != expected_contract:
                differing = sorted(key for key in set(observed_contract) | set(expected_contract)
                                   if observed_contract.get(key) != expected_contract.get(key))
                raise ValueError(f'batch {batch_id} {case}: executed contract differs from independent reconstruction: {differing}')

            result = result_by_batch_case[(batch_id, case)]
            execution_model.append(dict(batch=batch_id, case=case,
                invocation_id=result.get('invocation_id'), workspace_id=result.get('workspace', {}).get('id'),
                contract_sha256=digest(contract_raw), report_sha256=digest(report_bytes),
                candidate_archive_sha256=frozen['archive_sha256'],
                candidate_sha256=candidate_sha, target_sha256=target_sha,
                status=result.get('status'), step_statuses=[step.get('status') for step in result.get('steps', [])],
                target_cleanup=result.get('cleanup', {}).get('confirmed_exited'),
                workspace_cleanup=result.get('workspace', {}).get('cleaned'),
                contract_reconstructed=True))

            fixture_relative = observed_contract.get('workspace', {}).get('fixture')
            canonical_fixture_relative = canonical_contract.get('workspace', {}).get('fixture')
            planned_fixture = PurePosixPath(contract_path).parent.as_posix() + '/' + fixture_relative
            canonical_fixture = (PurePosixPath(canonical_path).parent /
                                 canonical_fixture_relative).as_posix()
            def tree(prefix):
                marker = prefix.rstrip('/') + '/'
                return {name[len(marker):]: digest(data) for name, data in payloads.items() if name.startswith(marker)}
            if not tree(planned_fixture) or tree(planned_fixture) != tree(canonical_fixture):
                raise ValueError('executed fixture bytes differ from canonical reviewed fixture')
            for step in observed_contract.get('steps', []):
                snapshot = step.get('snapshot') if isinstance(step, dict) else None
                if snapshot:
                    actual_snapshot = PurePosixPath(contract_path).parent.as_posix() + '/snapshots/' + snapshot
                    original_snapshot = DOC + 'snapshots/' + snapshot
                    if payloads.get(actual_snapshot) != payloads.get(original_snapshot) or actual_snapshot not in payloads:
                        raise ValueError('executed snapshot bytes differ from canonical approved baseline')
            contracts_verified += 1
    if contracts_verified != 240:
        raise ValueError('independent contract reconstruction denominator mismatch')

    faults = obj('fault-calibrations-native-exit-v1/' + host + '/summary.json')
    observations = faults.get('observations', [])
    if (faults.get('candidate_sha256') != candidate_sha or faults.get('host') != host or
            faults.get('distinct_faults') != 3 or faults.get('phases') != 9 or len(observations) != 3 or
            faults.get('baseline_passes') != 3 or faults.get('mutations_detected') != 3 or
            faults.get('restored_recovery_passes') != 3 or faults.get('source_restored') is not True or
            faults.get('target_binary_restored') is not True):
        raise ValueError('three-fault calibration summary is incomplete or mismatched')
    fault_rows = 0
    for observation in observations:
        phases = observation.get('phases', {})
        if (observation.get('detected') is not True or observation.get('source_restored') is not True or
                set(phases) != {'baseline', 'corrupted', 'restored'}):
            raise ValueError('fault mutation detection/source restoration incomplete')
        for phase, row in phases.items():
            receipt_path = row.get('finished_path', '')
            if '/case-evidence/' not in receipt_path:
                raise ValueError('fault finished receipt path missing')
            relative = receipt_path.split('/case-evidence/', 1)[1]
            retained = ROOT + 'retained-source/case-evidence/' + relative
            finished_bytes = payloads.get(retained)
            report_bytes = payloads.get(retained.rsplit('/', 1)[0] + '/report.json')
            if (finished_bytes is None or digest(finished_bytes) != row.get('finished_sha256') or
                    report_bytes is None or digest(report_bytes) != row.get('report_sha256') or
                    row.get('target_cleanup_confirmed') is not True or row.get('workspace_cleaned') is not True or
                    row.get('harness_cleanup') != 'harness_process_reaped'):
                raise ValueError('fault report/receipt/cleanup evidence mismatch')
            report = json.loads(report_bytes)
            positive = phase in {'baseline', 'restored'}
            result = report_identity(report, report['results'][0], positive)
            expected_target = observation['mutant_binary_sha256'] if phase == 'corrupted' else target_sha
            finished = json.loads(finished_bytes)
            if (row.get('runner_candidate_sha256') != candidate_sha or
                    row.get('expected_runner_sha256') != candidate_sha or
                    row.get('expected_target_sha256') != expected_target or
                    row.get('target_binary_sha256') != expected_target or
                    finished.get('runner_candidate_sha256') != candidate_sha or
                    finished.get('executable_sha256') != expected_target or
                    finished.get('report_sha256') != digest(report_bytes)):
                raise ValueError('fault phase runner/target executable identity differs from its bound mutation')
            fault_model.append(dict(fault_id=observation.get('fault'),
                phase=phase, invocation_id=result.get('invocation_id'),
                runner_sha256=candidate_sha, target_sha256=expected_target,
                status=result.get('status'), target_cleanup=result.get('cleanup', {}).get('confirmed_exited'),
                workspace_cleanup=result.get('workspace', {}).get('cleaned'),
                source_restored=observation.get('source_restored') is True,
                detected=observation.get('detected') is True))
            fault_rows += 1
    if fault_rows != 9:
        raise ValueError('fault phase denominator mismatch')

    plan = obj('first-public-v1/planned.json')
    if (plan.get('runner_sha256') != candidate_sha or plan.get('target_binary_sha256') != target_sha or
            plan.get('candidate') != 'v0.4.0-rc.6' or plan.get('no_handwritten_first_use_spec') is not True):
        raise ValueError('public route plan differs from exact native candidate')
    public = {}
    for name in ('first-use', 'diagnosis', 'maintenance-before-update', 'maintenance-update', 'relocation'):
        data = obj('first-public-v1/' + name + '-report.json')
        if data.get('runner_version') != 'v0.4.0-rc.6' or len(data.get('results', [])) != 1:
            raise ValueError('public route report is incomplete: ' + name)
        row = data['results'][0]
        public[name] = row.get('status')
        if name in {'first-use', 'maintenance-update', 'relocation'}:
            if row.get('status') != 'passed' or any(s.get('status') != 'passed' for s in row.get('steps', [])):
                raise ValueError('public success route did not pass: ' + name)
            report_identity(data, row, True)
        else:
            if row.get('status') != 'failed' or not row.get('failure', {}).get('category'):
                raise ValueError('public diagnosis/maintenance did not fail usefully: ' + name)
            report_identity(data, row, False)
    # The initial project spec is the actual public recorder export.
    initial = json.loads(get('first-public-v1/project/selection.json'))
    maintenance = json.loads(get('first-public-v1/maintenance/selection-maintenance.json'))
    if (initial.get('command', [None])[-1:] != ['--query=cedar'] or
            maintenance.get('command', [None])[-1:] != ['--query=amber'] or
            not any(step == {'expect': 'amber'} for step in maintenance.get('steps', []))):
            raise ValueError('maintenance did not update the exact query and matching result assertion')
    relocated = [name for name in payloads if name.startswith(ROOT + 'first-public-v1/relocated space caf')
                 and name.endswith('/selection-maintenance.json')]
    if len(relocated) != 1 or payloads[relocated[0]] != get('first-public-v1/maintenance/selection-maintenance.json'):
        raise ValueError('Unicode relocation changed the reviewed maintenance spec bytes')
    preview = get('first-public-v1/delivered-workflow-preview.yml').decode('utf-8')
    if ('pull_request:' not in preview or 'pull_request_target:' in preview or
            revision not in preview or 'persist-credentials: false' not in preview or
            'contents: read' not in preview or 'secrets.' in preview.lower()):
        raise ValueError('delivered workflow preview lacks a read-only source-pinned PR boundary')

    process = obj('process-proof.json')
    cleanup = obj('retained-source/cleanup-inventory.json')
    prepared = obj('retained-source/prepared.json')
    removed = obj('retained-source/removed.json')
    if (process.get('confirmed_no_matching_live_processes') is not True or process.get('matching_live_processes') != [] or
            cleanup.get('project') != 'skim' or cleanup.get('source_restored_exact') is not True or
            prepared.get('removed') is not False or prepared.get('source_restored_exact') is not True or
            prepared.get('cleanup_inventory_sha256') != digest(get('retained-source/cleanup-inventory.json')) or
            prepared.get('process_proof_sha256') != digest(get('process-proof.json')) or
            removed.get('removed') is not True or removed.get('cleanup_inventory_sha256') != digest(get('retained-source/cleanup-inventory.json')) or
            (removed.get('process_proof_sha256') is not None and
             removed.get('process_proof_sha256') != digest(get('process-proof.json')))):
        raise ValueError('checked target removal/source/process receipts do not cross-bind')
    cache_removed_paths = [n for n in payloads if '/cache-cleanup/' in n and n.endswith('/removed.json')]
    if len(cache_removed_paths) != 1:
        raise ValueError('compiler cache cleanup receipt missing or ambiguous')
    cache_removed_path = cache_removed_paths[0]
    cache_removed = json.loads(payloads[cache_removed_path])
    cache_prepared_path = cache_removed_path.rsplit('/', 1)[0] + '/prepared.json'
    cache_prepared_raw = payloads.get(cache_prepared_path)
    if (cache_prepared_raw is None or digest(cache_prepared_raw) != cache_removed.get('prepared_sha256') or
            cache_removed.get('removed_roots') != ['cargo-home', 'cargo-target', 'go-mod-cache', 'home', 'rustup-home', 'tmp']):
        raise ValueError('compiler cache cleanup prepared/removed receipts differ')

    return dict(schema_version=1, project='skim', host=host, run_id=run_id, revision=revision,
        provider_artifact_sha256=provider_sha256, retrieved_sha256=raw_digest.hexdigest(),
        artifact_bytes=provider_bytes, zip_entries=len(infos), expanded_bytes=total,
        distinct_all_invocations=len(invocations),
        candidate_runner_sha256=candidate_sha, target_binary_sha256=target_sha,
        ordinary=dict(batches=12, outcomes=ordinary, distinct_reports=len(reports),
            distinct_invocations=ordinary_invocations, candidate_identities=len(candidates), target_identities=len(targets),
            all_steps_passed=True, all_cleanup_confirmed=True, independent_contracts_reconstructed=contracts_verified,
            batch_summaries=per_batch),
        faults=dict(distinct=3, phases=fault_rows, baselines=3, detected_mutations=3,
            restored_recoveries=3, source_restored=True),
        public_route=dict(statuses=public, maintenance_updated_matching_expect=True,
            unicode_relocation_exact_spec=True, delivered_preview_sha256=digest(get('first-public-v1/delivered-workflow-preview.yml'))),
        actual_model=dict(project='skim', host=host, normal_scenarios=8, edge_scenarios=12, ordinary=execution_model,
            faults=fault_model, distinct_faults=3, fault_phases=9,
            candidate_archive_sha256=frozen['archive_sha256'], candidate_runner_sha256=candidate_sha,
            target_binary_sha256=target_sha, source_restored=True),
        cleanup=dict(process_absent=True, source_restored=True, compiler_cache_removed=True,
            checked_target_removed=True, cleanup_inventory_sha256=digest(get('retained-source/cleanup-inventory.json'))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--provider-sha256', required=True)
    parser.add_argument('--provider-bytes', type=int, required=True)
    parser.add_argument('--host', choices=['linux', 'windows'], required=True)
    parser.add_argument('--run-id', type=int, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.archive, args.provider_sha256, args.provider_bytes, args.host, args.run_id, args.revision, args.freeze)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('project', 'host', 'run_id', 'candidate_runner_sha256', 'target_binary_sha256', 'ordinary', 'faults', 'public_route', 'cleanup')}, sort_keys=True))


if __name__ == '__main__':
    main()
