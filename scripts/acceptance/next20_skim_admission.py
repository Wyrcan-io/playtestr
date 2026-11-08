"""Close Skim's exact rc.6 project admission from provider-bound V15 readbacks."""
import hashlib
import json
from pathlib import Path

from next20_check import DOC, RAW, ROOT
from next20_skim_model_controls import validate
from readiness_evidence import immutable_json, sha256


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical_sha256(value):
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def bind(subjects, path):
    path = Path(path)
    subjects[path.relative_to(ROOT).as_posix()] = sha256(path)
    return path


def tree_subjects(subjects, root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'Skim retained root missing or linked')
    count = 0
    total = 0
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(),
                'linked Skim retained evidence path: ' + str(path))
        if path.is_file():
            count += 1
            total += path.stat().st_size
            subjects[path.relative_to(ROOT).as_posix()] = sha256(path)
    return count, total


def admission():
    package = DOC/'skim'
    raw = RAW/'skim'
    require(not (RAW/'active/skim').exists(), 'active Skim source/runtime remains')
    provenance_path = package/'source-provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    source_review_path = package/'source-review-v5.json'
    source_review = json.loads(source_review_path.read_text(encoding='utf-8'))
    require(provenance.get('repository') == 'skim-rs/skim' and
            provenance.get('pin') == '1ab47f6ba7f1bfc355273bbdd98d4b2056ef95a3' and
            source_review.get('license') == 'MIT' and
            source_review.get('repository') == 'https://github.com/skim-rs/skim' and
            source_review.get('pin') == provenance['pin'], 'Skim canonical source identity differs')

    aggregate_path = bind({}, DOC/'skim-artifact-retrieval-readback-v15.json')
    aggregate = json.loads(aggregate_path.read_text(encoding='utf-8'))
    require(aggregate.get('project') == 'skim' and aggregate.get('candidate') == 'v0.4.0-rc.6' and
            aggregate.get('workflow_run_id') == 42528435724 and aggregate.get('totals') == dict(
                fault_phases=18, independently_reconstructed_contracts=480,
                ordinary=480, semantic_corruptions_rejected=24),
            'Skim V15 aggregate is not the exact qualified project matrix')

    freeze_path = bind({}, DOC/'replacement-candidate-freeze-native-exit-v1.json')
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
    controls_path = bind({}, DOC/'skim-model-controls-v3.json')
    controls = json.loads(controls_path.read_text(encoding='utf-8'))
    require(controls.get('project') == 'skim' and controls.get('candidate') == 'v0.4.0-rc.6' and
            controls.get('source_run_id') == aggregate['workflow_run_id'] and
            controls.get('semantic_corruptions_rejected') == 24,
            'Skim actual-model control receipt differs from provider readbacks')
    require(aggregate.get('actual_model_controls') == dict(
        path=controls_path.name, positive_models_restored=True,
        semantic_corruptions_rejected=24, sha256=sha256(controls_path)),
        'Skim V15 aggregate does not bind the current model controls')

    controls_by_host = {cell['host']: cell for cell in controls['cells']}
    freeze_by_host = {cell['host']: cell for cell in freeze['cells']}
    aggregate_by_host = {cell['host']: cell for cell in aggregate['hosts']}
    cells = []
    source_revisions = set()
    for host in ('linux', 'windows'):
        readback_path = bind({}, DOC/f'artifact-retrieval-readback-v15-{host}.json')
        readback = json.loads(readback_path.read_text(encoding='utf-8'))
        model = readback.get('actual_model')
        model_cell = controls_by_host.get(host)
        frozen = freeze_by_host.get(host)
        summary = aggregate_by_host.get(host)
        require(model and model_cell and frozen and summary, 'Skim native cell model is missing')
        validate(model, host)
        require(model_cell.get('model') == model and model_cell.get('model_sha256') == canonical_sha256(model) and
                len(model_cell.get('controls', [])) == 12 and
                all(row.get('rejected') is True for row in model_cell['controls']),
                'Skim actual model/corruption controls differ for ' + host)
        require(readback.get('project') == 'skim' and readback.get('host') == host and
                readback.get('run_id') == aggregate['workflow_run_id'] and
                readback.get('ordinary', {}).get('outcomes') == 240 and
                readback.get('ordinary', {}).get('independent_contracts_reconstructed') == 240 and
                readback.get('faults', {}).get('phases') == 9 and
                readback.get('faults', {}).get('distinct') == 3 and
                readback.get('cleanup') == summary['cleanup'],
                'Skim provider artifact readback is incomplete for ' + host)
        route = readback.get('public_route', {})
        require(route.get('statuses') == dict(diagnosis='failed', **{'first-use': 'passed',
                    'maintenance-before-update': 'failed', 'maintenance-update': 'passed',
                    'relocation': 'passed'}),
                'Skim public-route outcome matrix differs for ' + host)
        require(route.get('maintenance_updated_matching_expect') is True and
                route.get('unicode_relocation_exact_spec') is True and
                len(route.get('delivered_preview_sha256', '')) == 64,
                'Skim maintenance/relocation/delivered-workflow evidence is incomplete for ' + host)
        require(model['candidate_archive_sha256'] == frozen['archive_sha256'] and
                model['candidate_runner_sha256'] == frozen['binary_sha256'] and
                model['target_binary_sha256'] == readback['target_binary_sha256'] and
                readback['provider_artifact_sha256'] == summary['provider_artifact_sha256'] and
                readback['artifact_bytes'] == summary['provider_bytes'],
                'Skim native cell does not bind the frozen candidate and provider artifact')
        source_revisions.add(readback['revision'])
        cells.append(dict(host=host, execution_host=host, run=aggregate['workflow_run_id'],
            source_revision=readback['revision'], ordinary=240, calibrations=9,
            candidate_archive_sha256=model['candidate_archive_sha256'],
            runner_sha256=model['candidate_runner_sha256'],
            target_sha256=model['target_binary_sha256'],
            actual_model=readback_path.name+'#actual_model',
            actual_model_sha256=model_cell['model_sha256'],
            readback=readback_path.name, readback_sha256=sha256(readback_path),
            provider_artifact_sha256=readback['provider_artifact_sha256'],
            provider_artifact_bytes=readback['artifact_bytes'],
            distinct_faults=3, fault_phases=9, checked_cleanup=True,
            semantic_corruptions_rejected=12))
    require(len(source_revisions) == 1 and len(cells) == 2,
            'Skim native cells are not from one reviewed workflow/source revision')

    # Both native logs report the same prepared-agent first route at 3 commands
    # and 8 recorder controls; this is not a human usability observation.
    route_summary = dict(shell_invocations=3, recorder_controls=8,
        no_handwritten_playtestr_json=True, first_use='passed',
        diagnosis='seeded failure identified and useful next action recorded',
        maintenance='selected snapshot updated after the matching assertion change',
        relocation='spaced Unicode path passed', delivered_workflow='preview only; not dispatched')

    subjects = {}
    for path in sorted(package.rglob('*')):
        if (not path.is_file() or path.name == 'admission.json' or path.name.startswith('draft-') or
                path.name == 'README.md'):
            continue
        require(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(),
                'linked Skim documentation subject')
        subjects[path.relative_to(ROOT).as_posix()] = sha256(path)
    for path in (aggregate_path, controls_path, freeze_path,
                 DOC/'artifact-retrieval-readback-v15-linux.json',
                 DOC/'artifact-retrieval-readback-v15-windows.json',
                 ROOT/'scripts/acceptance/next20_skim_admission.py'):
        subjects[path.relative_to(ROOT).as_posix()] = sha256(path)
    raw_files, retained_bytes = tree_subjects(subjects, raw)
    require(0 < raw_files and retained_bytes <= 64*1024**2,
            'Skim retained project evidence exceeds its individual cap')
    result = dict(schema_version=1, admitted=True, project='skim', repository='skim-rs/skim',
        pin=provenance['pin'], candidate='v0.4.0-rc.6', canonical_scenarios=20,
        normal=8, edge=12, ordinary=480, calibrations=18, real_source_faults=3,
        native_cells=cells, cell_model_negative_controls=24, local_target_absent=True,
        maintenance_suffix_relocation=True, initial_usability_target_met=True,
        prepared_agent_public_route=route_summary, generated_workflow=True,
        delivered_ci_observations=0, human_participants=0, human_usability='unmeasured',
        paid_admissions=0, retained_bytes=retained_bytes, retained_files=raw_files,
        subjects=subjects, limitations=[
            'Private engineering qualification of exact rc.6 archives; campaign-wide gates remain open.',
            'Prepared-agent route passed in 3 shell invocations and 8 recorder controls; no unfamiliar-human usability observation.',
            'Windows ArrowDown/Ctrl-N directional navigation remains unverified.',
            'E12 checks the selected screen and exit only; exact raw NUL framing remains unverified.',
            'Delivered free workflow was previewed but not dispatched; no delivered-CI observation credit.',
            'Campaign combined retained storage cap is currently exceeded; this project admission does not close that separate campaign gate.'
        ], scope='One exact rc.6 project admission from two provider-digest-bound native cells, 480 ordinary executions, 18 positive/mutated/restored fault phases, 24 rejected semantic model corruptions, public first-use/diagnosis/maintenance/relocation and checked cleanup. Campaign closure remains separate.')
    return result


def main():
    package = DOC/'skim'
    path = package/'admission.json'
    result = admission()
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) != result:
            raise ValueError('existing Skim admission differs; preserve it and declare a new revision')
    else:
        immutable_json(path, result)
    print('Skim admitted on exact rc.6: 20 scenarios, 480 ordinary, 18 fault phases, 2 native cells; campaign closure remains open.')


if __name__ == '__main__':
    main()
