"""Declared real editor workflows, authored through public recorder controls."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
import platform
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256

SENTINEL=b'preserve reviewed existing work\n'


def key(name):return '/key '+name
def text(value):return '/text '+json.dumps(value,ensure_ascii=True)
def expect(value):return '/expect '+value
def absent(value):return '/absent '+value
def command(value):return [text(':'+value),key('Enter')]
def normal():return [key('Escape'),absent('INSERT')]
def append(value):return [text('A'),expect('INSERT'),text(value),*normal()]
def save():return [expect('[+]'),*command('w'),absent('[+]')]
def quit_clean():return [*command('q'),'/exit 0']
def discard():return [*command('q!'),'/exit 0']


def rows():
    seed=b'reviewed seed\n';line='reviewed seed'
    def row(identity,title,files,args,actions,expected,missing=(),snapshot=False):
        return dict(id=identity,title=title,kind='normal' if identity.startswith('N') else 'edge',
            files={**files,'sentinel.txt':SENTINEL},args=args,actions=actions,
            expected={**expected,'sentinel.txt':SENTINEL},missing=list(missing),snapshot=snapshot)
    return [
        row('N01','append and save an existing document',{'note.txt':seed},['note.txt'],
            [expect(line),*append(' + tested'),expect(line+' + tested'),*save()],{'note.txt':b'reviewed seed + tested\n'},snapshot=True),
        row('N02','create a named document with the editor final newline',{},['new-note.txt'],
            [expect('new-note.txt'),text('i'),expect('INSERT'),text('fresh document'),*normal(),expect('fresh document'),*save()],
            {'new-note.txt':b'fresh document\n'}),
        row('N03','change the first word while preserving the remaining line',{'note.txt':b'bravo charlie\n'},['note.txt'],
            [expect('bravo charlie'),text('cw'),expect('INSERT'),text('reviewed'),*normal(),expect('reviewed charlie'),*save()],
            {'note.txt':b'reviewed charlie\n'}),
        row('N04','undo and redo an inserted group',{'note.txt':seed},['note.txt'],
            [expect(line),*append(' + redo'),expect(line+' + redo'),text('u'),absent(line+' + redo'),key('CtrlR'),
             expect(line+' + redo'),*save()],{'note.txt':b'reviewed seed + redo\n'},snapshot=True),
        row('N05','delete the first complete line and retain the next',{'note.txt':b'delete this\nkeep this\n'},['note.txt'],
            [expect('delete this'),text('dd'),absent('delete this'),expect('keep this'),*save()],{'note.txt':b'keep this\n'}),
        row('N06','yank and paste a complete line',{'note.txt':b'copy this\nlast\n'},['note.txt'],
            [expect('copy this'),text('yyp'),*save()],{'note.txt':b'copy this\ncopy this\nlast\n'}),
        row('N07','save two files across an explicit buffer switch',{'alpha.txt':b'alpha document\n','beta.txt':b'beta document\n'},['alpha.txt'],
            [expect('alpha document'),*append(' + checked'),expect('alpha document + checked'),*save(),*command('e beta.txt'),
             expect('beta document'),*append(' + checked'),expect('beta document + checked'),*save()],
            {'alpha.txt':b'alpha document + checked\n','beta.txt':b'beta document + checked\n'}),
        row('N08','search for a later word and change only that match',{'note.txt':b'alpha bravo charlie\n'},['note.txt'],
            [expect('alpha bravo charlie'),text('/bravo'),key('Enter'),text('cw'),expect('INSERT'),text('reviewed'),
             *normal(),expect('alpha reviewed charlie'),*save()],{'note.txt':b'alpha reviewed charlie\n'}),
        row('E01','discard dirty changes while preserving original bytes',{'note.txt':seed},['note.txt'],
            [expect(line),*append(' not saved'),expect(line+' not saved'),*discard()],{'note.txt':seed}),
        row('E02','reject an unsaved quit then resume and save',{'note.txt':seed},['note.txt'],
            [expect(line),*append(' staged'),*command('q'),expect('No write since last change'),*append(' recovered'),
             expect(line+' staged recovered'),*save()],{'note.txt':b'reviewed seed staged recovered\n'}),
        row('E03','abandon a new dirty file without creating it',{},['abandon.txt'],
            [expect('abandon.txt'),text('i'),expect('INSERT'),text('will not persist'),*normal(),expect('will not persist'),*discard()],
            {},missing=['abandon.txt']),
        row('E04','delete all text and persist exactly zero bytes',{'empty.txt':b'temporary\n'},['empty.txt'],
            [expect('temporary'),text('dd'),absent('temporary'),*save()],{'empty.txt':b''}),
        row('E05','edit UTF-8 text in a Unicode and spaced path',{'project caf\u00e9/notes \u96ea.txt':b'starter\n'},['project caf\u00e9/notes \u96ea.txt'],
            [expect('starter'),*append(' caf\u00e9 \u96ea'),expect('starter caf\u00e9 \u96ea'),*save()],
            {'project caf\u00e9/notes \u96ea.txt':'starter caf\u00e9 \u96ea\n'.encode()}),
        row('E06','preserve CRLF while editing the first line',{'note.txt':b'first\r\nsecond\r\n'},['note.txt'],
            [expect('second'),text('I'),expect('INSERT'),text('!'),*normal(),expect('!first'),*save()],{'note.txt':b'!first\r\nsecond\r\n'}),
        row('E07','preserve an absent final newline',{'note.txt':b'tail'},['note.txt'],
            [expect('tail'),*append('!'),expect('tail!'),*save()],{'note.txt':b'tail!'}),
        row('E08','resize a dirty document and retain fresh ordered edits',{'note.txt':seed},['note.txt'],
            [expect(line),*append(' + resized'),'/resize 40 12','/redraw',*append(' narrow'),expect('resized narrow'),
             '/resize 100 28','/redraw',*append(' wide'),expect('resized narrow wide'),*save()],
            {'note.txt':b'reviewed seed + resized narrow wide\n'},snapshot=True),
        row('E09','recover from an unknown editor command',{'note.txt':seed},['note.txt'],
            [expect(line),*command('no-such-command'),expect('Unknown command'),key('Escape'),key('Escape'),*append(' recovered'),expect(line+' recovered'),*save()],
            {'note.txt':b'reviewed seed recovered\n'}),
        row('E10','force reload to discard changes then save a new edit',{'note.txt':seed},['note.txt'],
            [expect(line),*append(' discarded'),expect(line+' discarded'),*command('e!'),absent(line+' discarded'),
             *append(' retained'),expect(line+' retained'),*save()],{'note.txt':b'reviewed seed retained\n'}),
        row('E11','open a leading-dash filename after the option terminator',{'-draft.txt':b'draft contents\n'},['--','-draft.txt'],
            [expect('draft contents'),*append('!'),expect('draft contents!'),*save()],{'-draft.txt':b'draft contents!\n'}),
        row('E12','retain embedded binary NUL bytes when appending to a line',{'note.txt':b'head\x00tail\n'},['note.txt'],
            [expect('tail'),*append('!'),expect('tail!'),*save()],{'note.txt':b'head\x00tail!\n'}),
    ]

def serialise(row):
    return {**row,'files':{k:base64.b64encode(v).decode() for k,v in row['files'].items()},
        'expected':{k:base64.b64encode(v).decode() for k,v in row['expected'].items()}}


def plan_hash(row):return hashlib.sha256(json.dumps(serialise(row),sort_keys=True).encode()).hexdigest()


def environment():
    build=json.loads((RAW/'active/vis/build.json').read_text());binary=RAW/'active/vis'/build['binary_relative_path']
    if not binary.is_file():raise RuntimeError('owned editor binary missing')
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env['PATH']=str(binary.parent)+os.pathsep+env['PATH']
    return env


async def author(row):
    root=RAW/'vis/authoring'/row['id']/uuid.uuid4().hex;root.mkdir(parents=True)
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
    spec=root/'spec.json';runner=RAW/'bin/playtestr'
    capture=await execute([runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home',
        '--temporary-temp','--width','100','--height','28','--timeout-ms','10000','--run-timeout-ms','120000',
        '--env','TERM=xterm-256color','--env','LC_ALL='+('en_US.UTF-8' if platform.system()=='Darwin' else 'C.UTF-8'),'--','vis',*row['args']],'vis',row['id']+'-public-author-review-replay',
        input='\n'.join(controls)+'\n',env=environment(),timeout=180,campaign=Campaign())
    await validate_and_test(row,spec,capture['id'])


async def validate_and_test(row,spec,capture_ident,resumed=False):
    root=spec.parent;runner=RAW/'bin/playtestr'
    exported=json.loads(spec.read_text(encoding='utf-8-sig'));states=[s['state'] for s in exported['steps'] if 'state' in s]
    files={s['path']:base64.b64decode(s['bytes_base64']) for s in states if s['kind']=='file'}
    if files!=row['expected']:raise RuntimeError(row['id']+' independent expected saved bytes reject the export')
    if {s['path'] for s in states if s['kind']=='absent'}!=set(row['missing']):raise RuntimeError('missing selected absence contract')
    entries=next(s['entries'] for s in states if s['path']=='.')
    if set(entries)!={Path(name).parts[0] for name in row['expected']}:raise RuntimeError('unexpected working-directory side effect')
    report=root/'ordinary-result.json'
    ordinary=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),
        spec.relative_to(ROOT)],'vis',row['id']+'-ordinary-authored-contract',env=environment(),timeout=130,campaign=Campaign())
    result=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
    if result['status']!='passed' or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
        raise RuntimeError('authored case or cleanup unconfirmed')
    immutable_json(RAW/'vis/approved'/(row['id']+'.json'),dict(case=row['id'],plan_sha256=plan_hash(row),
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
        spec=args.resume_export.resolve(strict=True);spec.relative_to((RAW/'vis/authoring'/selected[0]['id']).resolve())
        if json.loads((spec.parent/'declared-plan.json').read_text(encoding='utf-8-sig'))!=serialise(selected[0]):raise RuntimeError('original case plan differs')
        finished=json.loads((RAW/'events'/(args.capture_id+'-finished.json')).read_text())
        if finished['category']!='passed' or finished['exit_code']!=0:raise RuntimeError('original public export did not pass')
        if spec.parent.name not in (RAW/'vis'/args.capture_id/'console.log').read_text(encoding='utf-8'):raise RuntimeError('capture belongs to another output')
        await validate_and_test(selected[0],spec,args.capture_id,True)
        return
    batch=RAW/'vis/authoring-batches'/uuid.uuid4().hex;batch.mkdir(parents=True)
    immutable_json(batch/'declared.json',dict(rows=[serialise(r) for r in selected],qualification='declared, not executed'))
    failures=[]
    for row in selected:
        approved=RAW/'vis/approved'/(row['id']+'.json')
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
