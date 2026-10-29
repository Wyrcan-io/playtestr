"""Review a cached-license package-generation route against predeclared outcomes."""
import asyncio
import argparse
import base64
import json
import os
from pathlib import Path
import tomllib

from adversarial_process import execute
from next20_candidate import executable
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


README='''# synthetic-lib

[![PyPI - Version](https://img.shields.io/pypi/v/synthetic-lib.svg)](https://pypi.org/project/synthetic-lib)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/synthetic-lib.svg)](https://pypi.org/project/synthetic-lib)

-----

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install synthetic-lib
```

## License

`synthetic-lib` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.
'''


async def main(generation):
    target=RAW/'active/hatch';package=DOC/'hatch';raw=RAW/'hatch'/('library-public-v'+str(generation));spec=package/('normal-library.json' if generation==1 else 'normal-library-repaired.json')
    if raw.exists() or spec.exists():raise ValueError('preserve every generation window')
    extension=json.loads((package/'template-scope-extension.json').read_text())
    license_file=package/extension['owned_cache_file']
    if sha256(license_file)!=extension['owned_cache_sha256']:raise ValueError('reviewed cache changed')
    runtime=json.loads((target/'runtime.json').read_text());python=Path(runtime['python']);runner=executable('native-exit-v1')
    inventory=json.loads((target/'installed-inventory.json').read_text())['files']
    for name,digest in inventory.items():
        if sha256(target/'venv'/name)!=digest:raise ValueError('reviewed runtime changed')
    fixture_name='fixture-library' if generation==1 else 'fixture-library-v2'
    fixture=package/fixture_name;(fixture/'cache/licenses').mkdir(parents=True,exist_ok=False);raw.mkdir(parents=True)
    config=b'mode = "local"\n[template]\nname = "Ada"\nemail = "ada@example.invalid"\n[template.licenses]\nheaders = false\ndefault = ["Apache-2.0"]\n[template.plugins.default]\ntests = false\nci = false\nsrc-layout = true\n'
    sentinel=b'unrelated synthetic data\n'
    for name,data in [('hatch.toml',config),('sentinel.txt',sentinel),('cache/licenses/Apache-2.0.txt',license_file.read_bytes())]:
        with (fixture/name).open('xb') as stream:stream.write(data)
    classifiers=['Development Status :: 4 - Beta','Programming Language :: Python',
        *['Programming Language :: Python :: '+x for x in ['3.8','3.9','3.10','3.11','3.12']],
        'Programming Language :: Python :: Implementation :: CPython','Programming Language :: Python :: Implementation :: PyPy']
    expected={'build-system':{'requires':['hatchling'],'build-backend':'hatchling.build'},
        'project':{'name':'synthetic-lib','dynamic':['version'],'description':'Owned library','readme':'README.md',
        'requires-python':'>=3.8','license':'Apache-2.0','keywords':[],'authors':[{'name':'Ada','email':'ada@example.invalid'}],
        'classifiers':classifiers,'dependencies':[],'urls':{'Documentation':'https://github.com/Ada/synthetic-lib#readme',
        'Issues':'https://github.com/Ada/synthetic-lib/issues','Source':'https://github.com/Ada/synthetic-lib'}},
        'tool':{'hatch':{'version':{'path':'src/synthetic_lib/__about__.py'}}}}
    native=lambda text:text.replace('\n','\r\n').encode() if os.name=='nt' else text.encode()
    files={'package/README.md':native(README),'package/LICENSE.txt':native(license_file.read_text(encoding='utf-8')),
        'package/src/synthetic_lib/__about__.py':native('__version__ = "0.0.1"\n'),'package/src/synthetic_lib/__init__.py':b'',
        'hatch.toml':config,'sentinel.txt':sentinel}
    entries={'package':{'LICENSE.txt','README.md','pyproject.toml','src'},'package/src':{'synthetic_lib'},'package/src/synthetic_lib':{'__about__.py','__init__.py'}}
    controls=['/expect Description','/text "Owned library"','/expect Owned library','/key Enter','/expect pyproject.toml','/exit 0','/snapshot normal-library.txt','/file package/pyproject.toml',
        '/file package/README.md','/file package/LICENSE.txt','/file package/src/synthetic_lib/__about__.py','/file package/src/synthetic_lib/__init__.py',
        '/entries package','/entries package/src','/entries package/src/synthetic_lib','/file hatch.toml','/file sentinel.txt','/review','/replay','/save']
    controls[6]='/snapshot '+('normal-library.txt' if generation==1 else 'normal-library-repaired.txt')
    immutable_json(raw/'planned.json',dict(schema_version=1,controls=controls,expected_complete_toml=expected,window=generation,
        expected_files={n:base64.b64encode(b).decode() for n,b in files.items()},expected_entries={n:sorted(v) for n,v in entries.items()},
        scope_extension_sha256=sha256(package/'template-scope-extension.json'),runner_sha256=sha256(runner),runtime_sha256=sha256(target/'runtime.json'),
        scope='Additional prepared public route, not a replacement unfamiliar-user measurement or final qualification. Entire intended metadata and all selected generated/preserved bytes declared before launch.'))
    campaign=NextCampaign();env=environment(target)
    args=[runner,'record','--output',spec.relative_to(ROOT),'--fixture',fixture_name,'--temporary-home','--temporary-temp',
        '--width','120','--height','30','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in {'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','PYTHONNOUSERSITE':'1'}.items():args+=['--env',name+'='+value]
    args+=['--',os.path.relpath(python,package).replace('\\','/'),'-B','-m','hatch','--config','hatch.toml','--cache-dir','cache','--interactive','new','synthetic-lib','package']
    if generation==2:args.insert(args.index('synthetic-lib'),'--interactive')
    recorded=await execute(args,'hatch','cached-library-public-record-review-replay-export',cwd=ROOT,env=env,input='\n'.join(controls+['']),timeout=150,campaign=campaign)
    approved=json.loads(spec.read_text());states={s['state']['path']:s['state'] for s in approved['steps'] if 'state' in s}
    actual=base64.b64decode(states['package/pyproject.toml']['bytes_base64'],validate=True)
    if tomllib.loads(actual.decode('utf-8'))!=expected:raise ValueError('captured complete package metadata differs from independent oracle')
    for name,data in files.items():
        if base64.b64decode(states[name]['bytes_base64'],validate=True)!=data:raise ValueError('generated/preserved bytes differ: '+name)
    for name,names in entries.items():
        if set(states[name]['entries'])!=names:raise ValueError('generated directory differs: '+name)
    report=raw/'ordinary-report.json'
    ordinary=await execute([runner,'test','--report',report,'--artifacts-dir',raw/'ordinary-artifacts',spec],
        'hatch','cached-library-reviewed-ordinary-test',cwd=ROOT,env=env,timeout=150,campaign=campaign)
    row=json.loads(report.read_text())['results'][0]
    if row['status']!='passed' or not all(s['status']=='passed' for s in row['steps']) or not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:raise ValueError('ordinary generated-package route incomplete/unclean')
    immutable_json(package/('library-public.json' if generation==1 else 'library-public-repaired.json'),dict(schema_version=1,status='prepared-additional-public-route-passed-not-admitted',window=generation,
        attempts=[recorded['id'],ordinary['id']],shell_invocations=2,recorder_controls=len(controls),spec_sha256=sha256(spec),report_sha256=sha256(report),
        plan_sha256=sha256(raw/'planned.json'),scope_extension_sha256=sha256(package/'template-scope-extension.json'),human_participants=0,
        project_admissions=0,final_ordinary_credit=0,source_fault_credit=0))
    print('Cached-license library record/review/replay/export/ordinary passed with complete independent metadata,generated files,entries and cleanup checks.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,choices=[1,2],default=1);args=parser.parse_args();asyncio.run(main(args.generation))
