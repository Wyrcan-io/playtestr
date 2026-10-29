"""First public Hatch recorder route with independent complete metadata oracles."""
import asyncio
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import tomllib

from adversarial_process import execute
from next20_candidate import executable
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main(generation):
    target=RAW/'active/hatch';package=DOC/'hatch';raw=RAW/'hatch'/('first-use-v'+str(generation))
    spec=package/('normal-init.json' if generation==1 else 'normal-init-existing-tables.json')
    if raw.exists() or spec.exists():raise ValueError('preserve original first-use window')
    runtime=json.loads((target/'runtime.json').read_text());python=Path(runtime['python']);runner=executable('native-exit-v1')
    if sha256(python)!=runtime['python_sha256']:raise ValueError('reviewed interpreter changed')
    inventory=json.loads((target/'installed-inventory.json').read_text())['files']
    for name,digest in inventory.items():
        if sha256(target/'venv'/name)!=digest:raise ValueError('reviewed runtime changed')
    primary=json.loads((package/'source-provenance.json').read_text())['files']
    actual={p.relative_to(target/'src').as_posix():sha256(p) for p in (target/'src').rglob('*') if p.is_file()}
    if any(actual.get(n)!=d for n,d in primary.items()) or set(actual)-set(primary)!={'src/hatch/_version.py'}:raise ValueError('unreviewed generated/source change')
    generated=target/'src/src/hatch/_version.py'
    generated_proof=dict(schema_version=1,
        primary_source_provenance_sha256=sha256(package/'source-provenance.json'),
        generated_files={'src/hatch/_version.py':dict(sha256=sha256(generated),bytes=generated.stat().st_size,role='Actual hatch-vcs generated private pin-derived version module; not a primary Git blob.')},
        editable_path_only_pth_sha256=sha256(target/'venv/Lib/site-packages/_editable_impl_hatch.pth') if os.name=='nt' else sha256(next((target/'venv/lib').rglob('_editable_impl_hatch.pth'))))
    generated_manifest=package/'runtime-generated-source.json'
    if generated_manifest.exists():
        if json.loads(generated_manifest.read_text())!=generated_proof:raise ValueError('generated source proof changed')
    else:immutable_json(generated_manifest,generated_proof)
    raw.mkdir(parents=True);fixture_name='fixture' if generation==1 else 'fixture-existing-tables';fixture=package/fixture_name;fixture.mkdir()
    config=b'mode = "local"\n[template]\nname = "Ada"\nemail = "ada@example.invalid"\n[template.licenses]\nheaders = false\ndefault = []\n'
    seed=b'[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n\n[tool.synthetic]\nkeep = "alpha"\n'
    if generation==2:seed+=b'\n[project]\nname = "synthetic-notes"\n\n[tool.hatch.version]\npath = "legacy.py"\n'
    sentinel=b'unrelated synthetic data\n'
    for name,data in [('hatch.toml',config),('pyproject.toml',seed),('sentinel.txt',sentinel)]:
        with (fixture/name).open('xb') as stream:stream.write(data)
    expected={'build-system':{'requires':['hatchling'],'build-backend':'hatchling.build'},
        'project':{'name':'synthetic-notes','description':'Synthetic package','dynamic':['version']},
        'tool':{'synthetic':{'keep':'alpha'},'hatch':{'version':{'path':'synthetic_notes/__init__.py'}}}}
    controls=['/expect Description','/text "Synthetic package"','/expect Synthetic package','/key Enter',
        '/expect Updated: pyproject.toml','/exit 0','/snapshot normal-init.txt','/file pyproject.toml','/file hatch.toml',
        '/file sentinel.txt','/entries .','/review','/replay','/save']
    snapshot_name='normal-init.txt' if generation==1 else 'normal-init-existing-tables.txt'
    controls[6]='/snapshot '+snapshot_name
    immutable_json(raw/'planned.json',dict(schema_version=1,expected_complete_toml=expected,controls=controls,initial_window=generation==1,
        runner_sha256=sha256(runner),runtime_sha256=sha256(target/'runtime.json'),handwritten_playtestr_json=False,
        scope='Prepared agent route, no human study or native/project admission. Built-in existing pyproject update bypasses templates/license downloads and environment creation.'))
    campaign=NextCampaign();env=environment(target);attempts=[]
    async def run(argv,label,input=None):
        result=await execute(argv,'hatch',label,cwd=ROOT,env=env,input=input,timeout=150,campaign=campaign);attempts.append(result['id']);return result
    version=await run([runner,'--version'],'hatch-first-use-runner-version')
    if version['output'].strip()!='playtestr v0.4.0-rc.6':raise ValueError('wrong candidate version')
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture',fixture_name,'--temporary-home','--temporary-temp',
        '--width','120','--height','30','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in {'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','PYTHONNOUSERSITE':'1','PYTHON_KEYRING_BACKEND':'keyring.backends.null.Keyring'}.items():argv+=['--env',name+'='+value]
    argv+=['--',os.path.relpath(python,package).replace('\\','/'),'-B','-m','hatch','--config','hatch.toml','--interactive','new','--init','synthetic-notes','.']
    await run(argv,'hatch-first-public-record-review-replay-export','\n'.join(controls+['']))
    approved=json.loads(spec.read_text());states={s['state']['path']:s['state'] for s in approved['steps'] if 'state' in s}
    payload=base64.b64decode(states['pyproject.toml']['bytes_base64'],validate=True)
    if tomllib.loads(payload.decode('utf-8'))!=expected:raise ValueError('complete captured metadata differs from independent declared oracle')
    for name,data in [('hatch.toml',config),('sentinel.txt',sentinel)]:
        if base64.b64decode(states[name]['bytes_base64'],validate=True)!=data:raise ValueError('unrelated fixture changed')
    if states['.']['kind']!='entries' or set(states['.']['entries'])!={'hatch.toml','pyproject.toml','sentinel.txt'}:raise ValueError('unexpected generated file set')
    report=raw/'ordinary-report.json'
    await run([runner,'test','--report',report,'--artifacts-dir',raw/'ordinary-artifacts',spec],'hatch-first-reviewed-ordinary-test')
    row=json.loads(report.read_text())['results'][0]
    if row['status']!='passed' or not all(s['status']=='passed' for s in row['steps']) or not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('ordinary route incomplete/unclean')
    for name,digest in inventory.items():
        if sha256(target/'venv'/name)!=digest:raise ValueError('runtime changed during route')
    immutable_json(package/('first-use.json' if generation==1 else 'first-use-repaired.json'),dict(schema_version=1,status='prepared-public-agent-route-passed-not-admitted',initial_window=generation==1,
        candidate='v0.4.0-rc.6',attempts=attempts,shell_invocations=3,recorder_controls=len(controls),handwritten_playtestr_json=False,
        runner_sha256=sha256(runner),runtime_sha256=sha256(target/'runtime.json'),spec_sha256=sha256(spec),ordinary_report_sha256=sha256(report),
        independently_expected_complete_toml=expected,approved_file_sha256=hashlib.sha256(payload).hexdigest(),human_time='unmeasured',human_participants=0,
        confounders=['Prepared synthetic fixture','Agent read upstream implementation','Owned reviewed interpreter explicitly supplied'],
        scope='First prepared agent public route only. No compatibility/admission or beginner-usability claim.'))
    print('Hatch public record/review/replay/export/ordinary route passed;3 shell invocations,14 recorder controls; full independent TOML/preserved files/entries/cleanup checks.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,choices=[1,2],default=1);args=parser.parse_args();asyncio.run(main(args.generation))
