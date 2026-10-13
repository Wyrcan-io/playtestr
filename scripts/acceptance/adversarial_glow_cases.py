"""Declare offline reader intentions; no exported contract is manufactured here."""
import json
from adversarial_process import DOC


def main():
    package=DOC/'glow'
    fixture=package/'fixtures'
    files={
        'overview.md':'# overview\n\nPROJECT OVERVIEW TOKEN\n\nProtected documentation paragraph.\n',
        'guide.md':'# guide\n\nguide DOCUMENT TOKEN\n\nSECOND DOCUMENT BODY\n',
        'nested/notes café.md':'# Nested notes\n\nNESTED UNICODE café 雪 TOKEN\n',
        'structured.md':'# Structured reference\n\nSTRUCTURED REFERENCE TOKEN\n\n```go\nfmt.Println("CODE BLOCK TOKEN")\n```\n\n| Key | Value |\n| --- | --- |\n| Setting | TABLE CELL TOKEN |\n',
        'long.md':'# Long reference\n\n'+''.join('PARAGRAPH %02d café 雪 TOKEN\n\n'%i for i in range(80)),
        'empty.md':'',
        'protected.txt':'PROTECTED NON-MARKDOWN NEIGHBOR\n',
        'empty-library/.keep':'OWNED EMPTY MARKDOWN LIBRARY\n',
    }
    for relative,value in files.items():
        path=fixture/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()!=value.encode('utf-8'):
            raise RuntimeError('Refuse changing existing reader fixture: '+relative)
        path.write_bytes(value.encode('utf-8'))
    def text(value):return {'text':value}
    def key(value):return {'key':value}
    def expect(value):return {'expect':value}
    def absent(value):return {'expect_not':value}
    def choose(query,body):return [text('/'),text(query),key('Enter'),expect(body)]
    base=['glow','--style','dark','--mouse=false']
    cases=[]
    def add(name,kind,purpose,steps,*,arguments=None):
        cases.append(dict(name=name,kind=kind,purpose=purpose,
            command=[*base,*(arguments or [])],steps=[*steps,text('q'),{'exit':0}],
            snapshot_after_step=len(steps),snapshot_rows=[1,29],timeout_ms=10000,
            expected_files=files,absent_paths=[],expected_exit=0,
            snapshot_exclusion='Only the last footer row is excluded; rendered document body and fresh transition checkpoints remain. Browser age labels are not accepted as deterministic body baselines.'))
    add('normal-project','normal','Discover local documentation and read a specifically filtered overview',
        [expect('6 documents'),*choose('overview','PROJECT OVERVIEW TOKEN')])
    add('normal-nested-unicode','normal','Filter and read a nested spaced Unicode document',
        [expect('6 documents'),*choose('notes cafe','NESTED UNICODE café 雪 TOKEN')])
    add('normal-long-scroll','normal','Read noninitial long-document pages and return to the beginning',
        [expect('PARAGRAPH 00'),text('G'),expect('PARAGRAPH 79'),text('g'),expect('PARAGRAPH 00')],arguments=['--tui','long.md'])
    add('normal-document-switch','normal','Return from one document and select a different useful document',
        [expect('6 documents'),*choose('overview','PROJECT OVERVIEW TOKEN'),key('Escape'),
         expect('6 documents'),*choose('guide','guide DOCUMENT TOKEN')])
    add('normal-structured-reference','normal','Read code and validate Markdown table reflow at two reviewed viewport widths',
        [expect('STRUCTURED REFERENCE TOKEN'),expect('CODE BLOCK TOKEN'),expect('TABLE CELL TOKEN'),
         {'resize':{'width':80,'height':30}},expect('Key'+' '*34+'│ Value'),
         {'resize':{'width':100,'height':30}},expect('Key'+' '*44+'│ Value')],arguments=['--tui','structured.md'])
    add('normal-line-numbers','normal','Read with explicit line numbers and navigate to a noninitial viewport',
        [expect('PARAGRAPH 00'),text('G'),expect('PARAGRAPH 79')],arguments=['--tui','--line-numbers','long.md'])
    add('edge-empty-library','edge','Handle a library containing no Markdown files and quit naturally',
        [expect('No files found.')],arguments=['empty-library'])
    add('edge-no-match-recovery','edge','Recover from an empty filter result and open a useful document',
        [expect('6 documents'),text('/'),text('ABSENT NEVER DOCUMENT'),expect('ABSENT NEVER DOCUMENT'),
         expect('No files found.'),key('Escape'),
         expect('6 documents'),*choose('guide','guide DOCUMENT TOKEN')])
    add('edge-cancel-filter','edge','Cancel a partial filter and continue with the original complete library',
        [expect('6 documents'),text('/'),text('over'),expect('Find: over'),key('Escape'),expect('6 documents'),
         *choose('guide','guide DOCUMENT TOKEN')])
    add('edge-empty-document','edge','Render an empty Markdown file without hanging or changing any input',
        [expect('empty.md'),expect('100%')],arguments=['--tui','empty.md'])
    cases[-1]['snapshot_rows']=[1,30]
    cases[-1]['snapshot_exclusion']='No rows excluded: the empty body and its real filename/percentage footer together provide meaningful evidence.'
    add('edge-resize-scroll','edge','Resize narrow and wide while navigating long Unicode documentation',
        [expect('PARAGRAPH 00'),{'resize':{'width':45,'height':18}},text('G'),expect('PARAGRAPH 79'),
         {'resize':{'width':120,'height':35}},text('g'),expect('PARAGRAPH 00'),
         {'resize':{'width':100,'height':30}},text('G'),expect('PARAGRAPH 79')],arguments=['--tui','long.md'])
    add('edge-long-filter-recovery','edge','Recover from a long unmatched input and select a Unicode filename',
        [expect('6 documents'),text('/'),text('UNMATCHED'+('Z'*240)),expect('Find: ZZZZZZZZZZZZ'),
         expect('No files found.'),key('Escape'),
         expect('6 documents'),*choose('notes cafe','NESTED UNICODE café 雪 TOKEN')])
    (package/'scenarios.json').write_text(json.dumps(dict(project='glow',fixture='fixtures',
        environment={'TERM':'screen-256color','GLAMOUR_STYLE':'dark','GLOW_TEXT_SIZING':'off'},cases=cases,
        windows_target_race_check={'case':'normal-project','count':10}),
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Declared',len(cases),'reader intentions; actual public recording and review still required')


if __name__=='__main__':main()
