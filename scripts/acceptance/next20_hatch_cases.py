"""Declare complete Hatch contracts after independent public-route review."""
import ast
import base64
import copy
import json
from pathlib import Path

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def native(text):return text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8')
def expect(text):return dict(expect=text)
def key(text):return dict(key=text)
def answer(text):return [dict(text=text),expect(text),key('Enter')]


TESTS='''[tool.hatch.envs.types]
extra-dependencies = [
  "mypy>=1.0.0",
]
[tool.hatch.envs.types.scripts]
check = "mypy --install-types --non-interactive {args:src/synthetic_lib tests}"

[tool.coverage.run]
source_pkgs = ["synthetic_lib", "tests"]
branch = true
parallel = true
omit = [
  "src/synthetic_lib/__about__.py",
]

[tool.coverage.paths]
synthetic_lib = ["src/synthetic_lib", "*/synthetic-lib/src/synthetic_lib"]
tests = ["tests", "*/synthetic-lib/tests"]

[tool.coverage.report]
exclude_lines = [
  "no cov",
  "if __name__ == .__main__.:",
  "if TYPE_CHECKING:",
]
'''

CLI_MAIN='''import sys

if __name__ == "__main__":
    from synthetic_lib.cli import synthetic_lib

    sys.exit(synthetic_lib())
'''
CLI_INIT='''import click

from synthetic_lib.__about__ import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="synthetic-lib")
def synthetic_lib():
    click.echo("Hello world!")
'''


def files(root):return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
def states(spec):return {s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in spec['steps'] if s.get('state',{}).get('kind')=='file'}


def main():
    package=DOC/'hatch';target=RAW/'active/hatch';declaration=package/'scenarios.json'
    if declaration.exists() or not (package/'library-public-repaired.json').is_file():raise ValueError('reviewed public flows first; preserve existing declaration')
    plan=json.loads((package/'scenario-plan-v1.json').read_text());tasks={r['id']:r for r in plan['normal']+plan['edge']}
    init=json.loads((package/'normal-init-existing-tables.json').read_text());library=json.loads((package/'normal-library-repaired.json').read_text())
    init_seed=files(package/'fixture-existing-tables');new_seed=files(package/'fixture-library-v2')
    init_out=states(init);new_out=states(library)
    new_out={n:b for n,b in new_out.items() if n.startswith('package/')}
    prefix=init['command'][:4]+['--config','hatch.toml','--cache-dir','cache','--interactive']
    cases=[]
    def add(cid,seed,outputs,command,steps,exit_code=0,generated=None,width=120,height=30,snapshot=None):
        fixture='fixtures/'+cid.lower();folder=package/fixture;folder.mkdir(parents=True,exist_ok=False)
        for name,data in seed.items():
            p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        expected=dict(seed);expected.update(outputs)
        spec=copy.deepcopy(init);spec.update(name=tasks[cid]['task'],width=width,height=height)
        spec['workspace'].update(fixture=fixture,cwd='.')
        spec['command']=prefix+command
        spec['steps']=copy.deepcopy(steps)+[dict(exit=exit_code)]
        if snapshot:spec['steps'].append(dict(snapshot=snapshot))
        directories={'.':set()}
        for name,data in expected.items():
            spec['steps'].append(dict(state=dict(kind='file',path=name,bytes_base64=base64.b64encode(data).decode())))
            parts=Path(name).parts
            for i,part in enumerate(parts):directories.setdefault('/'.join(parts[:i]) or '.',set()).add(part)
        for name,entries in sorted(directories.items()):spec['steps'].append(dict(state=dict(kind='entries',path=name,entries=sorted(entries))))
        name=cid.lower()+'.json';immutable_json(package/name,spec)
        cases.append(dict(id=cid,kind='normal' if cid.startswith('N') else 'edge',spec=name,spec_sha256=sha256(package/name),
            task=tasks[cid]['task'],risk=tasks[cid].get('risks',[tasks[cid].get('outcome','')]),combined_risks=tasks[cid].get('risks',[]),
            initial_fixture=fixture,hosts=['windows','linux'],expected_exit=exit_code,width=width,height=height,
            native_generated_text_paths=list(outputs if generated is None else generated),
            oracle='Complete intended metadata and generated/preserved bytes, all immediate directory entries, positive rendered checkpoints and exact exit. Public base files independently checked before reuse; no target writer executes to calculate expected outcomes.'))
    init_command=['new','--init','synthetic-notes','.']
    init_steps=[expect('Description'),*answer('Synthetic package'),expect('Updated: pyproject.toml')]
    add('N01',init_seed,{'pyproject.toml':init_out['pyproject.toml']},init_command,init_steps,snapshot='normal-init-existing-tables.txt')
    command=['new','--interactive','synthetic-lib','package']
    create_steps=[expect('Description'),*answer('Owned library'),expect('pyproject.toml')]
    add('N02',new_seed,new_out,command,create_steps,snapshot='normal-library-repaired.txt')
    cli=dict(new_out);text=cli['package/pyproject.toml'].decode().replace('\r\n','\n')
    text=text.replace('dependencies = []','dependencies = [\n  "click",\n]')
    text=text.replace('\n\n[tool.hatch.version]','\n\n[project.scripts]\nsynthetic-lib = "synthetic_lib.cli:synthetic_lib"\n\n[tool.hatch.version]')
    cli.update({'package/pyproject.toml':native(text),'package/src/synthetic_lib/__main__.py':native(CLI_MAIN),'package/src/synthetic_lib/cli/__init__.py':native(CLI_INIT)})
    add('N03',new_seed,cli,['new','--interactive','--cli','synthetic-lib','package'],create_steps)
    flat={n.replace('package/src/','package/'):b for n,b in new_out.items()}
    flat['package/pyproject.toml']=flat['package/pyproject.toml'].replace(b'path = "src/',b'path = "')
    seed=dict(new_seed);seed['hatch.toml']=seed['hatch.toml'].replace(b'src-layout = true',b'src-layout = false')
    add('N04',seed,flat,command,create_steps)
    tested=dict(new_out);tested['package/tests/__init__.py']=b''
    tested['package/pyproject.toml']=native(new_out['package/pyproject.toml'].decode().rstrip()+'\n\n'+TESTS)
    seed=dict(new_seed);seed['hatch.toml']=seed['hatch.toml'].replace(b'tests = false',b'tests = true')
    add('N05',seed,tested,command,create_steps)
    # The reviewed upstream CI file is static template data. Freeze it before
    # faults; importing or executing the downloaded target is not involved.
    ci_source=target/'src/src/hatch/template/files_feature_ci.py';tree=ast.parse(ci_source.read_text())
    ci_text=next(ast.literal_eval(n.value) for cls in tree.body if isinstance(cls,ast.ClassDef) for n in cls.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEMPLATE' for t in n.targets))
    ci=dict(new_out);ci['package/.github/workflows/test.yml']=native(ci_text)
    seed=dict(new_seed);seed['hatch.toml']=seed['hatch.toml'].replace(b'ci = false',b'ci = true')
    add('N06',seed,ci,command,create_steps)
    static=b'[project]\nname = "owned-version"\nversion = "1.2.3"\n\n[tool.synthetic]\nkeep = "alpha"\n'
    seed={k:v for k,v in init_seed.items() if k!='pyproject.toml'};seed['pyproject.toml']=static
    add('N07',seed,{'pyproject.toml':native(static.decode().replace('1.2.3','1.2.4'))},['version','patch'],[expect('Old: 1.2.3'),expect('New: 1.2.4')])
    config='''mode = "local"
project = ""
shell = ""
[dirs]
project = []
python = "isolated"
data = "data"
cache = "cache"
env = {}
[projects]
[publish]
[template]
name = "Ada"
email = "ada@example.invalid"
[template.licenses]
headers = false
default = ["Apache-2.0"]
[template.plugins.default]
tests = false
ci = false
src-layout = true
[terminal.styles]
info = "bold"
success = "bold cyan"
error = "bold red"
warning = "bold yellow"
waiting = "bold magenta"
debug = "bold"
spinner = "simpleDotsScrolling"
'''
    config_seed={'hatch.toml':config.encode(),'sentinel.txt':init_seed['sentinel.txt']}
    add('N08',config_seed,{'hatch.toml':native(config.replace('name = "Ada"','name = "Grace"'))},['config','set','template.name'],[expect('Value for `template.name`'),*answer('Grace'),expect('New setting:'),expect('Grace')])
    seed=dict(new_seed);seed['package/existing.txt']=b'owned dirty output\n'
    add('E01',seed,{},command,[expect('is not empty')],exit_code=1)
    seed=dict(new_seed);seed['package']=b'owned output file\n'
    add('E02',seed,{},command,[expect('points to a file')],exit_code=1)
    # Override only the explicit config argv, never fall back to ambient config.
    seed=dict(new_seed)
    add('E03',seed,{},command,[expect('does not exist')],exit_code=1)
    path=package/'e03.json';value=json.loads(path.read_text());value['command'][value['command'].index('hatch.toml')]='missing.toml';path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');cases[-1]['spec_sha256']=sha256(path)
    seed=dict(new_seed);seed['hatch.toml']=seed['hatch.toml'].replace(b'mode = "local"',b'mode = 7')
    add('E04',seed,{},command,[expect('must be a string')],exit_code=1)
    seed=dict(new_seed);seed['hatch.toml']=seed['hatch.toml'].replace(b'name = "Ada"',b'name = 7')
    add('E05',seed,{},command,[expect('Description'),*answer('Owned library'),expect('must be a string')],exit_code=1)
    add('E06',init_seed,{},init_command,[expect('Description'),dict(text='Unsaved edit'),expect('Unsaved edit'),key('CtrlC')],exit_code=1)
    unicode='Zo\u00eb \u96ea e\u0301'
    out=init_out['pyproject.toml'].decode().replace('"Synthetic package"',json.dumps(unicode,ensure_ascii=False))
    add('E07',init_seed,{'pyproject.toml':out.encode()},init_command,[expect('Description'),dict(resize=dict(width=60,height=16)),*answer(unicode),dict(resize=dict(width=120,height=30)),expect('Updated: pyproject.toml')],width=80)
    long='Long reviewed description '+('wrapped words '*12)+'FINAL-MARKER'
    out=init_out['pyproject.toml'].decode().replace('"Synthetic package"',json.dumps(long))
    add('E08',init_seed,{'pyproject.toml':out.encode()},init_command,[expect('Description'),dict(resize=dict(width=40,height=12)),dict(text=long),expect('FINAL-MARKER'),key('Enter'),dict(resize=dict(width=120,height=30)),expect('Updated: pyproject.toml')],width=80)
    quoted='Owned "quoted" notes'
    out=init_out['pyproject.toml'].decode().replace('"Synthetic package"',json.dumps(quoted))
    add('E09',init_seed,{'pyproject.toml':out.encode()},init_command,[expect('Description'),*answer(quoted),expect('Updated: pyproject.toml')])
    old=init_seed['pyproject.toml'].decode().replace('name = "synthetic-notes"','name = "kept-name"\ndescription = "Existing description"\ndependencies = ["packaging>=24"]\ndynamic = ["readme"]')
    seed=dict(init_seed);seed['pyproject.toml']=old.encode()
    updated=old.replace('requires = ["setuptools"]','requires = ["hatchling"]').replace('"setuptools.build_meta"','"hatchling.build"').replace('path = "legacy.py"','path = "synthetic_notes/__init__.py"').replace('dynamic = ["readme"]','dynamic = ["version"]')
    add('E10',seed,{'pyproject.toml':native(updated)},init_command,[expect('Description'),*answer('Ignored replacement'),expect('Updated: pyproject.toml')])
    seed={k:v for k,v in init_seed.items() if k!='pyproject.toml'};seed['pyproject.toml']=static
    add('E11',seed,{},['version','1.0.0'],[expect('not higher than the original version')],exit_code=1)
    seed={k:v for k,v in init_seed.items() if k!='pyproject.toml'}
    add('E12',seed,{},['version','patch'],[expect('No project detected')],exit_code=1)
    if len(cases)!=20 or len({c['id'] for c in cases})!=20:raise ValueError('scenario coverage differs')
    immutable_json(declaration,dict(schema_version=1,project='hatch',source_pin=plan['pin'],normal=8,edge=12,cases=cases,
        scenario_plan_sha256=sha256(package/'scenario-plan-v1.json'),template_scope_extension_sha256=sha256(package/'template-scope-extension.json'),
        static_ci_source_sha256=sha256(ci_source),development_revision=1,all_scenarios_qualified=False,real_faults_selected_after_freeze=0,
        oracle='Reviewed independent complete metadata and exact static generated/preserved payloads; all expected file trees fixed before development. Upstream static CI template treated as reviewed data, not executed. No target writer computes expected assertions.'))
    print('Declared Hatch20 complete contracts:8 normal/12 edge; no faults selected or final/native qualification credit.')


if __name__=='__main__':main()
