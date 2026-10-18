"""Declare and publicly author twenty local Markdown browsing workflows."""
import argparse
import asyncio
import base64
import json
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_frogmouth_first_use import ADDRESS_FOCUS_BORDER,SOURCE,command,environment,fixture_files,runner
from readiness_papis_cases import entry_sets,plan_hash,serialise


def text(value):return '/text '+json.dumps(value,ensure_ascii=True)
def expect(value):return '/expect '+value
def key(value):return '/key '+value


def rows(host=None):
    seed=fixture_files();start=[expect('Alpha body independent source.'),text('\x0e'),expect('Contents')]
    finish=[text('\x11'),'/exit 0']
    navigate=[*start,*command('beta.md'),expect('Beta body independent source.')]
    long=b'# Alpha guide\n\nAlpha body independent source.\n\n'+b'Reviewed scrollable paragraph.\n\n'*30+b'## Deep destination\n\nDeep destination independently reached.\n'
    def row(identity,title,actions,files=None,combined=()):
        files=dict(seed if files is None else files)
        return dict(id=identity,title=title,kind='normal' if identity.startswith('N') else 'edge',args=['alpha.md'],
            actions=[*actions,'/snapshot-rows '+identity+'.rows.json 4 26',*finish],files=files,expected=files,
            missing=[],dirs=[],entry_sets=entry_sets(files,[]),snapshot=True,exit=0,combined_risks=list(combined))
    result=[
        row('N01','open a nondefault local document through the address bar',navigate),
        row('N02','jump to a below-viewport heading through the table of contents',
            [*start,key('End'),key('Enter'),expect('Deep destination independently reached.')],{**seed,'alpha.md':long}),
        row('N03','browse the current directory and select a Markdown file',
            [*start,*command('chdir .'),expect('beta.md'),key('Home'),key('ArrowDown'),key('ArrowDown'),key('Enter'),expect('Beta body independent source.')]),
        row('N04','revisit the earlier document through browsing history',
            [*navigate,text('\x19'),expect('alpha.md'),key('Home'),key('ArrowDown'),key('Enter'),expect('Alpha body independent source.')]),
        row('N05','bookmark a selected document and revisit it after navigating away',
            [*navigate,text('\x04'),expect('Bookmark title:'),key('Enter'),'/absent Bookmark title:',
             *command('alpha.md'),expect('Alpha body independent source.'),text('\x02'),expect('beta.md'),key('Enter'),expect('Beta body independent source.')]),
        row('N06','decline then confirm clearing browsing history while preserving the current document',
            [*navigate,text('\x19'),expect('alpha.md'),key('Backspace'),expect('Clear history?'),key('ArrowRight'),key('Enter'),
             '/absent Clear history?',expect('alpha.md'),key('Backspace'),expect('Clear history?'),key('Enter'),'/absent Clear history?','/absent alpha.md']),
        row('N07','reload a scrolled document and return to its beginning',
            [*start,key('End'),key('Enter'),expect('Deep destination independently reached.'),text('\x12'),expect('Alpha body independent source.')],{**seed,'alpha.md':long}),
        row('N08','page through a long document and recover the first page',
            [*start,text('\x0e'),'/absent Contents',key('End'),expect('Deep destination independently reached.'),key('Home'),expect('Alpha body independent source.')],{**seed,'alpha.md':long}),
        row('E01','recover from a missing local document without modifying the originals',
            [*start,*command('missing.md'),expect('Error loading'),key('Enter'),'/absent Error loading',text('\x14'),'/absent '+ADDRESS_FOCUS_BORDER,*command('beta.md'),expect('Beta body independent source.')],combined=['missing file','error dialog','focus recovery']),
        row('E02','cancel a partially entered address and preserve the current document',
            [*start,*command('beta.md')[:-1],text('\x15'),'/absent beta.md',text('\x0e'),'/absent Contents']),
    ]
    def document(identity,title,content,anchor,name='beta.md',extra=(),combined=()):
        files={**seed,name:content}
        return row(identity,title,[*start,*command(name),*([expect(anchor)] if anchor else []),*extra],files,combined)
    result.extend([
        document('E03','display a CRLF document with explicit original byte preservation',b'# CRLF guide\r\n\r\nCRLF body independently rendered.\r\n','CRLF body independently rendered.'),
        document('E04','open a spaced Unicode path with Unicode CRLF content', '# Unicode guide\r\n\r\nReviewed caf\u00e9 \u96ea destination.\r\n'.encode(),'Reviewed caf\u00e9 \u96ea destination.','caf\u00e9 \u96ea guide.md',combined=['Unicode path','spaces','Unicode cells','CRLF bytes']),
        document('E05','render fenced source code without interpreting its markup',b'# Source guide\n\n```python\nprint("fenced_code_marker")\n```\n','fenced_code_marker'),
        document('E06','render a Markdown table after narrowing and restoring the viewport',b'# Table guide\n\n| Key | Value |\n| --- | --- |\n| table_marker | reviewed |\n','table_marker',extra=['/resize 70 28','/redraw',text('\x0e'),'/absent Contents','/resize 100 28','/redraw',text('\x0e'),expect('Contents')],combined=['table layout','narrow viewport','repeated resize']),
        document('E07','render nested list indentation and escaped markup',b'# List guide\n\n- parent item\n  - nested_list_marker\n\nEscaped \\*literal\\* text.\n','nested_list_marker'),
        document('E08','hide YAML front matter while retaining its exact bytes',b'---\nsecret_metadata_marker: synthetic\n---\n# Metadata guide\n\nVisible frontmatter body.\n','Visible frontmatter body.',extra=['/absent Alpha body independent source.'],combined=['front matter','rendered/source distinction','binary sentinel preservation']),
        document('E09','open an empty Markdown file and remove the previous document view',b'',None,extra=['/absent Alpha body independent source.']),
        document('E10','render incomplete Markdown fences as bounded plain content',b'# Incomplete guide\n\n```text\nunfinished_fence_marker\n','unfinished_fence_marker'),
        document('E11','open a long spaced Unicode filename as a local path',b'# Long filename\n\nLong filename destination body.\n','Long filename destination body.','reviewed long local guide '+('segment '*6)+'caf\u00e9.md',combined=['long filename','spaces','Unicode path','path scrolling']),
        document('E12','resize a document with wide characters and combining marks', '# Wide guide\n\nWide cells \u96ea\u754c and combining e\u0301 remain source exact.\n'.encode(),'Wide cells',extra=['/resize 70 28','/redraw',text('\x0e'),'/absent Contents','/resize 100 28','/redraw',text('\x0e'),expect('Contents')],combined=['wide cells','combining marks','repeated resize','exact UTF-8 bytes']),
    ])
    return result


async def author(row):
    root=RAW/'frogmouth/authoring'/row['id']/uuid.uuid4().hex;fixture=root/'fixture';fixture.mkdir(parents=True)
    immutable_json(root/'declared-plan.json',serialise(row))
    for name,value in row['files'].items():
        path=fixture/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
    controls=[*row['actions'],*['/file '+n for n in sorted(row['expected'])],*['/entries '+n for n in sorted(row['entry_sets'])],'/review','/replay','/save']
    binary=runner();spec=root/'spec.json'
    capture=await execute([binary,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--width','100','--height','28','--timeout-ms','15000','--run-timeout-ms','120000','--env','TERM=xterm-256color',
        '--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONIOENCODING=utf-8','--','frogmouth',*row['args']],
        'frogmouth',row['id']+'-public-author-review-replay',env=environment(),input='\n'.join(controls)+'\n',timeout=240,campaign=Campaign())
    value=json.loads(spec.read_text(encoding='utf-8-sig'))
    actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in value['steps'] if s.get('state',{}).get('kind')=='file'}
    entries={s['state']['path']:sorted(s['state']['entries']) for s in value['steps'] if s.get('state',{}).get('kind')=='entries'}
    if actual!=row['expected'] or entries!=row['entry_sets']:raise RuntimeError('independent file/directory oracle differs')
    report=root/'ordinary-results.json'
    ordinary=await execute([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'frogmouth',row['id']+'-ordinary-test',env=environment(),timeout=180,campaign=Campaign())
    evidence=json.loads(report.read_text(encoding='utf-8-sig'));outcome=evidence['results'][0]
    if evidence['runner_version']!='source-'+SOURCE or outcome['status']!='passed' or not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:raise RuntimeError('wrong runner/outcome or cleanup unconfirmed')
    immutable_json(root/'approved.json',dict(id=row['id'],plan_sha256=plan_hash(row),capture=capture['id'],ordinary=ordinary['id'],spec_sha256=sha256(spec),report_sha256=sha256(report),independent_exact_state=True,handwritten_spec=False))
    print(row['id'],'reviewed public recording and ordinary test pass',flush=True)


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',action='append',choices=[r['id'] for r in rows()]);args=parser.parse_args()
    selected=[r for r in rows() if not args.case or r['id'] in args.case];failures=[]
    for row in selected:
        try:await author(row)
        except Exception as exc:failures.append(dict(id=row['id'],error=str(exc)));print(row['id'],'FAILED',exc,flush=True)
    immutable_json(RAW/'frogmouth/authoring-batches'/(uuid.uuid4().hex+'.json'),dict(total=len(selected),selected=[r['id'] for r in selected],passed=len(selected)-len(failures),failures=failures))
    if failures:raise RuntimeError('Preserved public authoring failures: '+str([r['id'] for r in failures]))


if __name__=='__main__':asyncio.run(main())
