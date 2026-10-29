"""Project immutable admissions into separate exact-candidate ledger counters."""
import json

from next20_check import DOC
from readiness_evidence import sha256


def candidate_counters(admissions):
    result={};seen=set()
    for admission in admissions:
        candidate=admission.get('candidate');project=admission.get('project')
        if not admission.get('admitted') or not isinstance(candidate,str) or not candidate or not isinstance(project,str) or not project or (candidate,project) in seen:raise ValueError('missing candidate/project or duplicate admission')
        seen.add((candidate,project));row=result.setdefault(candidate,dict(projects=0,ordinary=0,calibrations=0,canonical_scenarios=0,native_cells=0,real_source_faults=0))
        row['projects']+=1
        for key in ['ordinary','calibrations','canonical_scenarios','real_source_faults']:
            value=admission[key]
            if type(value)!=int or value<0:raise ValueError('invalid actual admission counter')
            row[key]+=value
        row['native_cells']+=len(admission['native_cells'])
    return result


def main():
    ledger_path=DOC/'projects.json';ledger=json.loads(ledger_path.read_text());selection=json.loads((DOC/'selection-declaration.json').read_text())
    metadata={r['id']:r for r in json.loads((DOC/'screening-decisions.json').read_text())['rows'] if r.get('id')}
    screened=json.loads((DOC/'screening-decisions.json').read_text())['rows']
    for selected in selection['selected']:
        if selected['id'] in metadata:continue
        matches=[r for r in screened if r.get('repository')==selected['repository']]
        if len(matches)!=1:raise ValueError('selected reserve needs unique original canonical screening identity')
        metadata[selected['id']]=matches[0]
    rows={r['id']:r for r in ledger['projects']};admissions=[];references=[]
    for selected in selection['selected']:
        project=selected['id'];documents=[]
        for path in sorted((DOC/project).glob('admission*.json')):
            document=json.loads(path.read_text())
            if document.get('admitted') is not True:continue
            if document['project']!=project or document['repository']!=selected['repository'] or document['pin']!=metadata[project]['pin']:raise ValueError('admitted canonical project identity differs')
            admissions.append(document);documents.append(document)
            references.append(dict(project=project,candidate=document['candidate'],path=path.relative_to(DOC).as_posix(),sha256=sha256(path)))
        if not documents:continue
        row=rows.get(project)
        if row is None:
            row=dict(id=project,repository=selected['repository'],pin=metadata[project]['pin'],planned_hosts=selected['hosts']);ledger['projects'].append(row);rows[project]=row
        row.update(admitted=True,status='admitted-on-recorded-candidate',candidate_admissions=[r for r in references if r['project']==project],
            current_candidate_qualified=any(d['candidate']==ledger['qualification_candidate'] for d in documents))
    counters=candidate_counters(admissions);current=counters.get(ledger['qualification_candidate'],dict(projects=0,ordinary=0,calibrations=0,canonical_scenarios=0,native_cells=0,real_source_faults=0))
    historical=counters.get(ledger['admission_counters_candidate'])
    if historical is None:raise ValueError('historical counter candidate disappeared')
    # Existing top-level aggregate fields keep their explicitly labelled candidate.
    if any(ledger[field]!=historical[key] for field,key in [('new_project_admissions','projects'),('ordinary_executions','ordinary'),('calibration_executions','calibrations'),('canonical_scenarios','canonical_scenarios'),('native_cells','native_cells'),('real_target_faults','real_source_faults')]):raise ValueError('historical exact-candidate aggregate changed unexpectedly')
    ledger.update(candidate_counters=counters,admission_subjects=references,distinct_new_projects_with_any_candidate_admission=len({a['project'] for a in admissions}),
        current_candidate_new_project_admissions=current['projects'],current_candidate_ordinary_executions_qualified=current['ordinary'],
        current_candidate_calibration_executions_qualified=current['calibrations'],current_candidate_canonical_scenarios=current['canonical_scenarios'],
        current_candidate_native_cells=current['native_cells'],current_candidate_real_source_faults=current['real_source_faults'],
        candidate_scope='Top-level admission aggregates remain historical exact '+ledger['admission_counters_candidate']+'. Current '+ledger['qualification_candidate']+' counters and every per-project candidate admission are separate explicit projections. Historical admissions transfer no current-candidate credit; original-ten current requalification remains separate.')
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Current exact candidate:',ledger['qualification_candidate'],current['projects'],'/20;',current['ordinary'],'ordinary,',current['calibrations'],'calibrations. Historical distinct admitted projects:',ledger['distinct_new_projects_with_any_candidate_admission'])


if __name__=='__main__':main()
