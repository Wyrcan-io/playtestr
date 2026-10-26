"""Promote only an actually admitted project and recompute qualified counters."""
import argparse
import json

from next20_check import DOC,RAW


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    ledger_path=DOC/'projects.json';ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    rows=[r for r in ledger['projects'] if r['id']==args.project]
    if len(rows)!=1:raise ValueError('missing/ambiguous selected ledger project')
    admission_path=DOC/args.project/'admission.json';admission=json.loads(admission_path.read_text(encoding='utf-8'))
    if not admission['admitted'] or admission['project']!=args.project or admission['pin']!=rows[0]['pin'] or admission['repository']!=rows[0]['repository']:
        raise ValueError('actual admitted identity differs from selected project')
    if (RAW/'active'/args.project).exists():raise ValueError('local target must be checked/removed before promotion')
    models=[json.loads(p.read_text(encoding='utf-8')) for p in (RAW/args.project/'audits').glob('*/actual-model.json')]
    revisions={m['revision'] for m in models};runs={m['run'] for m in models}
    if len(revisions)!=1 or len(runs)!=1:raise ValueError('actual native models require one qualified source/run')
    rows[0].update(status='admitted',admitted=True,qualified_scenarios=admission['canonical_scenarios'],
        qualified_native_cells=len(admission['native_cells']),native_run=next(iter(runs)),native_source=next(iter(revisions)),
        audited_native_cells=len(admission['native_cells']),audited_ordinary_executions=admission['ordinary'],
        audited_calibration_executions=admission['calibrations'],additional_terminal_only_probes=admission.get('additional_terminal_only_probes',0),
        local_target_absent=True,maintenance='Actual diagnosis, selected/cancelled approval, suffix pruning and byte-identical relocation passed; first attempts preserved.',
        admission=args.project+'/admission.json',delivered_ci_observations=admission.get('delivered_ci_observations',0))
    admitted=[]
    for row in ledger['projects']:
        if row.get('admitted'):
            document=json.loads((DOC/row['admission']).read_text(encoding='utf-8'))
            if not document['admitted'] or document['project']!=row['id']:raise ValueError('ledger contains an unverified admission')
            admitted.append(document)
    ledger.update(status='new-project-admissions-in-progress',new_project_admissions=len(admitted),
        ordinary_executions=sum(a['ordinary'] for a in admitted),calibration_executions=sum(a['calibrations'] for a in admitted),
        canonical_scenarios=sum(a['canonical_scenarios'] for a in admitted),native_cells=sum(len(a['native_cells']) for a in admitted),
        real_target_faults=sum(a['real_source_faults'] for a in admitted),
        additional_terminal_only_probes=sum(a.get('additional_terminal_only_probes',0) for a in admitted))
    ledger['observed_audited_ordinary_executions']=ledger['ordinary_executions']
    ledger['observed_audited_calibration_executions']=ledger['calibration_executions']
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Recorded actual admissions:',len(admitted),'/',ledger['new_project_target'],'ordinary:',ledger['ordinary_executions'],'mandatory calibrations:',ledger['calibration_executions'],'separate probes:',ledger['additional_terminal_only_probes'])


if __name__=='__main__':main()
