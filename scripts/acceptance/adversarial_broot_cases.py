"""Declare owned Broot maintainer intentions; public recording must verify them."""
import json
from adversarial_process import DOC


def main():
    package=DOC/'broot'
    fixture=package/'fixtures-reviewed'
    config=json.dumps({'show_selection_mark':True,'true_colors':False,
        'enable_kitty_keyboard':False,'quit_on_last_cancel':False},indent=2)+'\n'
    files={'alpha.txt':'ALPHA ORIGINAL TOKEN\nProtected alpha second line.\n',
        'bravo.txt':'BRAVO ORIGINAL TOKEN\n',
        'protected.txt':'PROTECTED NEIGHBOR TOKEN\n',
        'nested/notes café.txt':'NESTED UNICODE NOTES TOKEN\nOther nested bytes.\n',
        'occupied/keep.txt':'OCCUPIED DIRECTORY TOKEN\n',
        'long.txt':''.join('line %02d: long café 雪 TOKEN\n'%i for i in range(60)),
        '.configuration/broot.hjson':config}
    for name,value in files.items():
        path=fixture/name
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()!=value.encode('utf-8'):
            raise RuntimeError('Refuse changing reviewed fixture bytes: '+name)
        path.write_bytes(value.encode('utf-8'))
    (fixture/'empty').mkdir(exist_ok=True)
    def text(value):return {'text':value}
    def key(value):return {'key':value}
    def expect(value):return {'expect':value}
    def choose(name):return [text(name),expect('▶└──'+name)]
    def execute(command):return [text(':'+command),key('Enter')]
    cases=[]
    def add(name,kind,purpose,steps,*,changed=None,absent=None,dirs=None,root='.',rows=(2,28)):
        expected=dict(files)
        expected.update(changed or {})
        for item in absent or []:expected.pop(item,None)
        cases.append(dict(name=name,kind=kind,purpose=purpose,
            command=['broot','--conf','.configuration/broot.hjson','--no-hidden',root],
            steps=[*steps,text(':quit'),key('Enter'),{'exit':0}],snapshot_after_step=len(steps),
            snapshot_rows=list(rows),timeout_ms=10000,expected_files=expected,
            absent_paths=absent or [],expected_directories=dirs or [],
            snapshot_exclusion='Exclude the random managed-root path and transient command/status rows; retain real tree/selection/preview content. Footer-only empty-view evidence is explicitly declared when needed.'))
    add('normal-project','normal','Copy a selected file to a spaced Unicode destination and preserve neighbors',
        [expect('alpha.txt'),*choose('alpha'),text(':cp '),text('copied café.txt'),key('Enter'),
         key('Escape'),expect('copied café.txt')],changed={'copied café.txt':files['alpha.txt']})
    add('normal-rename','normal','Move a real selected file to a new spaced Unicode name',
        [expect('bravo.txt'),*choose('bravo'),*execute('mv renamed café.txt'),key('Escape'),
         expect('renamed café.txt')],changed={'renamed café.txt':files['bravo.txt']},absent=['bravo.txt'])
    add('normal-nested-focus','normal','Focus a noninitial nested directory and inspect its actual children',
        [expect('alpha.txt'),*choose('nested'),key('Enter'),expect('/fixture/nested'),expect('notes café.txt')])
    add('normal-unicode-preview','normal','Preview a selected spaced Unicode text file without launching an editor',
        [expect('alpha.txt'),text('notes'),expect('▶   └──nested/notes café.txt'),*execute('preview_text'),
         expect('NESTED UNICODE NOTES TOKEN')])
    add('normal-mkdir','normal','Create a real nested directory through the supported local mkdir verb',
        [expect('alpha.txt'),text(':mkdir '),text('created-dir/sub'),key('Enter'),expect('created-dir')],
        dirs=['created-dir','created-dir/sub'])
    add('normal-content-search','normal','Search a noninitial text token and inspect its matching document',
        [expect('alpha.txt'),text('c/BRAVO'),expect('▶└──bravo.txt'),
         expect('BRAVO ORIGINAL TOKEN')])
    add('edge-empty-directory','edge','Inspect a truly empty fixture directory and quit naturally',
        [expect('alpha.txt'),*choose('empty'),key('Enter'),expect('/fixture/empty')],dirs=['empty'],rows=(29,30))
    add('edge-no-match-recovery','edge','Recover from an unmatched filter and still copy a useful file',
        [expect('alpha.txt'),text('ABSENTNEVERTOKEN'),expect('ABSENTNEVERTOKEN'),{'expect_not':'alpha.txt'},key('Escape'),
         expect('alpha.txt'),*choose('alpha'),*execute('cp recovered.txt'),key('Escape'),expect('recovered.txt')],
        changed={'recovered.txt':files['alpha.txt']})
    add('edge-cancel-operation','edge','Cancel a partially entered copy command without creating its destination',
        [expect('alpha.txt'),*choose('alpha'),text(':cp CANCEL NEVER.txt'),expect('alpha:cp CANCEL NEVER.txt'),
         key('Escape'),{'expect_not':'alpha:cp CANCEL NEVER.txt'},expect('bravo.txt')],absent=['CANCEL NEVER.txt'])
    add('edge-invalid-verb','edge','Recover from a genuine invalid verb without changing any input file',
        [expect('alpha.txt'),text(':not_a_real_verb'),expect('No matching verb'),key('Escape'),
         {'expect_not':'No matching verb'},*choose('alpha'),*execute('cp after-invalid.txt'),
         key('Escape'),expect('after-invalid.txt')],changed={'after-invalid.txt':files['alpha.txt']})
    add('edge-invalid-destination','edge','Recover after an unsuccessful external copy; independently verify no destination and intact inputs',
        [expect('alpha.txt'),*choose('alpha'),text(':cp absent-parent/destination.txt'),
         expect('alpha:cp absent-parent/destination.txt'),key('Enter'),
         expect('Hit alt-Enter to open and quit, esc to clear the filter'),
         {'expect_not':'alpha:cp absent-parent/destination.txt'},key('Escape'),expect('bravo.txt')],
        absent=['absent-parent/destination.txt'])
    add('edge-resize-preview','edge','Resize a long Unicode preview with observed redraw before dependent navigation',
        [expect('alpha.txt'),*choose('long'),*execute('preview_text'),expect('line 00:'),
         {'resize':{'width':80,'height':24}},{'wait_for_redraw':True},
         *execute('page_down'),expect('line 40:'),{'expect_not':'line 00:'},
         {'resize':{'width':100,'height':30}},{'wait_for_redraw':True},
         *execute('page_up'),expect('1 ▶line 00:')])
    value=dict(project='broot',fixture='fixtures-reviewed',
        environment={'TERM':'screen-256color','BR_INSTALL':'no'},cases=cases)
    (package/'scenarios.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (package/'fixture-directories.json').write_text(json.dumps(['fixtures-reviewed/empty'],indent=2)+'\n',encoding='utf-8')
    print('Declared',len(cases),'intentions; actual recording/review required before credit')


if __name__=='__main__':main()
