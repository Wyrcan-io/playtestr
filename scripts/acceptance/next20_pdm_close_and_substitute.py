"""Close PDM as uncredited discovery and promote an originally screened reserve."""
from collections import Counter
import copy
import hashlib
import json

from next20_check import DOC, RAW
from next20_local_records import read_packet as local_packet
from next20_native_packet_reader import read_packet as native_packet
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    package=DOC/'pdm';require(not any((RAW/'active').iterdir()),'finish all active target cleanup before substitution')
    local_index,local=local_packet('pdm')
    for packet in ['retained-failed-final-v1','retained-complete-final-v2']:
        index,_=local_packet('pdm',packet=packet)
        proof=json.loads((RAW/'pdm'/packet/'expanded-removed.json').read_text(encoding='utf-8-sig'))
        require(proof['all_expanded_removed'] and proof['index_sha256']==sha256(RAW/'pdm'/packet/'index.json'),'closed packet removal proof differs')
    native_index,_=native_packet('pdm',3)
    def documents(relative):
        prefix='pdm/'+relative+'/';values={}
        for name,raw in local.items():
            if name.startswith(prefix) and name.endswith('.json'):values[name]=(json.loads(raw.decode('utf-8-sig')),hashlib.sha256(raw).hexdigest())
        for path in (RAW/'pdm'/relative).rglob('*.json'):
            values[path.relative_to(RAW).as_posix()]=(json.loads(path.read_text(encoding='utf-8-sig')),sha256(path))
        return values
    selected={}
    for name,(row,digest) in documents('cell-readbacks').items():
        if row.get('ordinary_readbacks')==240 and row.get('calibration_readbacks')==9 and row.get('source_runtime_removed'):
            selected[row['host']]=dict(path=name,sha256=digest)
    require(set(selected)=={'windows','linux'},'both complete independently audited removed cells required')
    dependencies=[(n,d) for n,(r,d) in documents('dependency-readbacks').items() if len(r.get('results',[]))==2 and all(v['source_runtime_removed'] and v['reviewed_dependencies']==38 for v in r['results'])]
    require(bool(dependencies),'post-removal actual dependency proof missing')
    controls=[(n,r,d) for n,(r,d) in documents('audit-controls').items() if r.get('semantic_corruptions_rejected')==32]
    require(len(controls)==1 and controls[0][1]['project_admissions']==0,'actual model controls missing')
    missing=json.loads((package/'development-evidence-retention-disposition.json').read_text())
    require(missing['full_original_frame_retention'] is False and missing['first_rendered_frames_unavailable']==['N02','N08','E06'],'historical frame disposition changed')
    immutable_json(package/'qualification-disposition.json',dict(schema_version=1,project='pdm',repository='pdm-project/pdm',
        pin='201bdc719c15a7c86cc305c0c788fe9cbdef15c3',candidate='v0.4.0-rc.6',admitted=False,
        status='uncredited-engineering-discovery-historical-evidence-incomplete',
        reason='Three original invalid-backend development failure screens were overwritten by the former harness. Their reports/launches/consoles remain, but original screen payloads cannot be recovered. Complete admission requires retained first-failure evidence; no silent waiver or recreated-original claim.',
        engineering_observations=dict(final_ordinary=480,final_calibrations=18,real_source_faults=3,native_cells=2,
            development_attempts=120,development_passed=110,development_failed=10,
            rejected_windows_final_attempts=227,rejected_windows_final_passed=226,rejected_windows_final_failed=1,
            separate_startup_diagnostic_executions=50,semantic_evidence_corruptions_rejected=32),
        qualification_credit=dict(projects=0,ordinary=0,calibrations=0,scenarios=0,native_cells=0),
        final_cell_readbacks=selected,dependency_readback=dict(path=dependencies[-1][0],sha256=dependencies[-1][1]),
        actual_model_controls=dict(path=controls[0][0],sha256=controls[0][2]),
        local_record_index_sha256=sha256(RAW/'pdm/retained-local-v1/index.json'),
        native_final_index_sha256=sha256(RAW/'pdm/retained-native-v3/index.json'),
        mandatory_native_dictionary_index_sha256=sha256(RAW/'pdm/retained-native-v2/index.json'),
        retained_windows_source_removed=True,retained_linux_source_removed=True,
        current_execution_source_and_oracles_complete=True,historical_original_frames_complete=False,
        historical_loss_disposition_sha256=sha256(package/'development-evidence-retention-disposition.json'),
        additional_limits=['Recursive README overwrite remains an excluded upstream behavior.','Windows two-second startup boundary failed once; complete replacement and finite diagnostic used explicit five seconds; delay cause unknown.','Transient expanded-retention cap breach remains recorded.'],
        human_participants=0,human_usability='unmeasured',paid_admissions=0,publication='unpublished private candidate',
        scope='Retain all useful workflows,original failures,exact final cell evidence and cleanup. Keep PDM in the attempted denominator and future novelty exclusions; substitute an eligible metadata-only reserve to meet twenty complete admissions.'))
    selection_path=DOC/'selection-declaration.json';before=selection_path.read_bytes();selection=json.loads(before)
    require(len(selection['selected'])==20 and len(selection['reserves'])==8,'unexpected pre-substitution allocation')
    outgoing=next(r for r in selection['selected'] if r['id']=='pdm')
    require('pypa/hatch' in selection['reserves'] and 'chriswalz/bit' not in selection['reserves'],'reserve allocation changed')
    screened=json.loads((DOC/'screening-decisions.json').read_text())['rows']
    hatch=next(r for r in screened if r.get('repository')=='pypa/hatch');bit=next(r for r in screened if r.get('repository')=='chriswalz/bit')
    require(hatch['disposition']=='metadata-reserve' and not hatch['acquired'] and not hatch['admitted'],'incoming target was already exposed/admitted')
    require(bit['disposition']=='screened-not-selected' and 'quota' in bit['reason'] and not bit['fork'] and not bit['archived'],'replacement reserve is ineligible')
    prior=RAW/'screening/selection-history/pdm-hatch-v1';prior.mkdir(parents=True,exist_ok=False)
    (prior/'selection-before.json').write_bytes(before)
    incoming=dict(outgoing,id='hatch',repository='pypa/hatch')
    current=copy.deepcopy(selection);current['selected']=[incoming if r['id']=='pdm' else r for r in selection['selected']]
    current['reserves']=[r for r in selection['reserves'] if r!='pypa/hatch']+['chriswalz/bit']
    current['status']='execution-in-progress-after-explicit-reserve-substitution'
    current['substitution_records']=['substitution-pdm-hatch-v1.json']
    for field,key in [('languages','language_family'),('categories','category')]:require(dict(Counter(r[key] for r in current['selected']))==selection[field],'substitution lost declared diversity allocation')
    require(current['late_transfer']==selection['late_transfer'] and len(set(r['repository'] for r in current['selected']))==20,'late reservation or canonical uniqueness changed')
    after=(json.dumps(current,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
    immutable_json(DOC/'substitution-pdm-hatch-v1.json',dict(schema_version=1,reason='Preserve strict original-evidence completeness while retaining PDM as uncredited discovery.',
        outgoing=dict(id='pdm',repository=outgoing['repository'],qualification_disposition_sha256=sha256(package/'qualification-disposition.json')),
        incoming=dict(id='hatch',repository=hatch['repository'],pin=hatch['pin'],license=hatch['license'],exposure='Original metadata-only reserve; no source acquisition,installation or target execution before this substitution.'),
        replenished_reserve=dict(repository=bit['repository'],pin=bit['pin'],license=bit['license'],original_disposition=bit['disposition'],
            scope='Originally screened feasible additional Git-prompt lead,not an excluded completed identity. Detailed source/workflow/native feasibility still requires review before acquisition.'),
        original_selection_sha256=hashlib.sha256(before).hexdigest(),current_selection_sha256=hashlib.sha256(after).hexdigest(),
        current_selected=20,current_reserves=8,planned_cells_unchanged=selection['planned_cells'],
        language_category_stateful_fullscreen_prompt_allocations_preserved=True,late_transfer_unexposed_and_unchanged=True,
        product_source_changed=False,pdm_failure_history_preserved=True,new_project_admissions=0))
    selection_path.write_bytes(after)
    ledger_path=DOC/'projects.json';ledger=json.loads(ledger_path.read_text());row=next(r for r in ledger['projects'] if r['id']=='pdm')
    row.update(status='uncredited-discovery-historical-frame-loss',admitted=False,current_candidate_qualified=False,
        engineering_final_ordinary_observed=480,engineering_final_calibrations_observed=18,
        rejected_final_window_attempts=227,separate_startup_diagnostics=50,semantic_evidence_controls=32,
        qualification_disposition='pdm/qualification-disposition.json',substituted_by='hatch',source_runtime_removed=True)
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Closed PDM as uncredited discovery with480+18 audited observations; original history retained. Promoted metadata-only Hatch, replenished reserve with originally screened Bit;20 selected/8 reserves, allocation unchanged.')


if __name__=='__main__':main()
