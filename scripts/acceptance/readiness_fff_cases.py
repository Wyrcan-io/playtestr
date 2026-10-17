"""Twenty real file-manager workflows authored only through public recorder controls."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import platform
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256

SENTINEL=b'preserve reviewed existing work\n'


def key(name):return '/key '+name
def text(value):return '/text '+json.dumps(value,ensure_ascii=True)
def expect(value):return '/expect '+value
def absent(value):return '/absent '+value
def quit_clean():return [text('q'),'/exit 0']
def prompt(trigger,label,value):
    return [text(trigger),expect(label),text(value),key('Enter'),absent(label)]
def choose(name):
    return [text('/'+name),expect('/'+name),key('Enter'),absent('/'+name)]
def goto(name):return prompt(':','go to dir:',name)
def create(name):return [*prompt('f','mkfile:',name),expect(name)]
def rename(old,new):return [*prompt('r','rename '+old+':',new),expect(new)]
def marked(operation):return [text(operation),expect('[1] selected')]
def paste(name):return [text('p'),expect(name),absent('[1] selected')]


def entry_sets(files,declared_dirs):
    dirs={'trash',*declared_dirs}
    for name in [*files,*declared_dirs]:
        parent=PurePosixPath(name).parent
        while str(parent)!='.':
            dirs.add(parent.as_posix());parent=parent.parent
    nodes=set(files)|dirs
    return {name:sorted(PurePosixPath(n).name for n in nodes if PurePosixPath(n).parent.as_posix()==name)
            for name in {'.',*dirs}}


def rows(host=None):
    host=host or ('macos' if platform.system()=='Darwin' else 'linux')
    if host not in {'linux','macos'}:raise RuntimeError('undeclared native authoring profile')
    def first_directory(real_entries):
        count=real_entries+(2 if host=='macos' else 0)
        controls=[expect('(1/'+str(count)+')'),text('G'),expect('('+str(count)+'/'+str(count)+')'),text('g'),expect('(1/'+str(count)+')')]
        if host=='macos':controls += [text('j'),expect('(2/'+str(count)+')')]
        return controls
    seed=b'reviewed source\n';anchor=b'destination anchor\n'
    def row(identity,title,files,actions,expected,missing=(),dirs=(),snapshot=False):
        expected={**expected,'sentinel.txt':SENTINEL}
        return dict(id=identity,title=title,kind='normal' if identity.startswith('N') else 'edge',args=[],
            files={**files,'sentinel.txt':SENTINEL},actions=actions,expected=expected,missing=list(missing),
            entry_sets=entry_sets(expected,dirs),snapshot=snapshot)
    def copied(identity,title,contents):
        return row(identity,title,{'source.txt':contents,'destination/anchor.txt':anchor},
            [expect('source.txt'),*choose('source.txt'),*marked('y'),*goto('destination'),expect('anchor.txt'),*paste('source.txt')],
            {'source.txt':contents,'destination/anchor.txt':anchor,'destination/source.txt':contents},snapshot=identity=='N04')
    return [
        row('N01','create an empty named file',{'source.txt':seed},[expect('source.txt'),*create('created.txt')],
            {'source.txt':seed,'created.txt':b''},snapshot=True),
        row('N02','create a nested empty directory tree',{'source.txt':seed},
            [expect('source.txt'),*prompt('n','mkdir:','made/deep'),expect('made/')],{'source.txt':seed},dirs=['made/deep']),
        row('N03','rename a file while preserving its exact contents',{'source.txt':seed},
            [expect('source.txt'),*choose('source.txt'),*rename('source.txt','renamed.txt')],{'renamed.txt':seed},missing=['source.txt']),
        copied('N04','copy a file into another directory',seed),
        row('N05','move a file into another directory',{'source.txt':seed,'destination/anchor.txt':anchor},
            [expect('source.txt'),*choose('source.txt'),*marked('m'),*goto('destination'),expect('anchor.txt'),*paste('source.txt')],
            {'destination/anchor.txt':anchor,'destination/source.txt':seed},missing=['source.txt']),
        row('N06','confirm moving a selected file to the synthetic trash',{'source.txt':seed},
            [expect('source.txt'),*choose('source.txt'),*marked('d'),text('p'),expect('trash [1] items?'),text('y'),
             absent('trash [1] items?'),absent('source.txt')],{'trash/source.txt':seed},missing=['source.txt']),
        row('N07','copy a directory tree with nested and hidden contents',
            {'bundle/nested/deep.txt':seed,'bundle/.hidden':b'hidden bytes\n','destination/anchor.txt':anchor},
            [expect('bundle/'),*first_directory(4),*marked('y'),*goto('destination'),expect('anchor.txt'),*paste('bundle/')],
            {'bundle/nested/deep.txt':seed,'bundle/.hidden':b'hidden bytes\n','destination/anchor.txt':anchor,
             'destination/bundle/nested/deep.txt':seed,'destination/bundle/.hidden':b'hidden bytes\n'}),
        row('N08','rename a directory without losing its nested file',{'folder/nested.txt':seed},
            [expect('folder/'),*first_directory(3),*rename('folder','renamed-folder')],{'renamed-folder/nested.txt':seed},missing=['folder']),
        row('E01','cancel file creation by submitting an empty name',{'source.txt':seed},
            [expect('source.txt'),text('f'),expect('mkfile:'),key('Enter'),absent('mkfile:')],{'source.txt':seed},missing=['cancelled.txt']),
        row('E02','refuse to recreate an existing file and preserve its bytes',{'source.txt':seed},
            [expect('source.txt'),text('f'),expect('mkfile:'),text('source.txt'),key('Enter'),expect("warn: 'source.txt' already exists."),
             key('Enter'),absent("warn: 'source.txt' already exists.")],{'source.txt':seed}),
        row('E03','erase a proposed rename and keep the original path',{'source.txt':seed},
            [expect('source.txt'),*choose('source.txt'),text('r'),expect('rename source.txt:'),text('draft'),expect('draft'),
             text('\x7f'*5),absent('draft'),key('Enter'),absent('rename source.txt:')],{'source.txt':seed},missing=['draft']),
        row('E04','reject a rename collision without changing either file',{'source.txt':seed,'taken.txt':b'existing destination\n'},
            [expect('source.txt'),*choose('source.txt'),text('r'),expect('rename source.txt:'),text('taken.txt'),key('Enter'),
             expect("warn: 'taken.txt' already exists."),key('Enter'),absent("warn: 'taken.txt' already exists.")],
            {'source.txt':seed,'taken.txt':b'existing destination\n'}),
        row('E05','decline trash by submitting no affirmative answer',{'source.txt':seed},
            [expect('source.txt'),*choose('source.txt'),*marked('d'),text('p'),expect('trash [1] items?'),key('Enter'),
             absent('trash [1] items?')],{'source.txt':seed}),
        row('E06','create a Unicode and spaced filename',{'source.txt':seed},
            [expect('source.txt'),*create('notes caf\u00e9 \u96ea.txt')],{'source.txt':seed,'notes caf\u00e9 \u96ea.txt':b''}),
        row('E07','show a hidden file then rename it with bytes preserved', {'.hidden.txt':seed},
            [expect('sentinel.txt'),text('.'),expect('.hidden.txt'),*choose('.hidden.txt'),*rename('.hidden.txt','visible.txt')],
            {'visible.txt':seed},missing=['.hidden.txt']),
        copied('E08','copy embedded binary NUL bytes without conversion',b'head\x00tail\r\n'),
        row('E09','decline an interactive copy overwrite',{'source.txt':seed,'destination/anchor.txt':anchor,'destination/source.txt':b'keep old destination\n'},
            [expect('source.txt'),*choose('source.txt'),*marked('y'),*goto('destination'),expect('anchor.txt'),text('p'),expect('overwrite'),
             text('n'),key('Enter'),absent('overwrite')],
            {'source.txt':seed,'destination/anchor.txt':anchor,'destination/source.txt':b'keep old destination\n'}),
        row('E10','clear a marked operation before attempting paste',{'source.txt':seed},
            [expect('source.txt'),*choose('source.txt'),*marked('m'),text('c'),absent('[1] selected'),text('pq'),'/exit 0'],{'source.txt':seed}),
        row('E11','resize and create files in both viewports',{'source.txt':seed},
            [expect('source.txt'),'/resize 40 12','/redraw',*create('narrow.txt'),'/resize 100 28','/redraw',*create('wide.txt')],
            {'source.txt':seed,'narrow.txt':b'','wide.txt':b''},snapshot=True),
        row('E12','recover from an empty search before creating another file',{'source.txt':seed},
            [expect('source.txt'),text('/no-matching-item'),expect('/no-matching-item'),absent('source.txt'),key('Enter'),
             absent('/no-matching-item'),expect('source.txt'),*create('recovered.txt')],{'source.txt':seed,'recovered.txt':b''}),
    ]


def serialise(row):
    return {**row,'files':{k:base64.b64encode(v).decode() for k,v in row['files'].items()},
        'expected':{k:base64.b64encode(v).decode() for k,v in row['expected'].items()}}


def plan_hash(row):return hashlib.sha256(json.dumps(serialise(row),sort_keys=True).encode()).hexdigest()


def environment():
    build=json.loads((RAW/'active/fff/build.json').read_text());binary=RAW/'active/fff'/build['binary_relative_path']
    if not binary.is_file():raise RuntimeError('owned editor binary missing')
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env['PATH']=str(binary.parent)+os.pathsep+env['PATH']
    return env


async def author(row):
    root=RAW/'fff/authoring'/row['id']/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'declared-plan.json',serialise(row))
    fixture=root/'fixture';fixture.mkdir()
    for name,value in row['files'].items():
        path=fixture/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
    controls=list(row['actions'])
    if not controls or not controls[-1].startswith('/exit '):
        if row['snapshot']:controls+=['/snapshot-rows '+row['id']+'.rows.json 1 24']
        controls+=quit_clean()
    for name in sorted(row['expected']):controls+=['/file '+name]
    for name in row['missing']:controls+=['/missing '+name]
    controls+=['/entries '+name for name in sorted(row['entry_sets'])]
    controls+=['/review','/replay','/save']
    spec=root/'spec.json';runner=RAW/'bin/playtestr'
    capture=await execute([runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home',
        '--temporary-temp','--width','100','--height','28','--timeout-ms','10000','--run-timeout-ms','120000',
        '--env','TERM=xterm-256color','--env','LC_ALL='+('en_US.UTF-8' if platform.system()=='Darwin' else 'C.UTF-8'),'--env','FFF_LS_COLORS=0','--env','FFF_CD_ON_EXIT=1','--env','FFF_TRASH=trash','--','fff',*row['args']],'fff',row['id']+'-public-author-review-replay',
        input='\n'.join(controls)+'\n',env=environment(),timeout=180,campaign=Campaign())
    await validate_and_test(row,spec,capture['id'])


async def validate_and_test(row,spec,capture_ident,resumed=False):
    root=spec.parent;runner=RAW/'bin/playtestr'
    exported=json.loads(spec.read_text(encoding='utf-8-sig'));states=[s['state'] for s in exported['steps'] if 'state' in s]
    files={s['path']:base64.b64decode(s['bytes_base64']) for s in states if s['kind']=='file'}
    if files!=row['expected']:raise RuntimeError(row['id']+' independent expected saved bytes reject the export')
    if {s['path'] for s in states if s['kind']=='absent'}!=set(row['missing']):raise RuntimeError('missing selected absence contract')
    entries={s['path']:s['entries'] for s in states if s['kind']=='entries'}
    if {name:sorted(value) for name,value in entries.items()}!=row['entry_sets'] or any(len(value)!=len(set(value)) for value in entries.values()):raise RuntimeError('unexpected directory side effect')
    report=root/'ordinary-result.json'
    ordinary=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),
        spec.relative_to(ROOT)],'fff',row['id']+'-ordinary-authored-contract',env=environment(),timeout=130,campaign=Campaign())
    result=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
    if result['status']!='passed' or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
        raise RuntimeError('authored case or cleanup unconfirmed')
    immutable_json(RAW/'fff/approved'/(row['id']+'.json'),dict(case=row['id'],plan_sha256=plan_hash(row),
        spec=spec.relative_to(ROOT).as_posix(),spec_sha256=sha256(spec),capture_attempt=capture_ident,
        ordinary_attempt=ordinary['id'],report_sha256=sha256(report),expected_bytes_independently_checked=True,
        resumed_missing_ordinary_only=resumed))
    print(row['id'],'authored, independently reviewed and ordinary replay passed',flush=True)


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',action='append')
    parser.add_argument('--resume-export',type=Path);parser.add_argument('--capture-id');args=parser.parse_args()
    declared=rows();assert len(declared)==20 and sum(r['kind']=='normal' for r in declared)==8
    selected=[r for r in declared if not args.case or r['id'] in args.case]
    if args.case and {r['id'] for r in selected}!=set(args.case):raise RuntimeError('unknown case selection')
    if args.resume_export:
        if len(selected)!=1 or not args.capture_id:raise RuntimeError('resume requires one case and its completed capture identity')
        spec=args.resume_export.resolve(strict=True);spec.relative_to((RAW/'fff/authoring'/selected[0]['id']).resolve())
        if json.loads((spec.parent/'declared-plan.json').read_text(encoding='utf-8-sig'))!=serialise(selected[0]):raise RuntimeError('original case plan differs')
        finished=json.loads((RAW/'events'/(args.capture_id+'-finished.json')).read_text())
        if finished['category']!='passed' or finished['exit_code']!=0:raise RuntimeError('original public export did not pass')
        if spec.parent.name not in (RAW/'fff'/args.capture_id/'console.log').read_text(encoding='utf-8'):raise RuntimeError('capture belongs to another output')
        await validate_and_test(selected[0],spec,args.capture_id,True)
        return
    batch=RAW/'fff/authoring-batches'/uuid.uuid4().hex;batch.mkdir(parents=True)
    immutable_json(batch/'declared.json',dict(rows=[serialise(r) for r in selected],qualification='declared, not executed'))
    failures=[]
    for row in selected:
        approved=RAW/'fff/approved'/(row['id']+'.json')
        if approved.exists():
            if json.loads(approved.read_text())['plan_sha256']!=plan_hash(row):raise RuntimeError('approved case plan changed; explicit review required')
            print(row['id'],'already approved; not repeated',flush=True);continue
        try:await author(row)
        except Exception as error:
            failures.append(dict(case=row['id'],error=type(error).__name__,message=str(error)))
            print(row['id'],'failed; first evidence retained:',error,flush=True)
    immutable_json(batch/'outcomes.json',dict(failures=failures,selected=len(selected)))
    if failures:raise RuntimeError('case authoring incomplete; inspect retained first failures')


if __name__=='__main__':asyncio.run(main())
