"""Rebind corrected case inputs to the verified new runtime without oracle changes."""
import copy
import json
import os
from pathlib import Path
import shutil

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'pdm';target=RAW/'active/pdm';root=RAW/'pdm/runtime-revision/v2'
    activated=json.loads((root/'activated.json').read_text());runtime=json.loads((target/'runtime.json').read_text());ready=json.loads((root/'ready.json').read_text())
    if activated['new_runtime_sha256']!=sha256(target/'runtime.json') or runtime['runtime_directory']!='venv-v2':raise ValueError('verified new runtime selector differs')
    repeated=json.loads((package/'first-use-runtime-v2.json').read_text())
    new_public=package/'normal-minimal-runtime-v2.json'
    if sha256(new_public)!=repeated['spec_sha256'] or repeated['first_attempt']:raise ValueError('actual public repeat absent/changed')
    declaration=package/'scenarios.json';original=json.loads(declaration.read_text())
    if original['development_revision']!=2:raise ValueError('preserve previous runtime case revision')
    prior=RAW/'pdm/declaration-review/v2';prior.mkdir(parents=True,exist_ok=False);shutil.copyfile(declaration,prior/'scenarios.json')
    for case in original['cases']:
        path=package/case['spec']
        if sha256(path)!=case['spec_sha256']:raise ValueError('pre-revision actual contract changed')
        shutil.copyfile(path,prior/case['spec'])
    changed=copy.deepcopy(original);revisions=[];python=Path(runtime['python'])
    for case in changed['cases']:
        if case['id']=='N01':
            old=package/case['spec'];before=json.loads(old.read_text());after=json.loads(new_public.read_text())
            for value in [before,after]:
                value['command'][0]='<explicit owned interpreter>';value['command'][value['command'].index('--python')+1]='<explicit owned interpreter>'
                for step in value['steps']:
                    if 'snapshot' in step:step['snapshot']='<same reviewed screen>'
            if before!=after or sha256(package/'snapshots/normal-minimal.txt')!=sha256(package/'snapshots/normal-minimal-runtime-v2.txt'):raise ValueError('new public repeat changed original interaction or approved oracle bytes')
            case['spec']='normal-minimal-runtime-v2.json';case['spec_sha256']=sha256(new_public)
            revisions.append(dict(case='N01',old_spec='normal-minimal.json',new_spec=case['spec'],actual_repeat=True));continue
        path=package/case['spec'];value=json.loads(path.read_text());before=sha256(path)
        value['command'][0]=os.path.relpath(python,package).replace('\\','/');value['command'][value['command'].index('--python')+1]=str(python)
        path.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n');case['spec_sha256']=sha256(path)
        revisions.append(dict(case=case['id'],before_sha256=before,after_sha256=sha256(path),change='Explicit interpreter/existing-interpreter prerequisite bindings only; every step/oracle unchanged.'))
    changed.update(development_revision=3,pending_import_diagnosis=False,runtime_revision=2,
        runtime_compatibility_declaration='runtime-compatibility-v2.json',public_current_runtime_requalification='first-use-runtime-v2.json')
    declaration.write_text(json.dumps(changed,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'runtime-compatibility-v2.json',dict(schema_version=1,source_pin='201bdc719c15a7c86cc305c0c788fe9cbdef15c3',
        upstream_lock_sha256=sha256(target/'src/pdm.lock'),runtime_constraints=json.loads((root/'declaration.json').read_text())['constraints'],
        original_failure_disposition_sha256=sha256(package/'first-development-disposition.json'),actual_trace_sha256=sha256(RAW/'pdm/import-diagnostic/v2/report.json'),
        original_class_proof_sha256=sha256(root/'original-class-proof.json'),new_runtime_ready_sha256=sha256(root/'ready.json'),actual_compatible_classes=ready['class_proof'],
        original_runtime_and_metadata_preserved=True,revisions=revisions,
        qualification_credit=0,scope='Measured upstream dependency API incompatibility: original unearth0.19 derives from httpx2 while pinned PDM calls httpx.Client.__init__. Actual upstream-lock versions unearth0.18.2/hishel1.2.1 restore the correct class relationship. No target/runner source change, removed import case, relaxed assertion or outcome transfer. Both native cells and every scenario/fault must qualify the exact declared dependency profile.'))
    print('Rebound all20 corrected cases to verified runtimev2; actual public repeat keeps identical screen/state/action oracles; fresh full development still required')


if __name__=='__main__':main()
