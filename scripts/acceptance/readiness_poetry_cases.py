"""Technical author route: reviewed local Poetry workflows, public assertions only."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256

PACKAGE=ROOT/'docs/validation/runner-readiness-ten-project-pass/poetry'
SEED=b'''# preserve this reviewed comment
[project]
name = "fixture-app"
version = "1.2.3"
description = "Reviewed local fixture"
requires-python = ">=3.10"
readme = "README.md"
authors = [{name = "Fixture Author", email = "author@example.invalid"}]
dependencies = []

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
'''
SOURCE=b'\n[[tool.poetry.source]]\nname = "private"\nurl = "https://packages.example.invalid/simple/"\npriority = "explicit"\n'


def state(path,kind='file',value=b''):
    value={'path':path,'kind':kind,**({'bytes_base64':base64.b64encode(value).decode()} if kind=='file' else {'entries':value} if kind=='entries' else {})}
    return {'state':value}


def answer(value=''):
    return ([{'text':value}] if value else [])+[{'key':'Enter'}]


def wizard(final='yes',author=None,description=None,resize=False):
    steps=[{'expect':'Version ['}]
    if resize:steps += [{'resize':{'width':80,'height':20}},{'resize':{'width':100,'height':28}}]
    steps+=answer()
    if description is not None:steps += [{'expect':'Description ['},*answer(description)]
    steps += [{'expect':'Author ['}]
    if author:
        steps += answer('broken <unclosed')+[{'expect':'Invalid author string'},*answer(author)]
    else:steps+=answer()
    steps += [{'expect':'Would you like to define your main dependencies interactively?'},*answer('n'),
              {'expect':'Would you like to define your development dependencies interactively?'},*answer('n'),
              {'expect':'Do you confirm generation?'},*answer(final)]
    return steps


def init_args(description=True):
    return ['init','--name','atlas',*(['--description','Fixture project'] if description else []),
            '--author','Fixture Author <author@example.invalid>','--python','>=3.10','--license','MIT']


def normal_metadata(name='atlas',description='Fixture project',scaffold=False):
    # Literal reviewed layout, not a call to Poetry's output implementation.
    text=f'''[project]
name = "{name}"
version = "0.1.0"
description = "{description}"
authors = [
    {{name = "Fixture Author",email = "author@example.invalid"}}
]
license = "MIT"
'''+('readme = "README.md"\n' if scaffold else '')+'''requires-python = ">=3.10"
dependencies = [
]
'''+('''
[tool.poetry]
packages = [{include = "company", from = "src"}]
''' if scaffold else '\n')+'''
[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
'''
    return text.replace('\n',os.linesep).encode()


def rows():
    saved=[state('pyproject.toml',value=SEED),state('sentinel.txt',value=b'reviewed existing work\n')]
    def done(message,code,checks):return ([{'expect':message}] if message else [])+[{'exit':code},*checks]
    def scaffold(destination):
        return [state(destination+'/pyproject.toml',value=normal_metadata('company-service',scaffold=True)),
          state(destination,'entries',['README.md','pyproject.toml','src','tests']),
          state(destination+'/src','entries',['company']),state(destination+'/src/company','entries',['service']),
          state(destination+'/src/company/service/__init__.py',value=b''),
          state(destination+'/tests/__init__.py',value=b''),state(destination+'/README.md',value=b'')]
    new=['new','--interactive','--name','company.service','--description','Fixture project','--author',
         'Fixture Author <author@example.invalid>','--python','>=3.10','--license','MIT']
    return [
      ('N02','normal-new-namespace.json','fixture',[*new,'nested/atlas'],wizard()+done('Created package company.service',0,scaffold('nested/atlas'))),
      ('N03','normal-version.json','project-fixture',['version','minor'],done('Bumping version from 1.2.3 to 1.3.0',0,[state('pyproject.toml',value=SEED.replace(b'1.2.3',b'1.3.0')),saved[1]])),
      ('N04','normal-local-config.json','project-fixture',['config','virtualenvs.in-project','true','--local'],done('',0,[state('poetry.toml',value=('[virtualenvs]\nin-project = true\n').replace('\n',os.linesep).encode()),*saved])),
      ('N05','normal-source-add.json','project-fixture',['source','add','--priority=explicit','private','https://packages.example.invalid/simple/'],done('Adding source with name private.',0,[state('pyproject.toml',value=SEED+SOURCE+b'\n'),saved[1]])),
      ('N06','normal-source-remove.json','source-fixture',['source','remove','private'],done('Removing source with name private.',0,[state('pyproject.toml',value=b'tool.poetry.source = []\n'+SEED+b'\n'),saved[1]])),
      ('N07','normal-check.json','project-fixture',['check','--strict'],done('All set!',0,saved)),
      ('E01','edge-author-recovery.json','fixture',init_args(),wizard(author='Fixture Author <author@example.invalid>')+done('',0,[state('pyproject.toml',value=normal_metadata()),saved[1]])),
      ('E02','edge-decline-generation.json','fixture',init_args(),wizard(final='no')+done('Command aborted',1,[state('pyproject.toml','absent'),saved[1],state('.','entries',['sentinel.txt'])])),
      ('E03','edge-interrupt.json','fixture',init_args(),[{'expect':'Version ['},*answer(),{'expect':'Author ['},{'key':'CtrlC'},{'exit':1},state('pyproject.toml','absent'),saved[1]]),
      ('E04','edge-nonempty-destination.json','collision-fixture',[*new,'nested/atlas'],done('exists and is not empty',1,[state('nested/atlas/keep.txt',value=b'reviewed original\n'),state('nested/atlas','entries',['keep.txt']),state('nested/atlas/pyproject.toml','absent')])),
      ('E05','edge-resize-long-description.json','fixture',init_args(False),wizard(description='Reviewed long description '+('wide content '*20).strip(),resize=True)+done('',0,[state('pyproject.toml',value=normal_metadata(description='Reviewed long description '+('wide content '*20).strip())),saved[1]])),
      ('E06','edge-unicode-namespace.json','fixture',[*new,'caf\u00e9 space/atlas'],wizard()+done('Created package company.service',0,scaffold('caf\u00e9 space/atlas')+[saved[1]])),
      ('E07','edge-invalid-version.json','project-fixture',['version','definitely-invalid-version'],done('Invalid PEP 440 version',1,saved)),
      ('E08','edge-dry-run-preserves.json','artifact-fixture',['version','major','--dry-run'],done('Bumping version from 1.2.3 to 2.0.0',0,[*saved,state('dist/reviewed.bin',value=b'\x00existing artifact\xff'),state('dist','entries',['reviewed.bin'])])),
      ('E09','edge-wrong-type.json','wrong-type-fixture',init_args(),done('',1,[state('pyproject.toml','directory'),state('pyproject.toml/keep.txt',value=b'reviewed directory\n'),saved[1]])),
      ('E10','edge-source-case-update.json','source-fixture',['source','add','--priority=supplemental','PRIVATE','https://packages.example.invalid/simple/'],done('already exists. Updating.',0,[state('pyproject.toml',value=SEED+SOURCE.replace(b'"private"',b'"PRIVATE"').replace(b'"explicit"',b'"supplemental"')+b'\n'),saved[1]])),
      ('E11','edge-missing-source.json','source-fixture',['source','remove','missing'],done('Source with name missing was not found.',1,[state('pyproject.toml',value=SEED+SOURCE),saved[1]])),
      ('E12','edge-missing-readme.json','missing-readme-fixture',['check','--strict'],done('README.md',1,saved+[state('README.md','absent'),state('fixture_app/__init__.py',value=b'# reviewed source\n')]))]


def author():
    if (PACKAGE/'scenario-contracts-initial.json').exists():raise RuntimeError('preserve initial contracts')
    fixtures={
        'project-fixture':{'pyproject.toml':SEED,'README.md':b'Reviewed package\n','fixture_app/__init__.py':b'# reviewed source\n'},
        'source-fixture':{'pyproject.toml':SEED+SOURCE,'README.md':b'Reviewed package\n'},
        'collision-fixture':{'nested/atlas/keep.txt':b'reviewed original\n'},
        'artifact-fixture':{'pyproject.toml':SEED,'README.md':b'Reviewed package\n','dist/reviewed.bin':b'\x00existing artifact\xff'},
        'wrong-type-fixture':{'pyproject.toml/keep.txt':b'reviewed directory\n'},
        'missing-readme-fixture':{'pyproject.toml':SEED,'fixture_app/__init__.py':b'# reviewed source\n'}}
    for folder,files in fixtures.items():
        root=PACKAGE/folder;root.mkdir(exist_ok=False)
        for name,value in {'sentinel.txt':b'reviewed existing work\n',**files}.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
    reference=json.loads((PACKAGE/'normal-init.json').read_text())
    contracts=[dict(id='N01',spec='normal-init.json',spec_sha256=sha256(PACKAGE/'normal-init.json'))]
    for identity,name,fixture,argv,steps in rows():
        spec={k:v for k,v in reference.items() if k not in {'steps','command','name','workspace'}}
        spec.update(name='Poetry '+identity,command=['poetry','--no-plugins',*argv],
          workspace=dict(fixture=fixture,home='temporary',temp='temporary'),steps=steps)
        path=PACKAGE/name
        if path.exists():raise RuntimeError('refuse contract overwrite')
        path.write_text(json.dumps(spec,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
        contracts.append(dict(id=identity,spec=name,spec_sha256=sha256(path)))
    immutable_json(PACKAGE/'scenario-contracts-initial.json',dict(contracts=contracts,
        status='nineteen authored; N08 archive review pending; not frozen',holdout_selected=False))
    print('Nineteen declared contracts authored; N08 remains pending independent archive review.')


async def run(selected):
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    env=dict(os.environ)
    env['PATH']=str(RAW/'active/poetry/venv'/('Scripts' if os.name=='nt' else 'bin'))+os.pathsep+env['PATH']
    env['PYTHONDONTWRITEBYTECODE']='1'
    candidates=[('N01','normal-init.json'),('N08','normal-build-sdist.json')]+[(r[0],r[1]) for r in rows()]
    for identity,name in candidates:
        if selected and identity not in selected:continue
        report=RAW/'poetry/development-results'/(identity+'-'+uuid.uuid4().hex+'.json')
        report.parent.mkdir(parents=True,exist_ok=True)
        result=await execute([runner,'test','--artifacts-dir',report.with_suffix('').relative_to(ROOT),
            '--report',report.relative_to(ROOT),(PACKAGE/name).relative_to(ROOT)],'poetry','scenario-'+identity,
            env=env,timeout=130,campaign=Campaign())
        outcome=json.loads(report.read_text())['results'][0]
        if outcome['status']!='passed' or not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
            raise RuntimeError('scenario outcome/cleanup unqualified')
        print(identity,'passed',result['id'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--author',action='store_true')
    parser.add_argument('--case',action='append',default=[]);args=parser.parse_args()
    if args.author:author()
    else:asyncio.run(run(set(args.case)))
