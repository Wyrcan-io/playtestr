"""Declare independent init/update/import/workspace outcomes after public PDM use."""
import base64
import copy
import json
import shutil

from next20_check import DOC
from readiness_evidence import immutable_json,sha256


def expect(value):return dict(expect=value)
def key(value):return dict(key=value)
def answer(value):return [dict(text=value),key('Enter')]


def expected_toml(name='synthetic-notes',version='0.1.0',owner='Ada',email='ada@example.invalid',description='Default template for PDM package',dist=False,dependencies='[]',license_value='"MIT"',extra=''):
    q=lambda value:json.dumps(value,ensure_ascii=False)
    value='[project]\nname = '+q(name)+'\nversion = '+q(version)+'\ndescription = '+q(description)+'\nauthors = [\n    {name = '+q(owner)+',email = '+q(email)+'},\n]\ndependencies = '+dependencies+'\nrequires-python = ">=3.10"\nreadme = "README.md"\nlicense = '+license_value+'\n'
    value+=('\n[build-system]\nrequires = ["pdm-backend"]\nbuild-backend = "pdm.backend"\n\n' if dist else '\n')
    value+='\n[tool.pdm]\ndistribution = '+str(dist).lower()+'\n'+extra
    # Public Windows capture established native text-file newlines. Linux's
    # explicit native profile must change only declared generated text bytes.
    return value.replace('\n','\r\n').encode('utf-8')


def prompts(version='',owner='Ada',email='ada@example.invalid',requires='>=3.10',dist=False,description='A distributable synthetic package'):
    result=[expect('Project version')]+(answer(version) if version else [key('Enter')])
    if dist:result += [expect('Project description'),*answer(description)]
    else:result += [expect('Do you want to build this project'),key('Enter')]
    result += [expect('License(SPDX name)'),key('Enter'),expect('Author name'),*answer(owner),expect('Author email'),*answer(email),expect('Python requires'),*answer(requires)]
    return result


def main():
    package=DOC/'pdm';base=json.loads((package/'normal-minimal.json').read_text())
    if not (package/'first-use.json').is_file() or (package/'scenarios.json').exists():raise ValueError('public route first; preserve every existing declaration')
    cases=[];roots=['fixture']
    def row(cid,spec,task,risk,fixture,combined=(),generated=(),exit_code=0,extra=None):
        path=package/spec;value=json.loads(path.read_text())
        cases.append(dict(id=cid,kind='normal' if cid.startswith('N') else 'edge',spec=spec,task=task,risk=risk,initial_fixture=fixture,
            hosts=['linux','windows'],expected_exit=exit_code,width=value['width'],height=value['height'],spec_sha256=sha256(path),
            combined_risks=list(combined),native_generated_text_paths=list(generated),
            oracle='Independently authored exact complete TOML/generated source/readme bytes, initial-file/Git/sentinel preservation and precise directory entries in this invocation.',**(extra or {})))
    row('N01','normal-minimal.json','Create a minimal application through public review/replay/export','Exact first public TOML and rendered screen','fixture',generated=['pyproject.toml'])
    def add(cid,task,risk,steps,*,dist=False,seed=None,outputs=None,absent=(),directories=(),cwd='.',name='synthetic-notes',template=None,
            flags=(),exit_code=0,python_file=True,combined=(),width=120,height=30,extra=None,generated=None,root_entries=None):
        relative='fixtures/'+cid.lower();roots.append(relative);folder=package/relative;shutil.copytree(package/'fixture',folder)
        for name_,payload in (seed or {}).items():
            path=folder/name_;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
        for name_ in directories:(folder/name_).mkdir(parents=True,exist_ok=True)
        value=copy.deepcopy(base);value.update(name=task,width=width,height=height,timeout_ms=10000);value['workspace'].update(fixture=relative,cwd=cwd)
        value['command']=base['command'][:5]+(['--name',name] if name is not None else [])+['--python',base['command'][base['command'].index('--python')+1],'--no-git','--skip',':all']
        if dist:value['command']+=['--backend','pdm']
        value['command']+=list(flags)+[template or ('default' if dist else 'minimal')]
        value['steps']=copy.deepcopy(steps)+[dict(exit=exit_code)]
        expected=dict(seed or {});expected.update(outputs or {});expected.update({'sentinel.txt':(folder/'sentinel.txt').read_bytes(),'.git/config':(folder/'.git/config').read_bytes()})
        for path,payload in expected.items():value['steps'].append(dict(state=dict(path=path,kind='file',bytes_base64=base64.b64encode(payload).decode())))
        for path in absent:value['steps'].append(dict(state=dict(path=path,kind='absent')))
        for path in directories:
            if path=='pyproject.toml':value['steps'].append(dict(state=dict(path=path,kind='empty_directory')))
        if root_entries is None:
            entries={p.name for p in folder.iterdir()}
            if python_file and cwd=='.':entries.add('.pdm-python')
            if exit_code==0 and cwd=='.':entries.update(['.gitignore','pyproject.toml',*(['README.md','src','tests'] if dist else [])])
        else:entries=set(root_entries)
        value['steps'].append(dict(state=dict(path='.',kind='entries',entries=sorted(entries))))
        filename=cid.lower()+'.json';immutable_json(package/filename,value)
        row(cid,filename,task,risk,relative,combined,generated if generated is not None else list(outputs or {}),exit_code,extra)
    success=[expect('Project is initialized successfully')]
    add('N02','Create a distributable source package with the PDM backend','New package tree,README and build metadata',prompts(dist=True)+success,dist=True,
        outputs={'pyproject.toml':expected_toml(dist=True,description='A distributable synthetic package'),'README.md':b'# synthetic-notes\r\n','src/synthetic_notes/__init__.py':b'','tests/__init__.py':b''})
    old=expected_toml(name='old-notes',dependencies='["packaging>=22"]',extra='\n[tool.synthetic]\nmarker = "keep"\n')
    add('N03','Update project identity/version while preserving declared dependencies','Existing project update retains dependencies and unrelated settings',prompts(version='2.0.0')+success,
        seed={'pyproject.toml':old},outputs={'pyproject.toml':expected_toml(version='2.0.0',dependencies='["packaging>=22"]',extra='\n[tool.synthetic]\nmarker = "keep"\n')})
    local=expected_toml(name='template-seed',description='Locally reviewed template')
    add('N04','Initialize from a reviewed local template and rename its README','Local template merge without Git/network/commands',prompts()+success,template='local-template',
        seed={'local-template/pyproject.toml':local,'local-template/README.md':b'# template-seed\nLocal data\n'},
        outputs={'pyproject.toml':expected_toml(description='Locally reviewed template'),'README.md':b'# synthetic-notes\r\nLocal data\r\n'},
        root_entries={'.git','.gitignore','.pdm-python','local-template','README.md','pyproject.toml','sentinel.txt'},generated=['pyproject.toml','README.md'])
    parent=expected_toml(name='workspace-root')
    add('N05','Create a child project and persist parent workspace membership','Parent/child writes and inherited Python requirement',prompts()+success+[expect('Changes are written to')],
        cwd='packages/child',directories=['packages/child'],seed={'pyproject.toml':parent},python_file=False,
        outputs={'pyproject.toml':parent+b'\r\n[tool.pdm.workspace]\r\nmembers = ["packages/child"]\r\n','packages/child/pyproject.toml':expected_toml()},
        absent=['packages/child/.gitignore','packages/child/.pdm-python'])
    imported=expected_toml(dependencies='[\n    "packaging>=22",\n]')
    add('N06','Initialize then import a synthetic requirements file interactively','A second metadata-changing import without package installation',
        prompts()+success+[expect('Found following files'),expect('Please select'),*answer('0'),expect('Changes are written to')],
        seed={'requirements.txt':b'packaging>=22\n'},outputs={'pyproject.toml':imported},generated=['pyproject.toml'])
    license_project=expected_toml(license_value='{file = "LICENSE"}')
    add('N07','Update a project retaining its declared license-file table','License file representation and unrelated legal bytes remain intact',prompts()+success,
        seed={'pyproject.toml':license_project,'LICENSE':b'Synthetic license fixture\n'},outputs={'pyproject.toml':license_project},generated=['pyproject.toml'])
    add('N08','Explicitly overwrite a conflicting README when generating a package','Reviewed overwrite changes only the intended generated file',prompts(dist=True)+success,
        dist=True,flags=['--overwrite'],seed={'README.md':b'Old owned README\n'},
        outputs={'pyproject.toml':expected_toml(dist=True,description='A distributable synthetic package'),'README.md':b'# synthetic-notes\r\n','src/synthetic_notes/__init__.py':b'','tests/__init__.py':b''})
    correction=[expect('Project name'),*answer('bad name'),expect('Project name is not valid'),dict(resize=dict(width=100,height=30)),expect('Project name'),*answer('synthetic-notes')]
    add('E01','Correct an invalid project name across a viewport resize','Validation/re-entry and resize preserve exact metadata',correction+prompts()+success,name=None,
        outputs={'pyproject.toml':expected_toml()},combined=['invalid-name recovery','resize','saved-state'])
    add('E02','Reject an invalid Python requirement without rewriting existing metadata','Late validation preserves prior configuration and sentinel',prompts(requires='not-a-specifier')+[expect('InvalidSpecifier')],
        seed={'pyproject.toml':old},exit_code=1,combined=['invalid-specifier','existing-state preservation'],generated=[])
    cancellation=dict(native_exit_profile=dict(windows=3221225786,linux=130))
    add('E03','Cancel the first metadata prompt in a small viewport','Native interrupt before project write',
        [expect('Project version'),key('CtrlC')],exit_code=3221225786,width=60,height=12,absent=['pyproject.toml'],
        combined=['interrupt','small viewport','absence oracle'],extra=cancellation,generated=[])
    late=[expect('Project version'),key('Enter'),expect('Do you want to build this project'),key('Enter'),expect('License'),key('Enter'),expect('Author name'),*answer('Ada'),dict(resize=dict(width=100,height=30)),expect('Author email'),key('CtrlC')]
    add('E04','Cancel late in metadata entry while preserving an existing project','Interrupt after input/resize does not commit partial metadata',late,seed={'pyproject.toml':old},exit_code=3221225786,
        combined=['late interrupt','resize','existing configuration'],extra=cancellation,generated=[])
    add('E05','Save a Unicode author exactly','UTF-8 text input and exact native file bytes',prompts(owner='Zo\u00eb \u96ea')+success,
        outputs={'pyproject.toml':expected_toml(owner='Zo\u00eb \u96ea')},combined=['Unicode input','native text-file bytes'])
    long='Long reviewed description '+('wrapped words '*9)
    wrapping=[expect('Project version'),key('Enter'),expect('Project description'),dict(resize=dict(width=40,height=12)),*answer(long),expect('License'),dict(resize=dict(width=100,height=30)),key('Enter'),expect('Author name'),*answer('Ada'),expect('Author email'),*answer('ada@example.invalid'),expect('Python requires'),*answer('>=3.10')]+success
    add('E06','Enter a long description through narrow and widened viewports','Wrapping/resize retains complete input and generated package bytes',wrapping,dist=True,width=80,
        outputs={'pyproject.toml':expected_toml(dist=True,description=long),'README.md':b'# synthetic-notes\r\n','src/synthetic_notes/__init__.py':b'','tests/__init__.py':b''},combined=['long input','wrap','resize','saved package'])
    literal='Ada; $(never-run) & | < >'
    add('E07','Treat shell-looking author text as literal saved metadata','Metacharacters never invoke a shell or rewrite unrelated data',prompts(owner=literal)+success,
        outputs={'pyproject.toml':expected_toml(owner=literal)},absent=['unexpected-command.txt'],combined=['metacharacters','exact file bytes','unrelated-file preservation'])
    add('E08','Reject a local template without project metadata','Local error after prompts, with no remote fallback',prompts()+[expect('Template pyproject.toml not found')],template='broken-template',
        seed={'broken-template/README.md':b'Reviewed local fixture\n'},exit_code=1,absent=['pyproject.toml'],generated=[])
    malformed=b'[project\nname = "broken"\n'
    add('E09','Reject malformed existing TOML without modifying it','Startup parse failure preserves exact original bytes',[],seed={'pyproject.toml':malformed},exit_code=1,python_file=False,generated=[])
    add('E10','Reject malformed local-template TOML after Unicode metadata input','Parse failure,Unicode and owned template cleanup',prompts(owner='Zo\u00eb \u96ea'),template='broken-template',
        seed={'broken-template/pyproject.toml':malformed},exit_code=1,absent=['pyproject.toml'],combined=['malformed template','Unicode input','no partial output'],generated=[])
    add('E11','Handle native EOF at a live prompt','EOF/error distinction and no project output',[expect('Project version'),key('CtrlZ'),key('Enter')],exit_code=1,
        absent=['pyproject.toml'],extra=dict(native_eof_profile=dict(windows=['CtrlZ','Enter'],linux=['CtrlD'])),generated=[])
    add('E12','Reject a directory where pyproject.toml must be a file','Directory collision remains untouched and target exits accurately',[],directories=['pyproject.toml'],exit_code=1,python_file=False,generated=[])
    immutable_json(package/'fixture-git.json',dict(schema_version=1,fixture_roots=roots,directories=['objects','refs','refs/heads'],
        files={n:base64.b64encode((package/'fixture/.git'/n).read_bytes()).decode() for n in ['HEAD','config']},
        scope='Only reviewed synthetic empty Git boundaries reconstructed on fresh checkouts; no Git command, commit,network or target wrapper.'))
    immutable_json(package/'scenarios.json',dict(schema_version=1,project='pdm',source_pin='201bdc719c15a7c86cc305c0c788fe9cbdef15c3',
        normal=8,edge=12,cases=cases,development_revision=1,all_scenarios_qualified=False,real_faults_selected_after_freeze=0,
        oracle='Complete expected TOML and generated file bytes independently authored from reviewed templates/values; no target writer computes assertions. Original public route remains unchanged. Native newline changes are restricted to each declared generated path.'))
    print('Declared PDM20 useful cases:8normal/12edge; actual development/freeze/fault/native evidence still required')


if __name__=='__main__':main()
