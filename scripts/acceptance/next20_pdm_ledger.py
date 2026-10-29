"""Record actual PDM development separately from immutable admissions."""
import json
from next20_check import DOC, RAW
from readiness_evidence import sha256


def main():
    package=DOC/'pdm';summaries=sorted((RAW/'pdm/development').glob('*/summary.json'))
    if len(summaries)!=4:raise ValueError('four preserved local development windows required')
    local=[json.loads(p.read_text()) for p in summaries]
    native_paths=[package/'linux-first-development-readback.json',package/'linux-second-development-readback.json']
    native=[json.loads(p.read_text()) for p in native_paths]
    if any(v['passed']+v['failed']!=20 for v in local+native):raise ValueError('partial development window')
    ledger_path=DOC/'projects.json';ledger=json.loads(ledger_path.read_text())
    if any(r['id']=='pdm' for r in ledger['projects']):raise ValueError('preserve existing PDM ledger observation')
    row=dict(id='pdm',repository='pdm-project/pdm',pin='201bdc719c15a7c86cc305c0c788fe9cbdef15c3',
        status='development-complete-final-cell-evidence-in-progress-history-gate-open',planned_hosts=['linux','windows'],
        admitted=False,current_candidate_qualified=False,qualified_scenarios=0,qualified_native_cells=0,
        development_selected_scenarios_passed=20,development_ordinary_attempts=120,
        development_ordinary_passed=sum(v['passed'] for v in local+native),development_ordinary_failed=sum(v['failed'] for v in local+native),
        development_real_faults=3,development_fault_matrix_calibrations=9,
        local_development_summaries={p.relative_to(RAW).as_posix():sha256(p) for p in summaries},
        native_development_readbacks={p.relative_to(DOC).as_posix():sha256(p) for p in native_paths},
        historical_evidence_retention_complete=False,first_failure_frame_loss=['N02','N08','E06'],
        excluded_target_behavior='Recursive README overwrite leaves old file; supported preserve-existing workflow tested instead.',
        final_ordinary_executions_qualified=0,final_calibrations_qualified=0,
        scope='All120development attempts remain separate from final repetitions,authoring,maintenance and source-fault calibrations. Original invalid-backend frame loss remains explicit; no admission waiver.')
    if row['development_ordinary_passed']!=110 or row['development_ordinary_failed']!=10:raise ValueError('actual development denominator changed')
    ledger['projects'].append(row)
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Recorded PDM120 development attempts:110pass/10fail; admission/current-candidate counters unchanged.')


if __name__=='__main__':main()
