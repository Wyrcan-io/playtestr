"""Apply independently reviewed formatting and scoped supported-workflow corrections."""
import base64
import copy
import json
import shutil
import tomllib

from next20_check import RAW,DOC
from next20_pdm_cases import expected_toml
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'pdm';declaration=package/'scenarios.json';value=json.loads(declaration.read_text())
    summary_path=RAW/'pdm/development/a28c9ffbde86479785b01f52c7917e43/summary.json';summary=json.loads(summary_path.read_text())
    if value['development_revision']!=3 or summary['passed']!=17 or summary['failed']!=3 or summary['declaration_sha256']!=sha256(declaration):raise ValueError('actual second development boundary differs')
    prior=RAW/'pdm/declaration-review/v4';prior.mkdir(parents=True,exist_ok=False);shutil.copyfile(declaration,prior/'scenarios.json')
    for case in value['cases']:shutil.copyfile(package/case['spec'],prior/case['spec'])
    revisions=[]
    for cid in ['N02','N08','E06']:
        root=RAW/'pdm/file-oracle-diagnosis/v1'/cid;review=json.loads((root/'reviewed.json').read_text());diagnostic=json.loads((root/'spec.json').read_text())
        if sha256(root/'spec.json')!=review['diagnostic_spec_after_sha256'] or not review['independently_declared_metadata_matches']:raise ValueError('actual selected-file diagnosis missing/changed')
        case=next(c for c in value['cases'] if c['id']==cid);path=package/case['spec'];spec=json.loads(path.read_text());before=sha256(path)
        description='A distributable synthetic package'
        if cid=='E06':
            text=next(s for s in spec['steps'] if isinstance(s.get('text'),str) and s['text'].startswith('Long reviewed description '))
            if not text['text'].endswith(' '):raise ValueError('original trailing-space fixture anchor differs')
            text['text']=text['text'].rstrip();description=text['text']
        expected=expected_toml(dist=True,description=description)
        observed=base64.b64decode(next(s['state']['bytes_base64'] for s in diagnostic['steps'] if s.get('state',{}).get('path')=='pyproject.toml'))
        if expected!=observed:raise ValueError('independently authored exact TOML still differs from reviewed complete output')
        state=next(s['state'] for s in spec['steps'] if s.get('state',{}).get('path')=='pyproject.toml');state['bytes_base64']=base64.b64encode(expected).decode()
        if cid=='N08':
            if not review['explicit_overwrite_business_outcome_rejected'] or '--overwrite' not in spec['command']:raise ValueError('unsupported overwrite was not actually rejected')
            spec['command'].remove('--overwrite');spec['name']='Generate a source package while preserving an existing owned README'
            state=next(s['state'] for s in spec['steps'] if s.get('state',{}).get('path')=='README.md')
            state['bytes_base64']=base64.b64encode((package/case['initial_fixture']/'README.md').read_bytes()).decode()
            case.update(task=spec['name'],risk='Default non-overwrite branch preserves existing user content while writing new package/source metadata',
                excluded_original_workflow='Explicit --overwrite is broken on this pin; original failed case/reports retained and never credited as successful overwrite.')
            case['native_generated_text_paths'].remove('README.md')
        else:
            if not review['source_literal_readme_matches']:raise ValueError('new-package README output not independently correct')
        path.write_text(json.dumps(spec,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n');case['spec_sha256']=sha256(path)
        revisions.append(dict(case=cid,before_sha256=before,after_sha256=sha256(path),diagnostic_sha256=sha256(root/'reviewed.json')))
    value.update(development_revision=4,unsupported_upstream_workflow='Explicit overwrite recursively drops the overwrite flag; no overwrite compatibility claim.',
        historical_evidence_retention_complete=False,evidence_retention_disposition='development-evidence-retention-disposition.json')
    declaration.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    source=RAW/'active/pdm/src/src/pdm/cli/templates/__init__.py'
    immutable_json(package/'second-development-disposition.json',dict(schema_version=1,actual_second_summary=summary_path.relative_to(RAW).as_posix(),actual_second_summary_sha256=sha256(summary_path),
        passed=17,failed=3,import_now_passed=True,all_target_and_workspace_cleanup_confirmed=all(r['workspace_cleaned'] and r['target_exited'] for r in summary['results']),
        original_contracts=prior.relative_to(RAW).as_posix(),revisions=revisions,upstream_template_source_sha256=sha256(source),
        findings=['Distributable TOML output has two blank lines before tool.pdm; independently checked complete metadata is unchanged.',
            'Rich trims submitted string values; long-input case now omits its accidental trailing space. No output normalization.',
            'Actual explicit overwrite leaves existing README unchanged. Pinned recursive mirror fails to forward overwrite. This route is excluded,not accepted or patched. N08 now covers the independently meaningful default existing-file-preservation workflow.',
            'Three earliest backend-error screen files were overwritten by legacy development paths. All original reports/inputs/consoles survive; do not claim those original rendered bytes are retained. Global/original-evidence gate remains open.'],
        production_or_target_source_changed=False,final_qualification_credit=0))
    print('Applied3 independently reviewed exact-byte/workflow corrections; unsupported overwrite and original-frame loss remain explicit,not passing claims')


if __name__=='__main__':main()
