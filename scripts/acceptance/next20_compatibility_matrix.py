"""Summarize actual admitted native cells separately from proposed host coverage."""
from datetime import datetime,timezone
import json

from next20_check import DOC, RAW, ROOT
from next20_verify_jrnl import validate,require
from readiness_evidence import sha256


def main():
    selection=json.loads((DOC/'selection-declaration.json').read_text())
    ledger=json.loads((DOC/'projects.json').read_text());rows={r['id']:r for r in ledger['projects']}
    matrix=[];counts=dict(linux=0,windows=0,macos=0)
    for selected in selection['selected']:
        project=selected['id'];row=rows.get(project,{})
        record=dict(project=project,repository=selected['repository'],planned_hosts=selected['hosts'],
            admitted=False,qualified_native_cells=[])
        if row.get('admitted'):
            path=DOC/row['admission'];admission=json.loads(path.read_text())
            require(admission['admitted'] and admission['project']==project and admission['repository']==selected['repository'],'matrix admission identity differs')
            models=[]
            for model_path in (RAW/project/'audits').glob('*/actual-model.json'):
                require(model_path.stat().st_size<=4*1024**2,'matrix native model bound')
                model=json.loads(model_path.read_text());validate(model);models.append((model_path,model))
            require(len(models)==len(admission['native_cells']) and len({m['host'] for _,m in models})==len(models),'matrix duplicate/incomplete actual native models')
            for model_path,model in sorted(models,key=lambda item:item[1]['host']):
                cell=next(c for c in admission['native_cells'] if c['host']==model['host'])
                require(cell['ordinary']==240 and model['project']==project,'matrix ordinary/project identity differs')
                record['qualified_native_cells'].append(dict(host=model['host'],run=model['run'],
                    tooling_source_revision=model['revision'],runner_sha256=model['runner_sha256'],
                    candidate_archive_sha256=model['archive_sha256'],ordinary=cell['ordinary'],
                    calibrations_including_probes=cell['calibrations'],
                    native_model=model_path.relative_to(ROOT).as_posix(),native_model_sha256=sha256(model_path)))
                counts[model['host']]+=1
            record.update(admitted=True,pin=admission['pin'],admission=row['admission'],admission_sha256=sha256(path))
        matrix.append(record)
    require(sum(r['admitted'] for r in matrix)==ledger['new_project_admissions'],'matrix/ledger admitted count differs')
    result=dict(schema_version=1,observed_at_utc=datetime.now(timezone.utc).isoformat(),
        candidate='unchanged exact v0.4.0-rc.5',new_project_admissions=ledger['new_project_admissions'],
        qualified_host_cells=counts,planned_host_cells=selection['planned_cells'],projects=matrix,
        scope='Actual admitted cells and validated individual models only. Proposed hosts supply no compatibility credit. Earlier partial/failed cells remain in each project disposition. Full final campaign hash closure remains separate.')
    (DOC/'compatibility-matrix.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Current admitted native matrix:',counts,'projects:',ledger['new_project_admissions'],'; proposed cells remain separate.')


if __name__=='__main__':main()
