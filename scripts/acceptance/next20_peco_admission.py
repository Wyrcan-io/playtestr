"""Close the audited Peco project, preserving the copied-image proof correction."""
import json
import lzma

from next20_check import DOC, RAW, ROOT
from next20_peco_cell_readback import Evidence
from readiness_evidence import immutable_json, sha256


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    package = DOC / 'peco'
    root = RAW / 'peco'
    subjects = {}

    def bind(path):
        subjects[path.relative_to(ROOT).as_posix()] = sha256(path)
        return json.loads(path.read_text(encoding='utf-8-sig')) if path.suffix == '.json' else None

    require(not (RAW / 'active/peco').exists(), 'active source/runtime remains')
    complete = bind(package / 'complete-retained-readback-v1.json')
    require(complete['original_ordinary_verified'] == 480 and complete['qualified_normal_rebuild_calibrations'] == 18
            and complete['normal_rebuilds_verified'] == 6 and complete['actual_rebuild_compiler_executions_verified'] == 12
            and complete['local_reports_verified'] == 357 and complete['source_runtime_removed'], 'incomplete post-compaction audit')
    require(complete['local_index_sha256'] == sha256(root / 'retained-local-v1/index.json')
            and complete['local_removal_sha256'] == sha256(root / 'retained-local-v1/expanded-removed.json'), 'retention changed after audit')
    evidence = Evidence('windows')
    for window in ['', '-rebuild-v1']:
        proof = evidence.load('peco/process-proof' + window + '.json')
        require(proof['confirmed_no_matching_live_processes'] and not proof['matching_live_processes'], 'owned process remains')
    primary = bind(package / 'source-provenance.json')
    require(primary['repository'] == 'peco/peco' and primary['pin'] == 'c5bf9a3c098c52f324f46c1d00d0424b982cc9fa', 'canonical identity changed')
    controls_path = root / 'audit-controls/771a7babb35c434bafe682bec05a8d0f/results.json'
    controls = bind(controls_path)
    require(controls['normal_rebuild_calibration_model'] and controls['semantic_corruptions_rejected'] == 42, 'missing normal-rebuild integrity controls')
    cells = []
    for host in ['windows', 'linux']:
        old = bind(package / (host + '-final-cell-readback-removed.json'))
        new = bind(package / (host + '-normal-rebuild-readback-removed.json'))
        require(old['ordinary_readbacks'] == 240 and old['source_runtime_removed'] and old['all_target_workspace_cleanup'], 'ordinary cell incomplete')
        require(new['calibrations_verified'] == 9 and new['normal_rebuilds_verified'] == 3
                and new['actual_compiler_executions_verified'] == 6 and new['source_runtime_removed']
                and new['original_ordinary_matrix_unchanged'], 'normal source rebuild cell incomplete')
        model = next(c for c in controls['cells'] if c['host'] == host)
        require(len(model['controls']) == 21 and all(c['rejected'] for c in model['controls']), 'corruption controls incomplete')
        path = RAW / model['model']
        require(sha256(path) == model['model_sha256'], 'actual normalized model changed')
        actual = json.loads(lzma.decompress(path.read_bytes(), memlimit=64 * 1024**2))
        require(len(actual['ordinary']) == 240 and len(actual['faults']) == 3
                and all(f['normal_rebuild_recovery_executed'] for f in actual['faults']), 'actual normal-rebuild model incomplete')
        bind(path)
        cells.append(dict(host=host, ordinary=240, calibrations=9, normal_rebuilds=3,
                          ordinary_source_revision=old['helper_source_revision'], recovery_source_revision=new['source_revision'],
                          ordinary_run=old['provider_run'], recovery_run=new['run'], source_runtime_removed=True,
                          ordinary_readback=(package / (host + '-final-cell-readback-removed.json')).relative_to(DOC).as_posix(),
                          recovery_readback=(package / (host + '-normal-rebuild-readback-removed.json')).relative_to(DOC).as_posix(),
                          actual_model=model['model'], actual_model_sha256=model['model_sha256']))
    history = bind(package / 'all-attempt-evidence.json')
    delta = bind(package / 'normal-rebuild-history-delta-v1.json')
    require(history['historical_frames_complete'] and delta['all_original_failure_history_preserved']
            and delta['actual_local_report_total'] == 357 and delta['actual_local_target_total'] == 354, 'failure history incomplete')
    first = bind(package / 'first-use.json')
    require(first['shell_invocations'] == 3 and first['recorder_controls'] == 16 and not first['handwritten_playtestr_json'], 'public authoring evidence differs')
    journey = evidence.load('peco/maintenance-fdb85381c76b421ea90c8ab881c73f2b/journey.json')
    require(journey, 'maintenance evidence missing')
    for directory in ['retained-local-v1', 'retained-native-v1', 'retained-native-v2', 'retained-native-v3',
                      'retained-native-v4', 'retained-source', 'retained-source-rebuild-v1',
                      'go-module-corpus', 'go-module-corpus-rebuild-v1',
                      'execution-helper-source-v1', 'execution-helper-source-rebuild-v1']:
        require((root / directory).is_dir(), 'mandatory retained dependency missing')
        for path in (root / directory).rglob('*'):
            if path.is_file():
                subjects[path.relative_to(ROOT).as_posix()] = sha256(path)
    size = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    require(size <= 64 * 1024**2, 'retained project cap exceeded')
    gate = package / 'restoration-rebuild-gate.json'
    resolution = dict(schema_version=1, project='peco', candidate='v0.4.0-rc.6', gate_sha256=sha256(gate),
                      status='resolved-normal-rebuild', qualified_calibrations=18, accepted_ordinary_unchanged=True,
                      original_ordinary=480, actual_normal_rebuilds=6,
                      complete_retained_readback_sha256=sha256(package / 'complete-retained-readback-v1.json'),
                      prior_exposure='Repeated training faults; original selection/detection history preserved.',
                      historical_copy_recovery_calibrations=18)
    immutable_json(package / 'restoration-rebuild-resolution.json', resolution)
    for path in package.rglob('*'):
        if path.is_file() and path.name != 'admission.json':
            subjects[path.relative_to(ROOT).as_posix()] = sha256(path)
    immutable_json(package / 'admission.json', dict(schema_version=1, admitted=True, project='peco', repository=primary['repository'], pin=primary['pin'],
        candidate='v0.4.0-rc.6', canonical_scenarios=20, normal=8, edge=12, ordinary=480, calibrations=18,
        real_source_faults=3, native_cells=cells, cell_model_negative_controls=42, normal_restoration_rebuilds=6,
        local_target_absent=True, maintenance_suffix_relocation=True, initial_usability_target_met=True,
        generated_workflow=True, delivered_ci_observations=0, human_participants=0, human_usability='unmeasured',
        paid_admissions=0, retained_bytes=size, subjects=subjects,
        limitations=[
            'Private engineering qualification of exact rc.6 archives; campaign-wide gates remain open.',
            'Prepared-agent public route passed in3shell invocations/16controls; no unfamiliar-human usability observation.',
            'Original development, maintenance, materialization, metadata and cleanup failures remain preserved.',
            'Original copied-image recovery triples are historical;18new phases with6actual normal source rebuilds replace their qualification credit. Repeated faults are exposed training.',
            'Go SDK and system prerequisites are identified,not retained SDKs or isolation. Mandatory standalone native-v1 and all dependent packets must remain available.',
            'Generated workflow was linted,not dispatched; no delivered-CI observation credit.'],
        scope='One new canonical project:480ordinary/18normal-rebuild calibration phases on Windows and Linux; full retained evidence and checked cleanup. No release or campaign completion.'))
    print('Admitted Peco:480 ordinary,18 normal-rebuild calibration phases,2 native cells; historical failures preserved.')


if __name__ == '__main__':
    main()
