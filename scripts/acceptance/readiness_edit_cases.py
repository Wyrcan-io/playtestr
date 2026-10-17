"""Declared real editor workflows, authored through public recorder controls."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256

SENTINEL=b'preserve reviewed existing work\n'


def key(name):return '/key '+name
def text(value):return '/text '+json.dumps(value,ensure_ascii=True)
def expect(value):return '/expect '+value
def absent(value):return '/absent '+value
def save():return [expect('*'),key('CtrlS'),absent('*')]
def quit_clean():return [key('CtrlQ'),'/exit 0']
def discard():return [key('CtrlQ'),expect('Unsaved Changes'),text('n'),'/exit 0']


def rows():
    seed=b'reviewed seed\n';line='reviewed seed'
    def row(identity,title,files,args,actions,expected,missing=(),snapshot=False):
        return dict(id=identity,title=title,kind='normal' if identity.startswith('N') else 'edge',
            files={**files,'sentinel.txt':SENTINEL},args=args,actions=actions,
            expected={**expected,'sentinel.txt':SENTINEL},missing=list(missing),snapshot=snapshot)
    def edit_suffix(value):return [key('End'),text(value),expect(line+value)]
    return [
        row('N01','append and save an existing text file',{'note.txt':seed},['note.txt'],
            [expect(line),*edit_suffix(' + tested'),*save()],{'note.txt':b'reviewed seed + tested\n'},snapshot=True),
        row('N02','create a named new document',{},['new-note.txt'],
            [expect('new-note.txt'),text('fresh document'),expect('fresh document'),*save()],{'new-note.txt':b'fresh document'}),
        row('N03','edit the requested line and column',{'note.txt':b'alpha\nbravo\ncharlie\n'},['--goto','note.txt:2:1'],
            [expect('bravo'),text('reviewed '),expect('reviewed bravo'),*save()],{'note.txt':b'alpha\nreviewed bravo\ncharlie\n'}),
        row('N04','undo and redo the last inserted group',{'note.txt':seed},['note.txt'],
            [expect(line),*edit_suffix(' + redo'),expect('+ redo'),key('CtrlZ'),absent('+ redo'),expect(line),key('CtrlY'),
             expect(line+' + redo'),*save()],{'note.txt':b'reviewed seed + redo\n'},snapshot=True),
        row('N05','replace all selected document text',{'note.txt':b'old document\n'},['note.txt'],
            [expect('old document'),key('CtrlA'),text('rewritten document'),expect('rewritten document'),*save()],
            {'note.txt':b'rewritten document\n'}),
        row('N06','join adjacent lines without losing remaining text',{'note.txt':b'alpha \nbeta\n'},['note.txt'],
            [expect('beta'),key('ArrowDown'),key('Home'),key('Backspace'),expect('alpha beta'),*save()],{'note.txt':b'alpha beta\n'}),
        row('N07','save two documents across an active-file transition',
            {'alpha.txt':b'alpha document\n','beta.txt':b'beta document\n'},['alpha.txt','beta.txt'],
            [expect('beta document'),key('End'),text(' + checked'),expect('beta document + checked'),*save(),key('CtrlW'),
             expect('alpha document'),key('End'),text(' + checked'),expect('alpha document + checked'),*save()],
            {'alpha.txt':b'alpha document + checked\n','beta.txt':b'beta document + checked\n'}),
        row('N08','find and replace the selected first match',{'note.txt':b'alpha alpha\n'},['note.txt'],
            [expect('alpha alpha'),key('CtrlF'),expect('Find:'),text('alpha'),key('CtrlR'),expect('Replace:'),key('Tab'),
             text('beta'),key('Enter'),key('Escape'),absent('Replace:'),expect('beta alpha'),*save()],{'note.txt':b'beta alpha\n'}),
        row('E01','discard dirty changes and preserve original bytes',{'note.txt':seed},['note.txt'],
            [expect(line),*edit_suffix(' not saved'),*discard()],{'note.txt':seed}),
        row('E02','cancel an unsaved exit then keep editing and save',{'note.txt':seed},['note.txt'],
            [expect(line),*edit_suffix(' staged'),key('CtrlQ'),expect('Unsaved Changes'),key('Escape'),absent('Unsaved Changes'),
             text(' recovered'),expect(line+' staged recovered'),*save()],{'note.txt':b'reviewed seed staged recovered\n'}),
        row('E03','abandon a new document without creating its path',{},['abandon.txt'],
            [expect('abandon.txt'),text('will not persist'),expect('will not persist'),*discard()],{},missing=['abandon.txt']),
        row('E04','save an emptied document as exactly zero bytes',{'empty.txt':b''},['empty.txt'],
            [expect('empty.txt'),text('ephemeral'),expect('ephemeral'),key('CtrlA'),key('Backspace'),absent('ephemeral'),*save()],{'empty.txt':b''}),
        row('E05','edit UTF-8 content in a Unicode and spaced path',{'project caf\u00e9/notes \u96ea.txt':b'starter\n'},['project caf\u00e9/notes \u96ea.txt'],
            [expect('starter'),key('End'),text(' caf\u00e9 \u96ea'),expect('starter caf\u00e9 \u96ea'),*save()],
            {'project caf\u00e9/notes \u96ea.txt':'starter caf\u00e9 \u96ea\n'.encode()}),
        row('E06','preserve CRLF while editing one line',{'note.txt':b'first\r\nsecond\r\n'},['note.txt'],
            [expect('first'),key('End'),text('!'),expect('first!'),*save()],{'note.txt':b'first!\r\nsecond\r\n'}),
        row('E07','preserve an absent final newline',{'note.txt':b'tail'},['note.txt'],
            [expect('tail'),key('End'),text('!'),expect('tail!'),*save()],{'note.txt':b'tail!'}),
        row('E08','resize a dirty document and retain ordered edits',{'note.txt':seed},['note.txt'],
            [expect(line),*edit_suffix(' + resized'),'/resize 40 12','/redraw',text(' narrow'),expect('resized narrow'),
             '/resize 100 28','/redraw',text(' wide'),expect('resized narrow wide'),*save()],
            {'note.txt':b'reviewed seed + resized narrow wide\n'},snapshot=True),
        row('E09','clamp an out-of-range command-line position safely',{'note.txt':b'first\nlast'},['--goto','note.txt:999:999'],
            [expect('last'),text('!'),expect('last!'),*save()],{'note.txt':b'first\nlast!'}),
        row('E10','reject invalid go-to input and recover with a valid position',{'note.txt':b'first\nsecond\n'},['note.txt'],
            [expect('second'),key('CtrlG'),expect('Go to Line'),text('invalid-line'),key('Enter'),expect('invalid-line'),
             expect('Go to Line'),key('CtrlA'),text('2:1'),key('Enter'),absent('Go to Line'),text('fixed '),
             expect('fixed second'),*save()],{'note.txt':b'first\nfixed second\n'}),
        row('E11','open a leading-dash filename using the option terminator',{'-draft.txt':b'draft contents\n'},['--','-draft.txt'],
            [expect('draft contents'),key('End'),text('!'),expect('draft contents!'),*save()],{'-draft.txt':b'draft contents!\n'}),
        row('E12','refuse Save As overwrite then discard the scratch document',{'note.txt':seed},['note.txt'],
            [expect(line),key('CtrlN'),expect('Untitled-1'),text('replacement candidate'),expect('replacement candidate'),
             key('CtrlS'),expect('Save As'),key('CtrlA'),text('sentinel.txt'),expect('File name: sentinel.txt'),
             key('Enter'),key('Enter'),expect('File already exists.'),
             text('n'),absent('File already exists.'),key('Escape'),absent('Save As'),*discard()],{'note.txt':seed}),
    ]


def serialise(row):
    return {**row,'files':{k:base64.b64encode(v).decode() for k,v in row['files'].items()},
        'expected':{k:base64.b64encode(v).decode() for k,v in row['expected'].items()}}


def plan_hash(row):return hashlib.sha256(json.dumps(serialise(row),sort_keys=True).encode()).hexdigest()


def environment():
    build=json.loads((RAW/'active/edit/build.json').read_text());binary=RAW/'active/edit'/build['binary_relative_path']
    if not binary.is_file():raise RuntimeError('owned editor binary missing')
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env['PATH']=str(binary.parent)+os.pathsep+env['PATH']
    return env


async def author(row):
    root=RAW/'edit/authoring'/row['id']/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'declared-plan.json',serialise(row))
    fixture=root/'fixture';fixture.mkdir()
    for name,value in row['files'].items():
        path=fixture/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
    controls=list(row['actions'])
    if not controls or not controls[-1].startswith('/exit '):
        if row['snapshot']:controls+=['/snapshot '+row['id']+'.txt']
        controls+=quit_clean()
    for name in sorted(row['expected']):controls+=['/file '+name]
    for name in row['missing']:controls+=['/missing '+name]
    controls+=['/entries .','/review','/replay','/save']
    spec=root/'spec.json';runner=RAW/'runner-revisions/inherited-interrupt/playtestr.exe'
    capture=await execute([runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home',
        '--temporary-temp','--width','100','--height','28','--timeout-ms','10000','--run-timeout-ms','120000',
        '--inherit-env','SystemDrive','--','edit',*row['args']],'edit',row['id']+'-public-author-review-replay',
        input='\n'.join(controls)+'\n',env=environment(),timeout=180,campaign=Campaign())
    await validate_and_test(row,spec,capture['id'])


async def validate_and_test(row,spec,capture_ident,resumed=False):
    root=spec.parent;runner=RAW/'runner-revisions/inherited-interrupt/playtestr.exe'
    exported=json.loads(spec.read_text(encoding='utf-8-sig'));states=[s['state'] for s in exported['steps'] if 'state' in s]
    files={s['path']:base64.b64decode(s['bytes_base64']) for s in states if s['kind']=='file'}
    if files!=row['expected']:raise RuntimeError(row['id']+' independent expected saved bytes reject the export')
    if {s['path'] for s in states if s['kind']=='absent'}!=set(row['missing']):raise RuntimeError('missing selected absence contract')
    entries=next(s['entries'] for s in states if s['path']=='.')
    if set(entries)!={Path(name).parts[0] for name in row['expected']}:raise RuntimeError('unexpected working-directory side effect')
    report=root/'ordinary-result.json'
    ordinary=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),
        spec.relative_to(ROOT)],'edit',row['id']+'-ordinary-authored-contract',env=environment(),timeout=130,campaign=Campaign())
    result=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
    if result['status']!='passed' or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
        raise RuntimeError('authored case or cleanup unconfirmed')
    immutable_json(RAW/'edit/approved'/(row['id']+'.json'),dict(case=row['id'],plan_sha256=plan_hash(row),
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
        spec=args.resume_export.resolve(strict=True);spec.relative_to((RAW/'edit/authoring'/selected[0]['id']).resolve())
        if json.loads((spec.parent/'declared-plan.json').read_text(encoding='utf-8-sig'))!=serialise(selected[0]):raise RuntimeError('original case plan differs')
        finished=json.loads((RAW/'events'/(args.capture_id+'-finished.json')).read_text())
        if finished['category']!='passed' or finished['exit_code']!=0:raise RuntimeError('original public export did not pass')
        if spec.parent.name not in (RAW/'edit'/args.capture_id/'console.log').read_text(encoding='utf-8'):raise RuntimeError('capture belongs to another output')
        await validate_and_test(selected[0],spec,args.capture_id,True)
        return
    batch=RAW/'edit/authoring-batches'/uuid.uuid4().hex;batch.mkdir(parents=True)
    immutable_json(batch/'declared.json',dict(rows=[serialise(r) for r in selected],qualification='declared, not executed'))
    failures=[]
    for row in selected:
        approved=RAW/'edit/approved'/(row['id']+'.json')
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
