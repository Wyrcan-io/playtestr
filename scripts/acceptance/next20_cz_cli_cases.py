"""Declare twenty useful message/configuration outcomes after public authoring."""
import base64
import copy
import json
import shutil

from next20_check import DOC
from next20_fixture_git import reconstruct
from readiness_evidence import immutable_json,sha256


def prompts(*,scope='',subject='Add a synthetic entry.',body='',breaking=None,issues=None,
            cancel=None,validation=None,correct=False,resize=False,banner=True):
    steps=[dict(expect='cz-cli@0.0.3')] if banner else []
    questions=['Select the type','What is the scope','imperative tense','Provide a longer description',
               'Are there any breaking changes?','open issues?']
    for index,label in enumerate(questions):
        steps.append(dict(expect=label))
        if cancel==index:return steps+[dict(key='CtrlC')]
        if index==1 and scope:steps.append(dict(text=scope))
        if index==2:
            if validation=='empty':steps.extend([dict(key='Enter'),dict(expect='subject is required')])
            if validation=='length':
                rejected='This synthetic subject is too long'
                steps.extend([dict(text=rejected),dict(key='Enter'),dict(expect='Subject length must be less')])
                steps.extend(dict(key='Backspace') for _ in rejected)
            if subject is not None:steps.append(dict(text=subject+('X' if correct else '')))
            if correct:steps.append(dict(key='Backspace'))
            if resize:steps.extend([dict(resize=dict(width=40,height=16)),dict(expect='imperative tense')])
        if index==3 and body:steps.append(dict(text=body))
        if index==4 and breaking:steps.append(dict(text='y'))
        if index==5 and issues:steps.append(dict(text='y'))
        steps.append(dict(key='Enter'))
        if index==4 and breaking:steps.extend([dict(expect='Describe the breaking changes'),dict(text=breaking),dict(key='Enter')])
        if index==5 and issues:steps.extend([dict(expect='Add issue references'),dict(text=issues),dict(key='Enter')])
    return steps


def file_state(path,data):return dict(state=dict(path=path,kind='file',bytes_base64=base64.b64encode(data).decode()))


def main():
    package=DOC/'cz-cli'
    if not (package/'first-use.json').exists() or not (package/'snapshot-authoring.json').exists() or (package/'scenarios.json').exists():
        raise ValueError('Public authoring/snapshot routes first; preserve any existing declaration')
    template=json.loads((package/'normal-message.json').read_text(encoding='utf-8'));cases=[];roots=['fixture']
    for cid,name,task in [('N01','normal-message.json','Capture a new feature message through public authoring'),
                          ('N02','normal-fix.json','Select fix classification and compare the approved terminal screen')]:
        cases.append(dict(id=cid,kind='normal',spec=name,task=task,risk='Exact message and '+('approved rendered screen' if cid=='N02' else 'public authoring'),
            initial_fixture='fixture',expected_exit=0,hosts=['linux','windows'],combined_risks=[],spec_sha256=sha256(package/name)))
    sentinel=(package/'fixture/sentinel.txt').read_bytes()
    def add(cid,task,risk,steps,expected=None,config=None,raw_config=None,exit_code=0,width=120,height=32,combined=None,wrong_type=False,staging=False):
        relative='fixtures/'+cid.lower();roots.append(relative);folder=package/relative
        shutil.copytree(package/'fixture',folder)
        if raw_config is not None:(folder/'.czrc').write_bytes(raw_config)
        elif config is not None:(folder/'.czrc').write_text(json.dumps({'path':'cz-conventional-changelog',**config},sort_keys=True,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
        if wrong_type:(folder/'.git/COMMIT_EDITMSG').mkdir()
        spec=copy.deepcopy(template);spec.update(name=task,width=width,height=height)
        spec['workspace']['fixture']=relative
        if staging:spec['command'].remove('--allow-empty')
        spec['steps']=steps+[dict(exit=exit_code)]
        if wrong_type:spec['steps'].append(dict(state=dict(path='.git/COMMIT_EDITMSG',kind='empty_directory')))
        elif expected is None:spec['steps'].append(dict(state=dict(path='.git/COMMIT_EDITMSG',kind='absent')))
        else:spec['steps'].append(file_state('.git/COMMIT_EDITMSG',expected))
        entries=['HEAD','config','objects','refs']+(['COMMIT_EDITMSG'] if expected is not None or wrong_type else [])
        spec['steps'].extend([file_state('.czrc',(folder/'.czrc').read_bytes()),file_state('sentinel.txt',sentinel),
            dict(state=dict(path='.git',kind='entries',entries=sorted(entries,key=str.casefold))),
            dict(state=dict(path='.',kind='entries',entries=['.czrc','.git','sentinel.txt']))])
        name=cid.lower()+'.json';immutable_json(package/name,spec)
        cases.append(dict(id=cid,kind='normal' if cid.startswith('N') else 'edge',spec=name,task=task,risk=risk,
            initial_fixture=relative,expected_exit=exit_code,hosts=['linux','windows'],combined_risks=combined or [],spec_sha256=sha256(package/name)))
    add('N03','Normalize a scoped feature message','scope trimming and lowercasing',prompts(scope='  CORE  '),b'feat(core): add a synthetic entry')
    body='Explain the synthetic change.'
    add('N04','Include a descriptive message body','exact blank-line body separation',prompts(body=body),b'feat: add a synthetic entry\n\n'+body.encode())
    breaking='BREAKING CHANGE: drop the old mode'
    add('N05','Document a breaking change with its body','conditional questions and one breaking prefix',prompts(body=body,breaking=breaking),
        b'feat: add a synthetic entry\n\n'+body.encode()+b'\n\nBREAKING CHANGE: drop the old mode',combined=['conditional prompt','saved body','prefix normalization'])
    add('N06','Include synthetic issue references with a body','conditional reference question and exact footer',prompts(body=body,issues='Fixes #42'),
        b'feat: add a synthetic entry\n\n'+body.encode()+b'\n\nFixes #42')
    add('N07','Use reviewed team defaults from the local configuration','default type, scope and subject filtering',prompts(subject=None),b'fix(api): keep API',
        config=dict(defaultType='fix',defaultScope='API',defaultSubject='Keep API.'))
    wrapped='Document the owned fixture behavior with reproducible text.'
    add('N08','Wrap a descriptive body at the configured line width','configured word wrapping and exact preserved message',prompts(body=wrapped),
        b'feat: add a synthetic entry\n\nDocument the owned\nfixture behavior with\nreproducible text.',config=dict(maxLineWidth=24))
    add('E01','Cancel before choosing a message type','early interrupt leaves no message',prompts(cancel=0),exit_code=130)
    add('E02','Cancel at the final issue question','late interrupt leaves no partial message',prompts(body=body,cancel=5),exit_code=130)
    add('E03','Recover from a required-subject validation error','positive validation evidence followed by saved recovery',prompts(validation='empty'),b'feat: add a synthetic entry')
    add('E04','Correct a subject that exceeds the configured header limit','length validation, repeated editing and exact recovery',
        prompts(subject='Small change.',validation='length'),b'feat: small change',config=dict(maxHeaderWidth=22),combined=['validation failure','bounded editing','configured length','saved state'])
    add('E05','Preserve a Unicode scope and subject','Unicode input, normalization and UTF-8 file bytes',
        prompts(scope='R\u00c9L_\u96ea',subject='Add \u96ea.'),'feat(r\u00e9l_\u96ea): add \u96ea'.encode(),width=80,height=24,
        combined=['Unicode width','scope normalization','UTF-8 message','exact entries'])
    punctuation='Keep $(echo nope); & pipes |.'
    add('E06','Keep shell-looking message punctuation literal','message data cannot become a command or extra file',prompts(subject=punctuation),
        b'feat: keep $(echo nope); & pipes |',combined=['literal punctuation','file bytes','no extra files'])
    long_subject='Document the synthetic configuration behavior across the narrow viewport.'
    add('E07','Correct a wrapped subject while resizing the viewport','editable wrapped input, redraw and exact saved recovery',
        prompts(scope='API',subject=long_subject,correct=True,resize=True),('feat(api): '+long_subject[0].lower()+long_subject[1:-1]).encode(),width=90,height=22,
        combined=['input correction','wrapped input','resize/redraw','saved message'])
    add('E08','Complete the message on a small viewport','short readiness anchors and saved message at45x12',
        prompts(banner=False),b'feat: add a synthetic entry',width=45,height=12)
    add('E09','Reject malformed local adapter configuration','bounded parse error preserves all fixture data',
        [dict(expect='Parsing JSON at')],raw_config=b'{"path":\n',exit_code=1)
    add('E10','Reject an unresolved configured adapter','explicit adapter-resolution failure and unchanged files',
        [dict(expect='Could not resolve playtestr-no-such-adapter')],config=dict(path='playtestr-no-such-adapter'),exit_code=1)
    add('E11','Explain an empty staging area when allow-empty is absent','staging precondition fails before writing a message',
        [dict(expect='No files added to staging')],staging=True,exit_code=1)
    add('E12','Reject a directory at the message-file destination','complete prompts then exact write-type failure with cleanup',
        prompts()+[dict(expect='EISDIR')],wrong_type=True,exit_code=1,
        combined=['completed prompt flow','late filesystem failure','wrong type preserved','nonzero exit'])
    if len(cases)!=20 or sum(c['kind']=='normal' for c in cases)!=8 or sum(bool(c['combined_risks']) for c in cases)<4:raise ValueError('Incomplete declared scenario boundary')
    boundary=json.loads((package/'fixture-git.json').read_text(encoding='utf-8'));boundary['fixture_roots']=roots
    (package/'fixture-git.json').write_text(json.dumps(boundary,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    reconstruct(package)
    immutable_json(package/'scenarios.json',dict(schema_version=1,project='cz-cli',cases=cases,normal=8,edge=12,
        scope='Actual pinned CLI and standard locked adapter, trusted synthetic hook-mode messages; no commits/hooks/tags/services. First development attempts must all be retained.'))
    print('Declared20 useful cases:8normal/12edge; exact independently expected messages and unchanged fixture evidence.')


if __name__=='__main__':main()
