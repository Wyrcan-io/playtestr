"""Close Git Town's exact RC6 admission only from the audited V20 evidence."""
import json
import lzma
from pathlib import Path

from readiness_evidence import immutable_json, sha256

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass'
RAW = ROOT / 'artifacts/runner-readiness-next-twenty-project-pass'


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    ledger = json.loads((DOC / 'projects.json').read_text(encoding='utf-8'))
    rows = [row for row in ledger['projects'] if row['id'] == 'git-town']
    require(len(rows) == 1 and rows[0]['admitted'] is False, 'Git Town is missing, duplicated, or already admitted')
    row = rows[0]
    require(row['repository'] == 'git-town/git-town' and
            row['pin'] == '8d039892574d4852e1843020c31d423234042e78', 'selected upstream identity differs')
    require(ledger['qualification_candidate'] == 'v0.4.0-rc.6', 'current candidate changed')
    selected = json.loads((DOC / 'selection-declaration.json').read_text(encoding='utf-8'))
    require(any(p['id'] == 'git-town' and p['repository'] == row['repository'] for p in selected['selected']),
            'Git Town is not one of the declared selected projects')
    audit_path = DOC / 'git-town/final-series-audit-v20.json'
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    require(audit['run_id'] == '41994487910' and audit['run_conclusion'] == 'success' and
            audit['qualification_credit']['project_admission'] is False and
            audit['qualification_credit']['ordinary_executions'] == 480 and
            audit['qualification_credit']['calibrations'] == 18 and
            audit['qualification_credit']['distinct_real_faults'] == 3,
            'independent V20 audit is not the expected successful zero-admission record')
    control_dirs = sorted((RAW / 'git-town/audit-controls').glob('v20-reconstructed-*'),
                          key=lambda p: p.stat().st_mtime, reverse=True)
    require(control_dirs, 'reconstructed cell-model controls are absent')
    controls_path = control_dirs[0] / 'results.json'
    controls = json.loads(controls_path.read_text(encoding='utf-8'))
    require(controls['run_id'] == audit['run_id'] and controls['candidate'] == audit['candidate'] and
            controls['controls_count'] == 24 and len(controls['controls']) == 24 and
            all(item['rejected'] for item in controls['controls']), 'actual model tamper controls are incomplete')
    require({c['host'] for c in controls['cells']} == {'linux', 'windows'}, 'native model set differs')
    for cell in controls['cells']:
        path = RAW / cell['model']
        require(sha256(path) == cell['model_sha256'], 'actual cell model hash differs')
        model = json.loads(lzma.decompress(path.read_bytes(), memlimit=64 * 1024 * 1024))
        require(model['host'] == cell['host'] and len(model['ordinary']) == 240 and
                len({r['case'] for r in model['ordinary']}) == 20 and
                all(r['passed'] and r['confirmed_exited'] for r in model['ordinary']),
                'actual positive cell model is incomplete or contains a failure')
    first_use_path = DOC / 'git-town/authoring/first-use-attempts-v1.json'
    first_use = json.loads(first_use_path.read_text(encoding='utf-8'))['repaired_documented_window']
    require(first_use['ordinary_report_summary']['passed'] == 1 and
            first_use['ordinary_report_summary']['failed'] == 0 and
            first_use['commands_to_first_ordinary_pass'] <= 5 and first_use['command_is_bare_name'],
            'repaired documented first-use route lacks positive public evidence')
    maintenance_path = DOC / 'git-town/authoring/maintenance-readback-v1.json'
    maintenance = json.loads(maintenance_path.read_text(encoding='utf-8'))
    require(maintenance['maintenance_replay']['status'] == 'passed' and
            maintenance['maintenance_replay']['cleanup_confirmed'] and
            maintenance['maintenance_replay']['workspace_cleaned'], 'selected maintenance replay is not positive')
    relocation_path = DOC / 'git-town/authoring/relocated suite/試験/relocation-manifest-v1.json'
    relocation = json.loads(relocation_path.read_text(encoding='utf-8'))
    require(relocation['space_and_unicode_path_verified'] and relocation['portable_template'] and
            relocation['file_count'] > 0, 'portable Unicode/spaced relocation was not verified')
    require(not (RAW / 'active/git-town').exists(), 'owned Git Town local target/runtime remains active')
    require(ledger['new_project_admissions'] == 4 and ledger['current_candidate_new_project_admissions'] == 3,
            'pre-admission candidate accounting differs; reconcile before promotion')

    controls_doc = DOC / 'git-town/model-controls-v20.json'
    immutable_json(controls_doc, controls)
    declaration_path = DOC / 'git-town/final-series-declaration-native-exit-v20.json'
    declaration = json.loads(declaration_path.read_text(encoding='utf-8'))
    cells = []
    for cell in controls['cells']:
        cells.append(dict(host=cell['host'], run=cell['run_id'], source_revision=cell['source_revision'],
            execution_host=cell['execution_host'], ordinary=240, calibrations=9,
            candidate_archive_sha256=cell['candidate_archive_sha256'], runner_sha256=cell['runner_sha256'],
            actual_target_binary_sha256=cell['target_binary_sha256'],
            actual_model=cell['model'], actual_model_sha256=cell['model_sha256']))
    subjects = {}
    for path in (audit_path, declaration_path, DOC / 'git-town/final-series-attempts-v20.json',
                 DOC / 'git-town/scenario-catalog-v3.json', DOC / 'git-town/fault-declaration-v9.json',
                 DOC / 'git-town/source-provenance.json', DOC / 'git-town/source-review-v4.json',
                 first_use_path, maintenance_path, relocation_path, controls_doc,
                 DOC / 'git-town/final-series-retention-readback-v21.json',
                 DOC / 'git-town/final-series-retention-cleanup-v1.json'):
        subjects[path.relative_to(DOC).as_posix()] = sha256(path)
    for cell in controls['cells']:
        path = RAW / cell['model']
        subjects[cell['model']] = sha256(path)
    retention = json.loads((RAW / 'retained/git-town-final-v20-v2/readback-v1.json').read_text(encoding='utf-8'))
    subjects['retained/git-town-final-v20-v2/readback-v1.json'] = sha256(RAW / 'retained/git-town-final-v20-v2/readback-v1.json')
    for host_row in retention['hosts']:
        packet = RAW / host_row['retained_packet']
        subjects[host_row['retained_packet']] = sha256(packet)
    admission = dict(schema_version=1, project='git-town', repository='git-town/git-town',
        pin=row['pin'], admitted=True, candidate='v0.4.0-rc.6', canonical_scenarios=20,
        normal=8, edge=12, native_cells=cells, ordinary=480, calibrations=18,
        real_source_faults=3, cell_model_negative_controls=24, generated_workflow=True,
        delivered_ci_observations=0, human_participants=0, human_usability='unmeasured',
        initial_usability_target_met=False, maintenance_suffix_relocation=True, local_target_absent=True,
        paid_admissions=0, subjects=subjects,
        limitations=[
            'Private engineering qualification of exact v0.4.0-rc.6 archives; not a public release or stable-support claim.',
            'Human beginner usability remains unmeasured; first-use route was agent-assisted.',
            'Git Town admission adds zero delivered-CI triplets; the campaign-level two-project success/failure/recovery gate remains separate.',
            'Admission relies on the independently reviewed V20 artifact audit plus this locally reconstructed, model-tamper-tested exact evidence.'
        ],
        scope='One current-candidate project admission from two exact native RC6 cells, twenty canonical scenarios, 480 passing ordinary executions, 18 required source-fault calibration phases, three distinct real faults, actual model tamper controls, documented authoring/maintenance/relocation, and checked target cleanup. The original ten current-candidate requalification and remaining campaign gates are separate.')
    immutable_json(DOC / 'git-town/admission.json', admission)
    print('Git Town admission evidence prepared: 2 cells, 20 scenarios, 480 ordinary, 18 calibrations, 3 faults, 24 model controls.')


if __name__ == '__main__':
    main()
