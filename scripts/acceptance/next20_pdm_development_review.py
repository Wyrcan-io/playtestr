"""Preserve all first development inputs before correcting proven authoring errors."""
import copy
import argparse
import asyncio
import json
import os
import shutil

from next20_check import RAW,DOC,ROOT,NextCampaign
from next20_candidate import executable
from next20_python_setup import environment
from adversarial_process import execute
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'pdm';raw=RAW/'pdm';declaration=package/'scenarios.json'
    original=json.loads(declaration.read_text());summary_path=raw/'development/1486ad5574d54c3fb1aea943b79ca7a0/summary.json';summary=json.loads(summary_path.read_text())
    if summary['passed']!=15 or summary['failed']!=5 or summary['declaration_sha256']!=sha256(declaration):raise ValueError('actual first development subjects differ')
    destination=raw/'declaration-review/v1'
    if destination.exists():raise ValueError('preserve previous first-development inputs')
    destination.mkdir(parents=True);shutil.copyfile(declaration,destination/'scenarios.json');files={}
    for case in original['cases']:
        path=package/case['spec']
        if sha256(path)!=case['spec_sha256']:raise ValueError('first development spec changed')
        shutil.copyfile(path,destination/case['spec']);files[case['spec']]=sha256(path)
    immutable_json(destination/'inputs.json',dict(schema_version=1,original_declaration_sha256=sha256(declaration),original_development_summary_sha256=sha256(summary_path),files=files,
        scope='Every original development spec and declaration preserved byte-exact before corrections. Fixture/snapshot inputs remain unchanged. First15/5 outcomes never relabelled.'))
    changed=copy.deepcopy(original);revisions=[]
    for case in changed['cases']:
        path=package/case['spec'];value=json.loads(path.read_text());before=sha256(path)
        if case['id'] in {'N02','N08','E06'}:
            index=value['command'].index('--backend')+1
            if value['command'][index]!='pdm':raise ValueError('original invalid backend option differs')
            value['command'][index]='pdm-backend'
        elif case['id']=='N04':
            state=next(s['state'] for s in value['steps'] if s.get('state',{}).get('kind')=='entries' and s['state']['path']=='.')
            if '.gitignore' not in state['entries']:raise ValueError('original local-template wrong entry expectation differs')
            state['entries'].remove('.gitignore')
        else:continue
        path.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        case['spec_sha256']=sha256(path);revisions.append(dict(case=case['id'],before_sha256=before,after_sha256=sha256(path)))
    changed.update(development_revision=2,first_development_disposition='first-development-disposition.json',pending_import_diagnosis=True)
    declaration.write_text(json.dumps(changed,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'first-development-disposition.json',dict(schema_version=1,first_summary=summary_path.relative_to(RAW).as_posix(),first_summary_sha256=sha256(summary_path),
        passed=15,failed=5,all20_target_and_workspace_cleanup_confirmed=all(r['workspace_cleaned'] and r['target_exited'] for r in summary['results']),
        preserved_original_inputs=destination.relative_to(RAW).as_posix(),original_inputs_sha256=sha256(destination/'inputs.json'),revisions=revisions,
        pending_failure=dict(case='N06',actual_category='unexpected_exit',actual_target_error='TypeError: super(type, obj): obj must be an instance or subtype of type',owner='target/dependency investigation pending actual traceback',final_credit=0),
        source_basis='Pinned models/backends.py exposes pdm-backend,not pdm. Local template contains only its declared pyproject/README; it supplies no .gitignore. All already-passing file-byte oracles remain exact and unchanged.',
        scope='Four proven case-authoring fixes,not product repairs. No target/source/dependency change or false success for the unresolved import. Original15/5 remains historical.'))
    diagnostic=raw/'import-diagnostic/v1';diagnostic.mkdir(parents=True)
    value=json.loads((package/'n06.json').read_text());value['command'].insert(4,'-v')
    # Keep fixture paths correct while moving only this unchanged-oracle spec.
    value['workspace']['fixture']='fixture';shutil.copytree(package/'fixtures/n06',diagnostic/'fixture')
    value['command'][0]=os.path.relpath(RAW/'active/pdm/venv/Scripts/python.exe',diagnostic).replace('\\','/')
    immutable_json(diagnostic/'spec.json',value)
    immutable_json(diagnostic/'planned.json',dict(schema_version=1,base_case_sha256=sha256(package/'n06.json'),diagnostic_spec_sha256=sha256(diagnostic/'spec.json'),
        only_semantic_change='Target -v verbosity; unchanged keys/text/expect/exit/state oracles. Fixture bytes verified copied, executable path rebound only.',qualification_credit=0))
    print('Preserved original20cases/15passes5failures; corrected4 proven authoring errors; declared one verbose import diagnosis without weakening oracles')


def prepare_second_diagnostic():
    root=RAW/'pdm/import-diagnostic/v2';root.mkdir(parents=True,exist_ok=False);package=DOC/'pdm'
    value=json.loads((package/'n06.json').read_text());value['command'].insert(5,'-v');value.update(height=120,width=140)
    value['workspace']['fixture']='fixture';shutil.copytree(package/'fixtures/n06',root/'fixture')
    value['command'][0]=os.path.relpath(RAW/'active/pdm/venv/Scripts/python.exe',root).replace('\\','/')
    immutable_json(root/'spec.json',value)
    immutable_json(root/'planned.json',dict(schema_version=1,base_case_sha256=sha256(package/'n06.json'),diagnostic_spec_sha256=sha256(root/'spec.json'),
        prior_diagnostic_sha256=sha256(RAW/'pdm/import-diagnostic/v1/result.json'),
        changes='Put -v after init, as the observed command usage specifies; the global -v was overwritten by subparser defaults and still printed the quiet warning. Enlarge viewport only to retain the full traceback. All keys/text/expect/exit/state oracles unchanged.',
        maximum_additional_diagnostic_executions=1,qualification_credit=0))
    print('Declared one corrected verbose import diagnostic; prior attempt preserved and no qualification credit')


async def diagnose(generation):
    root=RAW/'pdm/import-diagnostic'/('v'+str(generation));spec=root/'spec.json';planned=json.loads((root/'planned.json').read_text())
    if sha256(spec)!=planned['diagnostic_spec_sha256'] or (root/'report.json').exists():raise ValueError('preserve exact original diagnostic; no automatic retries')
    result=await execute([executable('native-exit-v1'),'test','--report',(root/'report.json').relative_to(ROOT),
        '--artifacts-dir',(root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'pdm','verbose-import-original-TypeError-diagnosis',
        cwd=ROOT,env=environment(RAW/'active/pdm'),timeout=150,expected=1,campaign=NextCampaign())
    report=json.loads((root/'report.json').read_text());row=report['results'][0]
    if row['status']!='failed' or row['failure']['category']!='unexpected_exit' or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('actual import diagnostic outcome/cleanup differs')
    immutable_json(root/'result.json',dict(schema_version=1,attempt=result['id'],report_sha256=sha256(root/'report.json'),
        actual_case_status='failed',actual_category=row['failure']['category'],qualification_credit=0,
        scope='Expected rejection is successful diagnosis only; unchanged public state/exit oracles still fail, not a passing application scenario.'))
    print('Preserved actual failed import with verbose traceback; target/workspace cleanup confirmed; no qualification credit')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-diagnostic',action='store_true');parser.add_argument('--prepare-second-diagnostic',action='store_true');parser.add_argument('--generation',type=int,choices=[1,2],default=1);args=parser.parse_args()
    if args.prepare_second_diagnostic:prepare_second_diagnostic()
    elif args.run_diagnostic:asyncio.run(diagnose(args.generation))
    else:main()
