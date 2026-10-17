"""Declare and publicly author twenty offline bibliography workflows."""
import asyncio
import argparse
import base64
import hashlib
import json
import os
from pathlib import PurePosixPath
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_papis_first_use import environment,fixture_files


def text(value):return '/text '+json.dumps(value,ensure_ascii=True)
def expect(value):return '/expect '+value
def key(value):return '/key '+value
def absent(value):return '/absent '+value


def written(value,host):
    """Explicit native text-mode write contract; copied fixture bytes stay exact."""
    return value.replace(b'\n',b'\r\n') if host=='windows' else value


def csv_bytes(title,host):
    return written(('"title","year"\r\n"'+title+'","2024"\r\n').encode(),host)


def entry_sets(files,dirs):
    directories={'.',*dirs}
    for name in [*files,*dirs]:
        parent=PurePosixPath(name).parent
        while str(parent)!='.':directories.add(str(parent));parent=parent.parent
    nodes=set(files)|(directories-{'.'})
    return {d:sorted(PurePosixPath(n).name for n in nodes if str(PurePosixPath(n).parent)==d) for d in directories}


def rows(host=None):
    host=host or ('windows' if os.name=='nt' else 'linux')
    if host not in {'linux','windows'}:raise RuntimeError('undeclared Papis native host')
    seed=fixture_files();beta=[expect('Alpha Book'),key('ArrowDown'),expect('2/2')]
    select=[*beta,key('Enter')]
    folder=['export','--folder','--out','exported','--sort','title']
    csv=['export','--format','csv','--out','result.csv','--sort','title']
    def copied(files,book='beta',destination='exported'):
        return {destination+'/'+name:contents for path,contents in files.items()
                if path.startswith('library/'+book+'/') for name in [path.removeprefix('library/'+book+'/')]}
    def row(identity,title,args,actions,added=None,changed=None,missing=(),files=None,dirs=(),snapshot=False,exit=0,combined=()):
        files=dict(seed if files is None else files);expected={**files,**(added or {}),**(changed or {})}
        for name in missing:expected.pop(name,None)
        return dict(id=identity,title=title,kind='normal' if identity.startswith('N') else 'edge',
            args=args,actions=actions,files=files,expected=expected,missing=list(missing),dirs=list(dirs),
            entry_sets=entry_sets(expected,dirs),snapshot=snapshot,exit=exit,combined_risks=list(combined))
    common=[*select,expect('Writing to'),'/exit 0']
    beta_info=seed['library/beta/info.yaml']
    twofiles={**seed,'library/beta/attachment.bin':b'head\x00tail\r\n',
        'library/beta/info.yaml':beta_info.replace(b'- paper.txt\n',b'- paper.txt\n- attachment.bin\n')}
    unicode={k.replace('beta','caf\u00e9 \u96ea'):v for k,v in twofiles.items()}
    duplicated={**seed,'library/beta/info.yaml':beta_info.replace(b'Beta Book',b'Alpha Book')}
    long={**seed,'library/beta/info.yaml':beta_info.replace(b'Beta Book',b'Beta Book with an intentionally long title for a narrow terminal viewport')}
    many=dict(seed)
    for i in range(15):
        many['library/extra'+str(i).zfill(2)+'/info.yaml']=beta_info.replace(b'Beta Book',('Zeta '+str(i).zfill(2)).encode()).replace(b'beta',('extra'+str(i)).encode())
    preserved=b'keep existing export\r\n'
    result=[
        row('N01','export a nondefault document folder with exact attachment bytes',folder,
            [*beta,'/snapshot selected.txt',key('Enter'),expect('Exporting document'),'/exit 0'],copied(seed),snapshot=True),
        row('N02','export selected metadata as a spreadsheet CSV',csv,common,{'result.csv':csv_bytes('Beta Book',host)}),
        row('N03','append a selected bibliography export to preexisting content',csv+['--append'],
            [*select,expect('Appending to'),'/exit 0'],{'result.csv':preserved+csv_bytes('Beta Book',host)},files={**seed,'result.csv':preserved}),
        row('N04','add a tag to the selected entry and preserve other metadata',
            ['tag','--add','classic','--sort','title'],[*select,expect('Updated 1 / 1 documents'),'/exit 0'],
            changed={'library/beta/info.yaml':written(beta_info.replace(b'- reviewed\n',b'- reviewed\n- classic\n'),host)}),
        row('N05','change the title of one selected entry',
            ['update','--set','title','Revised Beta Book','--no-auto-doctor','--sort','title'],
            [*select,expect('Updated 1 / 1 documents'),'/exit 0'],changed={'library/beta/info.yaml':written(beta_info.replace(b'Beta Book',b'Revised Beta Book'),host)}),
        row('N06','remove one attached file with explicit confirmation',
            ['rm','--file','--sort','title'],[*select,expect('1/2'),key('Enter'),expect('Are you sure?'),text('y'),key('Enter'),expect('Removing file'),'/exit 0'],
            changed={'library/beta/info.yaml':written(beta_info.replace(b'- paper.txt',b'- attachment.bin'),host)},
            missing=['library/beta/paper.txt'],files=twofiles),
        row('N07','mark and export multiple selected folders',folder,
            [expect('Alpha Book'),text('\x14'),key('ArrowDown'),expect('2/2'),expect('#Alpha Book'),text('\x14'),key('Enter'),expect("Exporting document 'Beta Book - Ada Beta'"),'/exit 0'],
            {**copied(seed,'alpha','exported/alpha'),**copied(seed,'beta','exported/beta')}),
        row('N08','decline overwriting an existing export after selection',csv,
            [*select,expect('Overwrite?'),text('n'),key('Enter'),expect('Aborting.'),'/exit 0'],files={**seed,'result.csv':preserved}),
        row('E01','recover from an empty picker filter before export',folder,
            [expect('Alpha Book'),text('no-matching-entry'),expect('no-matching-entry'),absent('Alpha Book'),text('\x15'),expect('Alpha Book'),*beta[1:],key('Enter'),expect('Exporting document'),'/exit 0'],copied(seed)),
        row('E02','cancel a picker without producing an export',folder,
            [expect('Alpha Book'),text('\x03'),expect('No documents retrieved'),'/exit 0'],missing=['exported']),
        row('E03','reject invalid confirmation then decline overwrite',csv,
            [*select,expect('Overwrite?'),text('maybe'),expect('Please, write either'),text('\x15n'),key('Enter'),expect('Aborting.'),'/exit 0'],
            files={**seed,'result.csv':preserved},combined=['invalid input','correction','cancel','preexisting file']),
        row('E04','confirm replacing an existing binary export file',csv,
            [*select,expect('Overwrite?'),text('y'),key('Enter'),expect('Overwriting'),'/exit 0'],
            changed={'result.csv':csv_bytes('Beta Book',host)},files={**seed,'result.csv':b'old\x00bytes\r\n'}),
        row('E05','export a Unicode folder and preserve binary attachments',folder,
            [*select,expect('Exporting document'),'/exit 0'],copied(unicode,'caf\u00e9 \u96ea'),files=unicode,
            combined=['Unicode path','binary NUL/CRLF','multiple attachments']),
        row('E06','resize a long-title picker then filter and export',folder,
            [expect('Alpha Book'),'/resize 50 14','/redraw',text('Beta'),expect('> Beta'),'/resize 100 28','/redraw',key('Enter'),expect('Exporting document'),'/exit 0'],
            copied(long),files=long,combined=['small viewport','repeated resize','long title','search']),
        row('E07','navigate beyond the first viewport and return before export',folder,
            [expect('Alpha Book'),key('End'),expect('Zeta 14'),key('Home'),expect('1/17'),key('ArrowDown'),expect('2/17'),key('Enter'),expect('Exporting document'),'/exit 0'],copied(many),files=many),
        row('E08','disambiguate identical titles by author before export',folder,
            [expect('Ada Alpha'),expect('Ada Beta'),text('Ada Beta'),expect('> Ada Beta'),absent('Ada Alpha'),key('Enter'),expect('Exporting document'),'/exit 0'],
            copied(duplicated),files=duplicated,combined=['duplicate labels','author search','exact saved identity']),
        row('E09','unmark a previously selected entry before exporting another',folder,
            [expect('Alpha Book'),text('\x14'),key('ArrowDown'),expect('#Alpha Book'),key('ArrowUp'),expect('1/2'),text('\x14'),*beta[1:],absent('#Alpha Book'),key('Enter'),expect('Exporting document'),'/exit 0'],copied(seed)),
        row('E10','handle an empty synthetic library without writing an export',csv,
            [expect('No documents retrieved'),'/exit 0'],missing=['result.csv'],files={k:v for k,v in seed.items() if not k.startswith('library/')},dirs=['library']),
        row('E11','fail accurately when export parent directory is missing',
            ['export','--format','csv','--out','missing/result.csv','--sort','title'],
            [*select,expect('FileNotFoundError'),'/exit 1'],missing=['missing/result.csv'],exit=1),
        row('E12','inspect help and entry information before exporting exact bytes',folder,
            [expect('Alpha Book'),key('Tab'),text('help'),key('Enter'),'/screen',expect('Move cursor down in the list'),key('Escape'),key('Tab'),text('info'),key('Enter'),'/screen',expect("'author': 'Ada Alpha'"),key('Escape'),*beta[1:],key('Enter'),expect('Exporting document'),'/exit 0'],copied(seed),
            combined=['help overlay','metadata overlay','focus restoration','nondefault selection']),
    ]
    return result


def serialise(row):
    return {**row,'files':{n:base64.b64encode(b).decode() for n,b in row['files'].items()},
        'expected':{n:base64.b64encode(b).decode() for n,b in row['expected'].items()}}


def plan_hash(row):return hashlib.sha256(json.dumps(serialise(row),sort_keys=True).encode()).hexdigest()


async def author(row):
    root=RAW/'papis/authoring'/row['id']/uuid.uuid4().hex;fixture=root/'fixture';fixture.mkdir(parents=True)
    immutable_json(root/'declared-plan.json',serialise(row))
    for directory in row['dirs']:(fixture/directory).mkdir(parents=True,exist_ok=True)
    for name,value in row['files'].items():
        path=fixture/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
    controls=[*row['actions'],*['/file '+n for n in sorted(row['expected'])],*['/missing '+n for n in row['missing']],
        *['/entries '+n for n in sorted(row['entry_sets'])],'/review','/replay','/save']
    runner=RAW/('bin/playtestr.exe' if os.name=='nt' else 'bin/playtestr');spec=root/'spec.json'
    capture=await execute([runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture',
        '--temporary-home','--temporary-temp','--width','100','--height','28','--timeout-ms','15000',
        '--run-timeout-ms','120000','--env','TERM=xterm-256color','--env','PYTHONDONTWRITEBYTECODE=1',
        '--env','PYTHONIOENCODING=utf-8','--','papis','--config','config.ini','--lib','library','--np','1',
        '--color','no','--set','exporter-csv-keys',"['title','year']",*row['args']],
        'papis',row['id']+'-public-author-review-replay',env=environment(),input='\n'.join(controls)+'\n',timeout=240,campaign=Campaign())
    value=json.loads(spec.read_text(encoding='utf-8-sig'))
    actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in value['steps'] if s.get('state',{}).get('kind')=='file'}
    if actual!=row['expected']:raise RuntimeError('independent exact saved bytes differ for '+row['id'])
    missing={s['state']['path'] for s in value['steps'] if s.get('state',{}).get('kind')=='absent'}
    entries={s['state']['path']:sorted(s['state']['entries']) for s in value['steps'] if s.get('state',{}).get('kind')=='entries'}
    if missing!=set(row['missing']) or entries!=row['entry_sets']:raise RuntimeError('independent absence/directory-set oracle differs')
    report=root/'ordinary-results.json'
    ordinary=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
        (root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'papis',row['id']+'-ordinary-test',
        env=environment(),timeout=180,campaign=Campaign())
    outcome=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
    if outcome['status']!='passed' or not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
        raise RuntimeError('ordinary outcome or cleanup unconfirmed')
    immutable_json(root/'approved.json',dict(id=row['id'],plan_sha256=plan_hash(row),capture=capture['id'],ordinary=ordinary['id'],
        spec_sha256=sha256(spec),report_sha256=sha256(report),independent_exact_state=True,handwritten_spec=False))
    print(row['id'],'reviewed public recording and ordinary replay pass',flush=True)


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',action='append',choices=[r['id'] for r in rows()]);args=parser.parse_args()
    selected=[r for r in rows() if not args.case or r['id'] in args.case]
    failures=[]
    for row in selected:
        try:await author(row)
        except Exception as exc:failures.append(dict(id=row['id'],error=str(exc)));print(row['id'],'FAILED',str(exc),flush=True)
    immutable_json(RAW/'papis/authoring-batches'/(uuid.uuid4().hex+'.json'),dict(total=len(selected),selected=[r['id'] for r in selected],passed=len(selected)-len(failures),failures=failures))
    if failures:raise RuntimeError('preserved public authoring failures: '+str([f['id'] for f in failures]))


if __name__=='__main__':asyncio.run(main())
