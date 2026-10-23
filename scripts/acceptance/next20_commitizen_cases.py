"""Declare independently expected useful configuration outcomes after public use."""
import base64
import copy
import json
import shutil

from next20_check import DOC, RAW
from next20_fixture_git import reconstruct
from readiness_evidence import immutable_json, sha256


PROMPTS=['supported config file:', 'choose a cz (commit rule):', 'source of the version:',
    'Choose version scheme:', 'correct version format:', 'Create changelog automatically', 'Keep major version zero']


def initialization(*,file_down=0,jira=False,tag=None,changelog=True,major=True,cancel=None,resize=False,correct=False):
    steps=[]
    for index,prompt in enumerate(PROMPTS):
        steps.append(dict(expect=prompt))
        if cancel==index:return steps+[dict(key='CtrlC'),dict(expect='Stopped by user')]
        if index==0:steps += [dict(key='ArrowDown') for _ in range(file_down)]
        if index==1 and jira:steps += [dict(key='ArrowDown'),dict(key='ArrowDown')]
        if index==4 and tag is not None:
            steps.append(dict(text=tag+('X' if correct else '')))
            if correct:steps.append(dict(key='Backspace'))
            if resize:steps += [dict(resize=dict(width=100,height=30)),dict(expect='correct version format:')]
        if index==5 and not changelog:steps.append(dict(text='n'));continue
        if index==6 and not major:steps.append(dict(text='n'));continue
        steps.append(dict(key='Enter'))
    return steps+[dict(expect='Configuration complete')]


def expected_toml(*,jira=False,tag='$version',changelog=True,major=True,scheme='semver2',provider=None,prefix=b''):
    lines=['[tool.commitizen]', 'name = '+json.dumps('cz_jira' if jira else 'cz_conventional_commits'),
        'tag_format = '+json.dumps(tag,ensure_ascii=False),'version_scheme = '+json.dumps(scheme)]
    lines += ['version_provider = '+json.dumps(provider)] if provider else ['version = "0.0.1"']
    if changelog:lines.append('update_changelog_on_bump = true')
    if major:lines.append('major_version_zero = true')
    return prefix+('\n'.join(lines)+'\n').encode('utf-8')


def main():
    package=DOC/'commitizen-python'
    if not (package/'first-use-portable.json').is_file() or (package/'scenarios.json').exists():raise ValueError('public route first; existing declaration cannot be overwritten')
    template=json.loads((package/'normal-init-portable.json').read_text());cases=[];roots=['fixture']
    for cid,name,task in [('N01','normal-init-portable.json','Create default hidden TOML configuration'),
                          ('N02','normal-plain-toml.json','Choose plain TOML filename and approve final rendered screen')]:
        cases.append(dict(id=cid,kind='normal',spec=name,task=task,risk='Exact saved defaults and '+('reviewed screen' if cid=='N02' else 'public authoring'),initial_fixture='fixture',expected_exit=0,hosts=['linux','windows'],combined_risks=[],spec_sha256=sha256(package/name)))
    def add(cid,task,risk,steps,expected=None,filename='.cz.toml',seed=None,exit_code=0,width=120,height=32,combined=None,directory=False):
        relative='fixtures/'+cid.lower();roots.append(relative);folder=package/relative
        shutil.copytree(package/'fixture',folder)
        for name,data in (seed or {}).items():(folder/name).write_bytes(data)
        if directory:(folder/filename).mkdir()
        spec=copy.deepcopy(template);spec.update(name=task,width=width,height=height,timeout_ms=10000)
        spec['workspace']['fixture']=relative;spec['steps']=steps+[dict(exit=exit_code)]
        if directory:spec['steps'].append(dict(state=dict(path=filename,kind='directory')))
        elif expected is not None:spec['steps'].append(dict(state=dict(path=filename,kind='file',bytes_base64=base64.b64encode(expected).decode())))
        else:spec['steps'].append(dict(state=dict(path=filename,kind='absent')))
        sentinel=(folder/'sentinel.txt').read_bytes()
        spec['steps'] += [dict(state=dict(path='sentinel.txt',kind='file',bytes_base64=base64.b64encode(sentinel).decode())),
            dict(state=dict(path='.',kind='entries',entries=sorted({'.git','sentinel.txt',*(seed or {}),*([filename] if expected is not None or directory else [])})))]
        output=package/(cid.lower()+'.json');immutable_json(output,spec)
        cases.append(dict(id=cid,kind='normal' if cid.startswith('N') else 'edge',spec=output.name,task=task,risk=risk,initial_fixture=relative,expected_exit=exit_code,hosts=['linux','windows'],combined_risks=combined or [],spec_sha256=sha256(output)))
    expected_json=(b'{\n  "commitizen": {\n    "name": "cz_conventional_commits",\n    "tag_format": "$version",\n'
        b'    "version_scheme": "semver2",\n    "version": "0.0.1",\n    "update_changelog_on_bump": true,\n    "major_version_zero": true\n  }\n}')
    expected_yaml=(b'---\ncommitizen:\n  major_version_zero: true\n  name: cz_conventional_commits\n'
        b'  tag_format: $version\n  update_changelog_on_bump: true\n  version: 0.0.1\n  version_scheme: semver2\n')
    add('N03','Create JSON configuration with exact ordered defaults','Different supported serialization',initialization(file_down=2),expected_json,filename='.cz.json')
    add('N04','Create YAML configuration with exact defaults','Different supported serialization',initialization(file_down=4),expected_yaml,filename='.cz.yaml')
    add('N05','Choose Jira commit convention and persist it','Associate selected convention with saved name',initialization(jira=True),expected_toml(jira=True))
    add('N06','Opt out of automatic changelog generation','Explicit negative confirmation omits enabled setting',initialization(changelog=False),expected_toml(changelog=False))
    add('N07','Opt out of keeping major version zero','Explicit negative confirmation preserves other defaults',initialization(major=False),expected_toml(major=False))
    add('N08','Save a custom release tag format','Text input is persisted exactly',initialization(tag='release-$version'),expected_toml(tag='release-$version'))
    add('E01','Cancel before choosing a configuration file','Cancellation without partial creation',initialization(cancel=0),exit_code=25)
    add('E02','Cancel after selecting filename, convention and provider','Prior prompt progress must not create a partial file',initialization(jira=True,cancel=3),exit_code=25,combined=['multi-step selection','cancellation','absence'])
    original=expected_toml(tag='existing-$version',changelog=False)
    add('E03','Preserve an existing valid configuration','Existing project must not be silently reinitialized',[dict(expect='already exists')],original,seed={'.cz.toml':original})
    broken=b'[tool.commitizen\nname = "invalid"\n'
    add('E04','Reject malformed existing TOML without rewriting it','Pre-interaction validation and exact failure exit',[dict(expect='Failed to parse')],broken,seed={'.cz.toml':broken},exit_code=19)
    add('E05','Refuse writing a configuration where a directory exists','Wrong type survives failed completion',initialization()[:-1]+[dict(expect='Traceback (most recent call last)')],exit_code=1,directory=True,combined=['interactive success path','wrong output type','preservation'])
    unicode_tag='r\u00e9l_\u96ea-$version'
    add('E06','Persist Unicode version-format input exactly','UTF-8 input/rendering/saved bytes',initialization(tag=unicode_tag),expected_toml(tag=unicode_tag),combined=['Unicode text','template punctuation','saved UTF-8'])
    long_tag='release-'+('a'*65)+'-$version'
    add('E07','Correct wrapped long input and resize before accepting it','Backspace and resize preserve the intended value',initialization(tag=long_tag,resize=True,correct=True),expected_toml(tag=long_tag),width=40,height=12,combined=['wrapped input','Backspace correction','resize','saved exact value'])
    add('E08','Initialize correctly in a small terminal viewport','Wrapped questionary prompts retain selection',initialization(),expected_toml(),width=40,height=12,combined=['small viewport','wrapped prompts','saved defaults'])
    initial=b'[project]\nname = "synthetic-owned"\nversion = "1.2.3"\n'
    add('E09','Add Commitizen settings to existing project metadata','Preserve unrelated project fields and choose detected provider',initialization(),expected_toml(scheme='pep440',provider='pep621',prefix=initial+b'\n'),filename='pyproject.toml',seed={'pyproject.toml':initial},combined=['existing metadata','automatic provider choice','exact preservation'])
    literal='release-$version; echo synthetic>unexpected.txt'
    add('E10','Keep shell-looking tag-format text as saved data','Input punctuation must not create another file',initialization(tag=literal),expected_toml(tag=literal),combined=['literal punctuation','non-execution','exact entry set'])
    add('E11','Cancel at the final confirmation after custom text','No partially accepted configuration survives',initialization(tag='not-saved-$version',cancel=6),exit_code=25,combined=['custom input','late cancellation','absence'])
    unknown=b'[tool.commitizen]\nname = "unavailable_synthetic_rule"\n'
    add('E12','Reject an unavailable configured convention without changes','Visible setup error with exact nonzero exit',[dict(expect='committer has not been found')],unknown,seed={'.cz.toml':unknown},exit_code=1)
    git_path=package/'fixture-git.json';old=git_path.read_bytes();saved=RAW/'commitizen-python/declaration-review/fixture-git-v1.json';saved.parent.mkdir(parents=True)
    with saved.open('xb') as stream:stream.write(old)
    git=json.loads(old);git['fixture_roots']=roots;git['revision']=2;git_path.write_text(json.dumps(git,indent=2)+'\n',encoding='utf-8');reconstruct(package)
    immutable_json(package/'scenarios.json',dict(schema_version=1,project='commitizen-python',source_pin='b78d581f7e3089fa40bcd4794591fd56b43b671a',normal=8,edge=12,cases=cases,development_revision=1,
        exact_oracle='Independently declared complete configuration bytes, sentinel preservation and exact entry sets; no target writer used to calculate expected state.',
        initial_route='Original three/twenty local route preserved; selected portable route remeasured separately three/twenty after removing unnecessary personal venv PATH.',
        all_scenarios_qualified=False,real_faults_selected_after_freeze=0))
    print('Declared twenty useful Commitizen tasks, eight normal/twelve edge. No final/fault/native credit.')


if __name__=='__main__':main()
