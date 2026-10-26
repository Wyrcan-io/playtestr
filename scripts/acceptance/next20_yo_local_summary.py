"""Record actual local yo progress without granting native admission credit."""
import json

from next20_check import RAW, ROOT, DOC
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'yo';raw=RAW/'yo'
    development=[]
    for path in sorted((raw/'development').glob('*/summary.json')):
        value=json.loads(path.read_text())
        development.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha256(path),
            passed=value['passed'],failed=value['failed']))
    if sorted((row['passed'],row['failed']) for row in development)!=[(18,2),(20,0)]:
        raise ValueError('Require exact complete original/replacement development series')
    faults=list((raw/'faults').glob('*/summary.json'));journeys=list(raw.glob('maintenance-*/journey.json'))
    if len(faults)!=1 or len(journeys)!=1:raise ValueError('Require one complete fault and maintenance journey')
    matrix=json.loads(faults[0].read_text())
    if matrix['real_faults']!=3 or matrix['calibrations']!=10:raise ValueError('Local fault denominator differs')
    references=[faults[0],journeys[0],package/'first-use.json',package/'snapshot-authoring.json',
        package/'development-test-freeze.json',package/'first-development-disposition.json',
        package/'final-series-declaration.json',raw/'retained-catalogs-v1/index.json',
        raw/'retained-catalogs-v1/expanded-removed.json',RAW/'active/yo/npm-metadata-retention/index.json']
    immutable_json(package/'local-progress.json',dict(schema_version=1,project='yo',admitted=False,
        development=development,local_real_faults=3,local_calibration_observations=10,
        public_first_use_commands=3,public_first_use_controls=16,technical_snapshot_commands=3,technical_snapshot_controls=19,
        native_cells=0,final_ordinary_executions=0,new_project_admissions=0,
        public_maintenance='Actual complete journey retained, including two-command diagnosis and unchanged Unicode relocation.',
        subjects={p.relative_to(ROOT).as_posix():sha256(p) for p in references},
        remaining='Native complete series, independent full cell audits/corruptions, local retained report audit, bounded storage, confirmed source/runtime cleanup and final project admission.'))
    path=DOC/'projects.json';ledger=json.loads(path.read_text())
    if any(row['id']=='yo' for row in ledger['projects']):raise ValueError('Preserve existing yo ledger row')
    provenance=json.loads((package/'source-provenance.json').read_text())
    ledger['projects'].append(dict(id='yo',repository='yeoman/yo',pin=provenance['pin'],status='local-passed-native-pending',
        development_selected_scenarios_passed=20,development_ordinary_attempts=40,
        development_ordinary_passed=38,development_ordinary_failed=2,development_real_faults=3,
        development_fault_matrix_calibrations=9,additional_terminal_only_probes=1,
        planned_hosts=['linux','windows'],native_cells=0,ordinary_executions=0,admitted=False))
    if ledger['new_project_admissions']!=3:raise ValueError('Unexpected admitted campaign baseline')
    path.write_text(json.dumps(ledger,sort_keys=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Recorded local yo progress only; campaign stays3/20 new admissions,13/100 cumulative.')


if __name__=='__main__':main()
