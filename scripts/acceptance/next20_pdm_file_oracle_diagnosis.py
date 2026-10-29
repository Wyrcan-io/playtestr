"""Capture diagnostic copies of disputed file bytes without approving canonical tests."""
import argparse
import asyncio
import base64
import copy
import json
import hashlib
import os
from pathlib import Path
import shutil
import tomllib

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_candidate import executable
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


def prepare():
    package=DOC/'pdm';root=RAW/'pdm/declaration-review/v3';root.mkdir(parents=True,exist_ok=False)
    declaration=json.loads((package/'scenarios.json').read_text());shutil.copyfile(package/'scenarios.json',root/'scenarios.json')
    files={}
    for case in declaration['cases']:
        path=package/case['spec'];shutil.copyfile(path,root/case['spec']);files[case['spec']]=sha256(path)
    frames={}
    for name in ['n02','n04','n06','n08','e06']:
        path=package/(name+'.json.actual.txt')
        if not path.is_file():raise ValueError('remaining actual failure screen missing')
        shutil.copyfile(path,root/path.name);frames[path.name]=sha256(path)
    immutable_json(root/'original-inputs.json',dict(schema_version=1,case_spec_sha256=files,remaining_screen_sha256=frames,
        original_declaration_sha256=sha256(package/'scenarios.json'),
        first_backend_error_original_frames_overwritten=['N02','N08','E06'],
        scope='Current second-window file-mismatch frames and surviving first N04/N06 frames copied before any further executions. Three first-window invalid-option screen files were overwritten by the second series using the legacy helper default. Original reports/attempts/consoles/inputs remain, but those original rendered frame bytes are unavailable; never label a reproduction as original.'))
    source=RAW/'active/pdm/src/src/pdm/cli/templates/default/README.md'
    immutable_json(package/'development-evidence-retention-disposition.json',dict(schema_version=1,
        first_window='1486ad5574d54c3fb1aea943b79ca7a0',second_window='a28c9ffbde86479785b01f52c7917e43',
        original_reports_preserved=True,first_rendered_frames_unavailable=['N02','N08','E06'],
        cause='Legacy development helper omitted --artifacts-dir, allowing repeated failed specs to reuse their adjacent .actual.txt path.',
        current_frame_backup=root.relative_to(RAW).as_posix(),current_frame_backup_sha256=sha256(root/'original-inputs.json'),
        repair='Future development invocations use a unique per-series evidence directory and invocation-specific product artifact paths. Additional historical collision audit remains open.',
        full_original_frame_retention=False,affected_final_qualification_credit=0,
        scope='Honest evidence-retention deviation,not target/runner success. Original failing reports are unchanged; no fabricated raw frame or silently reconstructed history. Keep this boundary in any admission/global closure.'))
    for case,positions in [('N02',[19,20]),('N08',[19,20]),('E06',[21,22])]:
        folder=RAW/'pdm/file-oracle-diagnosis/v1'/case;folder.mkdir(parents=True,exist_ok=False)
        spec=json.loads((package/(case.lower()+'.json')).read_text());shutil.copytree(package/spec['workspace']['fixture'],folder/'fixture')
        spec['workspace']['fixture']='fixture';spec['command'][0]=os.path.relpath(Path(json.loads((RAW/'active/pdm/runtime.json').read_text())['python']),folder).replace('\\','/')
        immutable_json(folder/'spec.json',spec)
        states=[spec['steps'][n-1].get('state',{}).get('path') for n in positions]
        if set(states)!={'pyproject.toml','README.md'}:raise ValueError('diagnostic selected-state anchors differ')
        immutable_json(folder/'planned.json',dict(schema_version=1,case=case,original_spec_sha256=sha256(package/(case.lower()+'.json')),
            diagnostic_spec_before_sha256=sha256(folder/'spec.json'),selected_positions=positions,qualified_credit=0,
            expected_metadata=tomllib.loads(base64.b64decode(next(s['state']['bytes_base64'] for s in spec['steps'] if s.get('state',{}).get('path')=='pyproject.toml')).decode('utf-8')),
            expected_readme_source_sha256=sha256(source),scope='Only a private diagnostic copy may capture disputed file bytes. No canonical approval or new scenario credit. All other actions/oracles must remain identical.'))
    print('Preserved remaining failure frames and declared the3 original overwritten-frame gaps; prepared3 private selected-file diagnostic copies')


def review_capture(case,attempt):
    target=RAW/'active/pdm';root=RAW/'pdm/file-oracle-diagnosis/v1'/case;spec=root/'spec.json';planned=json.loads((root/'planned.json').read_text())
    original=json.loads((DOC/'pdm'/(case.lower()+'.json')).read_text());original['workspace']['fixture']='fixture'
    original['command'][0]=os.path.relpath(Path(json.loads((target/'runtime.json').read_text())['python']),root).replace('\\','/')
    encoded=(json.dumps(original,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
    if hashlib.sha256(encoded).hexdigest()!=planned['diagnostic_spec_before_sha256']:raise ValueError('original diagnostic input cannot be verified exactly')
    actual=json.loads(spec.read_text());expected=copy.deepcopy(original)
    for position in planned['selected_positions']:expected['steps'][position-1]=actual['steps'][position-1]
    if actual!=expected:raise ValueError('diagnostic capture changed unrelated oracle/action')
    captured={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in actual['steps'] if s.get('state',{}).get('kind')=='file'}
    metadata=tomllib.loads(captured['pyproject.toml'].decode('utf-8'));expected_metadata=copy.deepcopy(planned['expected_metadata'])
    if case=='E06':expected_metadata['project']['description']=expected_metadata['project']['description'].rstrip()
    if metadata!=expected_metadata:raise ValueError('actual business metadata differs beyond independently reviewed formatting/input-trim expectation')
    source=target/'src/src/pdm/cli/templates/default/README.md'
    if sha256(source)!=planned['expected_readme_source_sha256']:raise ValueError('reviewed README template changed')
    expected_readme=source.read_bytes().replace(b'example-package',b'synthetic-notes').replace(b'\r\n',b'\n').replace(b'\n',os.linesep.encode())
    readme_matches=captured['README.md']==expected_readme;unsupported_overwrite=False
    if not readme_matches:
        unsupported_overwrite=(case=='N08' and '--overwrite' in original['command'] and captured['README.md']==(root/'fixture/README.md').read_bytes())
        if not unsupported_overwrite:raise ValueError('unexplained actual README mismatch')
    immutable_json(root/'reviewed.json',dict(schema_version=1,case=case,attempt=attempt,diagnostic_spec_after_sha256=sha256(spec),
        independently_declared_metadata_matches=True,source_literal_readme_matches=readme_matches,explicit_overwrite_business_outcome_rejected=unsupported_overwrite,
        canonical_spec_changed=False,actual_native_file_sha256={path:hashlib.sha256(payload).hexdigest() for path,payload in captured.items()},qualification_credit=0))
    print(case,'actual diagnostic reviewed:', 'upstream explicit overwrite failed; old README preserved,not an accepted overwrite' if unsupported_overwrite else 'complete metadata and literal README correct; disputed byte formatting/input trim remains separate',flush=True)


async def run(selected):
    target=RAW/'active/pdm';env=environment(target);runner=executable('native-exit-v1')
    for case in [selected]:
        root=RAW/'pdm/file-oracle-diagnosis/v1'/case;spec=root/'spec.json';planned=json.loads((root/'planned.json').read_text())
        if sha256(spec)!=planned['diagnostic_spec_before_sha256'] or (root/'reviewed.json').exists():raise ValueError('preserve diagnostic attempt,do not automatically retry')
        original=json.loads(spec.read_text());controls=['/update-state '+str(n) for n in planned['selected_positions']]+['/review','/replay','/save']
        result=await execute([runner,'record','--edit',spec.relative_to(ROOT)],'pdm','inspect-disputed-synthetic-file-bytes-'+case,
            cwd=ROOT,env=env,input='\n'.join(controls+['']),timeout=180,campaign=NextCampaign())
        review_capture(case,result['id'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');parser.add_argument('--review-existing',action='store_true');parser.add_argument('--case',choices=['N02','N08','E06'],default='E06');args=parser.parse_args()
    if args.review_existing:
        matches=[]
        for path in (RAW/'events').glob('*-started.json'):
            value=json.loads(path.read_text())
            if value.get('project')=='pdm' and value.get('label')=='inspect-disputed-synthetic-file-bytes-'+args.case:matches.append(value)
        if len(matches)!=1:raise ValueError('ambiguous original diagnostic capture')
        finish=json.loads((RAW/'events'/(matches[0]['id']+'-finished.json')).read_text())
        if finish['category']!='passed' or finish['exit_code']!=0 or finish['harness_cleanup']!='harness_process_reaped':raise ValueError('original capture did not complete')
        review_capture(args.case,matches[0]['id'])
    elif args.run:asyncio.run(run(args.case))
    else:prepare()
