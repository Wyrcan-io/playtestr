"""Check the actual TOML reference behavior behind the retained sparse-init failure."""
import asyncio
import base64
import json
import tomllib

from adversarial_process import execute
from next20_check import RAW,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    target=RAW/'active/hatch';package=DOC/'hatch';spec=package/'normal-init.json'
    planned=RAW/'hatch/first-use-v1/planned.json'
    value=json.loads(spec.read_text());state=next(s['state'] for s in value['steps'] if s.get('state',{}).get('path')=='pyproject.toml')
    actual=tomllib.loads(base64.b64decode(state['bytes_base64'],validate=True).decode('utf-8'))
    expected=json.loads(planned.read_text())['expected_complete_toml']
    if actual==expected or actual.get('project')!={} or actual.get('tool',{}).get('hatch')!={}:raise ValueError('retained original sparse failure differs')
    code='''import tomlkit
d=tomlkit.parse('[tool.synthetic]\\nkeep="alpha"\\n')
p={}
d['project']=p
p['name']='synthetic-notes'
assert dict(d['project'])=={}
existing=tomlkit.parse('[project]\\nname="synthetic-notes"\\n')
existing.get('project')['description']='Synthetic package'
assert existing['project']['description']=='Synthetic package'
print('Confirmed actual installed tomlkit: newly assigned dict is detached; existing table mutation persists.')
'''.replace('\\n','\n')
    # Keep escape sequences inside the child program's string literals.
    code=code.replace("'[tool.synthetic]\nkeep=\"alpha\"\n'", "'[tool.synthetic]\\nkeep=\"alpha\"\\n'")
    code=code.replace("'[project]\nname=\"synthetic-notes\"\n'", "'[project]\\nname=\"synthetic-notes\"\\n'")
    result=await execute([target/'venv/Scripts/python.exe','-B','-c',code],'hatch','actual-tomlkit-sparse-table-reference-diagnostic',
        cwd=target,env=environment(target),timeout=30,campaign=NextCampaign())
    immutable_json(package/'initial-authoring-failure.json',dict(schema_version=1,status='initial-public-route-failed-independent-state-review',
        original_wrapper='0838339de39949d187fb9473bf185e01',original_spec_sha256=sha256(spec),original_plan_sha256=sha256(planned),
        actual_complete_toml=actual,independently_expected_complete_toml=expected,diagnostic_attempt=result['id'],
        source_file='src/hatch/project/core.py',source_sha256=sha256(target/'src/src/hatch/project/core.py'),
        explanation='Project.initialize assigns ordinary empty dicts into tomlkit, then mutates the detached Python dict. Existing TOML tables remain attached. Sparse route is unsupported with this pinned source/runtime; no target source patch or weakened state oracle.',
        initial_shell_invocations=2,initial_recorder_controls=14,initial_ordinary_pass=False,
        repaired_receipt_sha256=sha256(package/'first-use-repaired.json'),repaired_shell_invocations=3,repaired_recorder_controls=14,
        cumulative_shell_invocations=5,cumulative_recorder_controls=28,initial_twenty_control_target_met=False,
        scope='Failed initial usability observation remains failed. Repaired engineering flow passed in an explicitly separate window; no unfamiliar-human or project-admission credit.'))
    print('Retained sparse-init failure and reproduced detached-table mechanism; repaired window remains separate.')


if __name__=='__main__':asyncio.run(main())
