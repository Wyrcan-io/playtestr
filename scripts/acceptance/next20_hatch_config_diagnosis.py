"""Capture disputed config bytes in a private copy without approving the original."""
import asyncio
import base64
import json
import os
import shutil
import tomllib

from adversarial_process import execute
from next20_candidate import executable
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    package=DOC/'hatch';target=RAW/'active/hatch';root=RAW/'hatch/config-diagnosis-v1';root.mkdir(parents=True,exist_ok=False)
    original=package/'n08.json';value=json.loads(original.read_text());before=sha256(original)
    shutil.copytree(package/value['workspace']['fixture'],root/'fixture');value['workspace']['fixture']='fixture'
    python=json.loads((target/'runtime.json').read_text())['python'];value['command'][0]=os.path.relpath(python,root).replace('\\','/')
    spec=root/'private.json';immutable_json(spec,value)
    state=next(s['state'] for s in value['steps'] if s.get('state',{}).get('path')=='hatch.toml')
    expected=base64.b64decode(state['bytes_base64']);expected_values=tomllib.loads(expected.decode('utf-8'))
    immutable_json(root/'planned.json',dict(schema_version=1,original_spec_sha256=before,private_spec_before_sha256=sha256(spec),
        expected_complete_config=expected_values,controls=['/update-state 8','/review','/replay','/save'],
        scope='Diagnostic copy only. Original failed case/report/frame/expectation unchanged. Capture is not evidence that disputed bytes are correct; compare complete intended config values.'))
    result=await execute([executable('native-exit-v1'),'record','--edit',spec],'hatch','private-selected-config-byte-diagnostic',
        cwd=ROOT,env=environment(target),input='/update-state 8\n/review\n/replay\n/save\n',timeout=150,campaign=NextCampaign())
    updated=json.loads(spec.read_text());actual=base64.b64decode(updated['steps'][7]['state']['bytes_base64'])
    actual_values=tomllib.loads(actual.decode('utf-8'))
    if sha256(original)!=before:raise ValueError('original approval changed during private diagnosis')
    immutable_json(root/'observed.json',dict(schema_version=1,attempt=result['id'],original_unchanged=True,
        expected_hex=expected.hex(),actual_hex=actual.hex(),expected_complete_config=expected_values,actual_complete_config=actual_values,
        complete_semantics_equal=actual_values==expected_values,original_spec_approval_changed=False))
    print('Config diagnostic: complete intended values equal:',actual_values==expected_values)
    print('EXPECTED',repr(expected));print('ACTUAL',repr(actual))


if __name__=='__main__':asyncio.run(main())
