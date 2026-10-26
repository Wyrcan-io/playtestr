"""Declare useful local-template cases only after the real public first route."""
import base64
import copy
import json
import shutil

from next20_check import DOC
from readiness_evidence import immutable_json,sha256


def expect(value):return dict(expect=value)
def key(value):return dict(key=value)
def answer(value):return [dict(text=value),key('Enter')]


def main():
    package=DOC/'cargo-generate'
    if not (package/'first-use.json').is_file():raise ValueError('complete public route before handwritten cases')
    if (package/'scenarios.json').exists():raise ValueError('preserve existing case declaration')
    template=json.loads((package/'normal-project.json').read_text());cases=[]
    def row(cid,filename,task,risk,fixture,combined=None):
        actual=json.loads((package/filename).read_text())
        cases.append(dict(id=cid,kind='normal' if cid.startswith('N') else 'edge',spec=filename,
            task=task,risk=risk,initial_fixture=fixture,expected_exit=0,hosts=['linux','windows'],
            width=actual['width'],height=actual['height'],
            combined_risks=combined or [],spec_sha256=sha256(package/filename),
            oracle='Independently declared exact profile/README/sentinel bytes and output entries in the same invocation before cleanup'))
    row('N01','normal-project.json','Generate a named basic project with documentation',
        'Real prompt-to-Liquid-to-file path with stable prompt snapshot','fixture')
    def prompts(name='synthetic-notes',owner='Ada',extended=False,docs=True,skip_name=False,skip_owner=False):
        result=[]
        if not skip_name:result += [expect('Project Name'),*answer(name)]
        if not skip_owner:result += [expect('Project owner'),*answer(owner)]
        result += [expect('Project mode')]+([key('ArrowDown')] if extended else [])+[key('Enter'),expect('Include documentation')]
        return result+([] if docs else [key('ArrowUp')])+[key('Enter'),expect('New project created')]
    def add(cid,task,risk,steps,args=(),name='synthetic-notes',owner='Ada',mode='basic',docs=True,
            exit_code=0,failure=False,empty_output=False,initial=None,output='default',width=80,height=24,combined=None):
        fixture='fixtures/'+cid.lower();folder=package/fixture
        shutil.copytree(package/'fixture',folder)
        for filename,payload in (initial or {}).items():
            path=folder/filename;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
        value=copy.deepcopy(template);value.update(name=task,width=width,height=height,timeout_ms=10000)
        value['workspace']['fixture']=fixture;value['command']=template['command']+list(args)
        value['steps']=steps+[dict(exit=exit_code)]
        def state(path,kind='file',payload=None,entries=None):
            data=dict(path=path,kind=kind)
            if payload is not None:data['bytes_base64']=base64.b64encode(payload).decode()
            if entries is not None:data['entries']=sorted(entries)
            value['steps'].append(dict(state=data))
        state('sentinel.txt',payload=b'unrelated synthetic data\n')
        for filename,payload in (initial or {}).items():
            if filename!=name+'/keep.txt':state(filename,payload=payload)
        prefix='' if output=='root' else name+'/'
        if failure:
            if initial and name+'/keep.txt' in initial:
                state(name+'/keep.txt',payload=initial[name+'/keep.txt']);state(name,kind='entries',entries=['keep.txt'])
            else:state(name,kind='empty_directory' if empty_output else 'absent')
        else:
            profile=f'project={name}\nowner={owner}\nmode={mode}\nreadme={str(docs).lower()}\n'.encode('utf-8')
            readme=(f'# {name}\n\nOwner: {owner}\nMode: {mode}\n' if docs else 'Documentation disabled\n').encode('utf-8')
            state(prefix+'profile.txt',payload=profile);state(prefix+'README.md',payload=readme)
            if output!='root':state(name,kind='entries',entries=['profile.txt','README.md'])
        expected=set(p.name for p in folder.iterdir())
        if not failure:expected.update(['profile.txt','README.md'] if output=='root' else [name])
        elif empty_output:expected.add(name)
        state('.',kind='entries',entries=expected)
        filename=cid.lower()+'.json';immutable_json(package/filename,value)
        row(cid,filename,task,risk,fixture,combined);cases[-1].update(expected_exit=exit_code,width=width,height=height)
    add('N02','Choose extended mode for another owner','Menu selection must change saved output',
        prompts(owner='Grace',extended=True),owner='Grace',mode='extended')
    add('N03','Explicitly disable documentation','Boolean false must survive into generated files',
        prompts(docs=False),docs=False)
    add('N04','Supply project name and answer remaining prompts','CLI supplied variable skips only its own prompt',
        prompts(name='named-project',skip_name=True),args=['--name','named-project'],name='named-project')
    add('N05','Provide owner through define and choose extended mode','Provided string and prompted choices agree',
        prompts(owner='Lin',extended=True,skip_owner=True),args=['--define','owner=Lin'],owner='Lin',mode='extended')
    add('N06','Generate noninteractively from an explicit values file','Supported automation route has the same exact saved-state contract',
        [expect('New project created')],args=['--name','synthetic-notes','--silent','--values-file','values.toml'],
        owner='Mira',mode='extended',docs=False,
        initial={'values.toml':b'[values]\nowner="Mira"\nmode="extended"\nreadme=false\n'})
    add('N07','Initialize an existing owned directory and preserve unrelated files','Init destination semantics and sentinel preservation',
        prompts(name='rooted-project',skip_name=True),args=['--init','--name','rooted-project'],name='rooted-project',output='root')
    add('N08','Prefer rendered liquid file over a plain template twin','The public suffix precedence replaces the stale plain input',
        prompts(),initial={'template/README.md':b'stale unrendered template twin\n'})
    add('E01','Reject an invalid project name then accept a corrected name','Validation loop must not generate the rejected destination',
        [expect('Project Name'),*answer('1'),expect('not a valid value for crate_name'),*answer('synthetic-notes'),
         *prompts(skip_name=True)],combined=['invalid input','prompt reentry','correct exact generated name'])
    add('E02','Correct owner text with backspace during a small-view resize','Actual input editing and resize affect the intended saved value',
        [expect('Project Name'),*answer('synthetic-notes'),expect('Project owner'),dict(resize=dict(width=100,height=30)),
         dict(text='Adx'),key('Backspace'),*answer('a'),*prompts(skip_name=True,skip_owner=True)],width=40,height=12,
        combined=['small viewport','resize while editing','backspace correction'])
    add('E03','Cancel at the initial project-name prompt','No generated project after early cancellation',
        [expect('Project Name'),key('CtrlC')],exit_code=3221225786,failure=True)
    add('E04','Cancel after owner entry while selecting a mode','Partial prompt input cannot become a completed project',
        [expect('Project Name'),*answer('synthetic-notes'),expect('Project owner'),*answer('Ada'),expect('Project mode'),key('CtrlC')],
        exit_code=3221225786,failure=True,empty_output=True,combined=['partial input','selector interruption','no completed output'])
    add('E05','Preserve a Unicode owner through prompts and Liquid rendering','UTF-8 data and exact output bytes',
        prompts(owner='caf\u00e9 \u96ea'),owner='caf\u00e9 \u96ea')
    add('E06','Wrap a long owner then choose another mode','Wrapped input and selector navigation retain all owner bytes',
        prompts(owner='Synthetic owner '+('long label '*5).strip(),extended=True),
        owner='Synthetic owner '+('long label '*5).strip(),mode='extended',width=40,height=16,
        combined=['wrapped prompt','long string','nondefault selector value'])
    add('E07','Keep shell metacharacters as literal template data','Text input must not execute a shell or alter neighboring data',
        prompts(owner='A & B; $(literal)'),owner='A & B; $(literal)')
    add('E08','Refuse an existing output directory and preserve its contents','Existing destination protection',
        [expect('Target directory already exists')],args=['--name','synthetic-notes'],exit_code=1,failure=True,
        initial={'synthetic-notes/keep.txt':b'existing owned project must remain\n'})
    add('E09','Refuse a file as the template root','Wrong-type source with no generated output',
        [expect('Error:')],args=['--name','synthetic-notes','--path','template-file.txt'],exit_code=1,failure=True,
        initial={'template-file.txt':b'not a template directory\n'})
    # Replace the original --path operand instead of providing a duplicate flag.
    path=package/'e09.json';data=json.loads(path.read_text());data['command']=template['command'][:]
    data['command'][data['command'].index('--path')+1]='template-file.txt';data['command']+=['--name','synthetic-notes']
    path.write_text(json.dumps(data,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    cases[-1]['spec_sha256']=sha256(path)
    add('E10','Refuse a malformed template configuration without changing its source','Parser failure preserves owned inputs',
        [expect('Error:')],args=['--name','synthetic-notes'],exit_code=1,failure=True,
        initial={'template/cargo-generate.toml':b'[placeholders\ninvalid = true\n'})
    add('E11','Refuse silent generation when a required value is missing','No quiet fallback invents the required owner',
        [expect('Error:')],args=['--silent','--name','synthetic-notes'],exit_code=1,failure=True,empty_output=True)
    add('E12','Refuse malformed Liquid syntax after real prompt completion','Rendering failure cannot create a successful destination',
        prompts()[:-1]+[expect('Error:')],exit_code=1,failure=True,empty_output=True,
        initial={'template/profile.txt.liquid':b'{% if %}\n'},
        combined=['complete user inputs','rendering failure','no success output'])
    immutable_json(package/'scenarios.json',dict(schema_version=1,project='cargo-generate',
        source_pin=json.loads((package/'source-review.json').read_text())['pin'],normal=8,edge=12,
        status='development-declaration-not-final-freeze',cases=cases))
    print('Declared twenty development cases; no execution, final or admission credit.')


if __name__=='__main__':main()
