"""Explicit technical Bundler contracts; ordinary public runner observations."""
import argparse
import asyncio
import base64
import copy
import json
import os
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256

PACKAGE = ROOT/'docs/validation/runner-readiness-ten-project-pass/rubygems'
GEMFILE = b'# reviewed dependency-free project\n'
LOCK = b'GEM\n  specs:\n\nPLATFORMS\n  ruby\n\nDEPENDENCIES\n\nBUNDLED WITH\n   4.1.0.beta2\n'
CONFIG = b'---\nBUNDLE_PATH: "vendor/reviewed"\nBUNDLE_WITHOUT: "development"\n'
SENTINEL = b'reviewed existing work\n'
OPTIONS = ['--no-git','--no-bundle','--no-ci','--no-mit','--no-coc','--no-changelog','--no-linter']


def state(path, value=b'', kind='file'):
    return {'state': {'path':path, 'kind':kind, **(
        {'bytes_base64':base64.b64encode(value).decode()} if kind=='file' else
        {'entries':value} if kind=='entries' else {})}}


def finish(text, code, checks):
    return ([{'expect':text}] if text else [])+[{'exit':code},*checks]


def rows():
    reference=json.loads((PACKAGE/'normal-gem.json').read_text())
    scaffold=[copy.deepcopy(s) for s in reference['steps'] if 'state' in s]
    # Reviewed N01 bytes are reused for the same files in dirty-file scenarios.
    dirty=[s for s in scaffold if s['state']['path']!='atlas/Gemfile']
    dirty.insert(0,state('atlas/Gemfile',b'# preserve original Gemfile\n'))
    saved=[state('Gemfile',GEMFILE),state('sentinel.txt',SENTINEL)]
    gem=['gem','atlas',*OPTIONS,'--test=rspec']
    collision=[{'expect':'Overwrite'}, {'text':'n'}, {'key':'Enter'}]
    init=b'# frozen_string_literal: true\n\nsource "https://rubygems.org"\n\n# gem "rails"\n'
    return [
      ('N04','normal-set-path.json','project-fixture',['config','set','--local','path','vendor/reviewed'],finish('',0,[state('.bundle/config',b'---\nBUNDLE_PATH: "vendor/reviewed"\n'),*saved])),
      ('N05','normal-unset-path.json','config-fixture',['config','unset','--local','path'],finish('',0,[state('.bundle/config',b'---\nBUNDLE_WITHOUT: "development"\n'),*saved])),
      ('N06','normal-lock.json','project-fixture',['lock','--local','--add-platform','ruby','--remove-platform','x64-mingw-ucrt'],finish('Writing lockfile',0,[state('Gemfile.lock',LOCK),*saved])),
      ('N07','normal-check.json','lock-fixture',['check','--dry-run'],finish("The Gemfile's dependencies are satisfied",0,[state('Gemfile.lock',LOCK),*saved])),
      ('N08','normal-init.json','fixture',['init'],finish('Writing new Gemfile',0,[state('Gemfile',init),state('sentinel.txt',SENTINEL)])),
      ('E01','edge-invalid-name.json','fixture',['gem','123invalid',*OPTIONS,'--test=rspec'],finish('Invalid gem name',1,[state('123invalid',kind='absent'),state('sentinel.txt',SENTINEL)])),
      ('E02','edge-decline-overwrite.json','collision-fixture',gem,collision+finish("Gem 'atlas' was successfully created.",0,dirty)),
      ('E03','edge-interrupt.json','fixture',['gem','atlas',*OPTIONS],[{'expect':'Enter a test framework.'},{'key':'CtrlC'},{'exit':1},state('atlas',kind='absent'),state('.bundle-user-config',kind='absent'),state('sentinel.txt',SENTINEL)]),
      ('E04','edge-wrong-type.json','wrong-type-fixture',['gem','blocked/atlas',*OPTIONS,'--test=rspec'],finish('Not a directory',1,[state('blocked',b'reviewed regular file\n'),state('sentinel.txt',SENTINEL)])),
      ('E05','edge-resize-collision.json','collision-fixture',gem,[{'expect':'Overwrite'},{'resize':{'width':40,'height':12}},{'resize':{'width':100,'height':28}},{'text':'n'},{'key':'Enter'}]+finish("Gem 'atlas' was successfully created.",0,dirty)),
      ('E06','edge-unicode-namespace.json','fixture',['gem','caf\u00e9 space/company-atlas',*OPTIONS,'--test=rspec'],finish("Gem 'company-atlas' was successfully created.",0,[state('caf\u00e9 space/company-atlas/lib/company/atlas/version.rb',b'# frozen_string_literal: true\n\nmodule Company\n  module Atlas\n    VERSION = "0.1.0"\n  end\nend\n'),state('sentinel.txt',SENTINEL)])),
      ('E07','edge-missing-dependency.json','missing-fixture',['check'],finish("Bundler can't satisfy",1,[state('Gemfile',b'gem "readiness_missing_fixture", "= 0.0.1"\n'),state('Gemfile.lock',kind='absent'),state('sentinel.txt',SENTINEL)])),
      ('E08','edge-malformed-manifest.json','malformed-fixture',['check'],finish('error parsing',4,[state('Gemfile',b'gem "unfinished\n'),state('Gemfile.lock',LOCK),state('sentinel.txt',SENTINEL)])),
      ('E09','edge-init-existing.json','project-fixture',['init'],finish('already exists',1,[*saved,state('.',[ 'Gemfile','sentinel.txt'],kind='entries')])),
      ('E10','edge-conflicting-policy.json','config-fixture',['config','set','--local','with','development'],finish('cannot be in both',15,[state('.bundle/config',CONFIG),*saved])),
      ('E11','edge-print-lock.json','artifact-fixture',['lock','--local','--print'],finish('BUNDLED WITH',0,[state('Gemfile.lock',LOCK),state('dist/reviewed.bin',b'\x00existing artifact\xff'),*saved])),
      ('E12','edge-build-missing.json','fixture',['build','missing.gemspec'],finish('was not found',1,[state('missing.gemspec',kind='absent'),state('.',['sentinel.txt'],kind='entries'),state('sentinel.txt',SENTINEL)])),
    ]


def author():
    fixtures={
      'project-fixture':{'Gemfile':GEMFILE},
      'config-fixture':{'Gemfile':GEMFILE,'.bundle/config':CONFIG},
      'lock-fixture':{'Gemfile':GEMFILE,'Gemfile.lock':LOCK},
      'artifact-fixture':{'Gemfile':GEMFILE,'Gemfile.lock':LOCK,'dist/reviewed.bin':b'\x00existing artifact\xff'},
      'collision-fixture':{'atlas/Gemfile':b'# preserve original Gemfile\n'},
      'wrong-type-fixture':{'blocked':b'reviewed regular file\n'},
      'missing-fixture':{'Gemfile':b'gem "readiness_missing_fixture", "= 0.0.1"\n'},
      'malformed-fixture':{'Gemfile':b'gem "unfinished\n','Gemfile.lock':LOCK}}
    for folder, files in fixtures.items():
        root=PACKAGE/folder;root.mkdir(exist_ok=False)
        for name,value in {'sentinel.txt':SENTINEL,**files}.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
    reference=json.loads((PACKAGE/'normal-gem.json').read_text())
    contracts=[dict(id='N01',spec='normal-gem.json',sha256=sha256(PACKAGE/'normal-gem.json'))]
    for identity,name,fixture,argv,steps in rows():
        spec=copy.deepcopy(reference)
        spec.update(name='Bundler '+identity, command=['ruby','-EUTF-8','-S','bundle',*argv],
                    workspace=dict(fixture=fixture,home='temporary',temp='temporary'), steps=steps)
        path=PACKAGE/name
        with path.open('x',encoding='utf-8',newline='\n') as output:
            output.write(json.dumps(spec,indent=2,ensure_ascii=True)+'\n')
        contracts.append(dict(id=identity,spec=name,sha256=sha256(path)))
    immutable_json(PACKAGE/'initial-authored-contracts.json',dict(contracts=contracts,
        status='eighteen authored; N02 extension and N03 binary archive review pending; not frozen'))


def environment():
    active=RAW/'active/rubygems'
    runtime=json.loads((active/'runtime.json').read_text())
    ruby=active/runtime['ruby_relative_path']
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',RUBYLIB=str(active/'src/lib'))
    env['PATH']=str(active/'src/exe')+os.pathsep+str(ruby.parent)+os.pathsep+env['PATH']
    return env


async def run(selected):
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    failures=[]
    candidates=[('N01','normal-gem.json'),('N02','normal-extension.json'),('N03','normal-build-gem.json')]+[(r[0],r[1]) for r in rows()]
    for identity,name in candidates:
        if selected and identity not in selected:continue
        if not (PACKAGE/name).exists():continue
        report=RAW/'rubygems/development-results'/(identity+'-'+uuid.uuid4().hex+'.json')
        report.parent.mkdir(parents=True,exist_ok=True)
        try:
            result=await execute([runner,'test','--artifacts-dir',report.with_suffix('').relative_to(ROOT),
                '--report',report.relative_to(ROOT),(PACKAGE/name).relative_to(ROOT)],
                'rubygems','scenario-'+identity,env=environment(),timeout=130,campaign=Campaign())
            outcome=json.loads(report.read_text())['results'][0]
            assert outcome['status']=='passed' and outcome['cleanup']['confirmed_exited'] and outcome['workspace']['cleaned']
            print(identity,'passed',result['id'],flush=True)
        except Exception as error:
            # Each declared scenario is independent; retain every first failure.
            print(identity,'FAILED',str(error),flush=True)
            failures.append(identity)
    print('Inspect independent reports; failures are never counted as passes.',flush=True)
    if failures:raise RuntimeError('unqualified scenarios: '+','.join(failures))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--author',action='store_true')
    parser.add_argument('--case',action='append',default=[]);args=parser.parse_args()
    if args.author:author()
    else:asyncio.run(run(set(args.case)))
