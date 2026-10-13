"""Predeclare plain-text maintainer workflows; real recorder review is required."""
import json
from adversarial_process import DOC


def main():
    package=DOC/'helix';fixture=package/'fixtures'
    files={'main.txt':'ORIGINAL MAIN TOKEN\nProtected second line.\n',
        'second.txt':'SECOND BUFFER TOKEN\nOriginal second bytes.\n',
        'selection.txt':'alpha bravo charlie\nProtected neighboring line.\n',
        'nested/notes café.txt':'NESTED NOTES TOKEN\nOther nested bytes.\n',
        'protected.txt':'PROTECTED NEIGHBOR TOKEN\nNever change this file.\n',
        'occupied/keep.txt':'OCCUPIED DIRECTORY TOKEN\n',
        'long.txt':''.join('line %02d: long text café 雪\n'%i for i in range(60)),
        '.configuration/config.toml':'''theme = "base16_default_dark"
[editor]
mouse = false
auto-completion = false
path-completion = false
auto-format = false
auto-info = false
bufferline = "always"
default-line-ending = "lf"
clipboard-provider = "none"
editor-config = false
kitty-keyboard-protocol = "disabled"
gutters = ["line-numbers", "spacer"]
[editor.auto-save]
focus-lost = false
[editor.auto-save.after-delay]
enable = false
[editor.lsp]
enable = false
[editor.statusline]
left = ["mode", "file-name", "file-modification-indicator"]
right = ["position", "file-encoding", "file-line-ending"]
'''}
    for relative,value in files.items():
        path=fixture/relative;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()!=value.encode('utf-8'):
            raise RuntimeError('Refuse changing an existing fixture contract: '+relative)
        path.write_bytes(value.encode('utf-8'))
    def text(value):return {'text':value}
    def key(value):return {'key':value}
    def expect(value):return {'expect':value}
    def command(value):return [text(':'+value),key('Enter')]
    # Helix retains the buffer's final newline when changing the full selection.
    # Insert the body, preserving the intended single reviewed trailing LF.
    def replace(value):
        body=value[:-1] if value.endswith('\n') else value
        steps=[text('%'),text('c'),expect('INS')]
        for position,line in enumerate(body.split('\n')):
            if position:steps.append(key('Enter'))
            if line:steps.append(text(line))
        return [*steps,key('Escape'),expect('NOR')]
    def save(name='main.txt'):return [*command('w'),expect("'"+name+"' written")]
    cases=[]
    def add(name,kind,purpose,steps,*,paths=None,changed=None,absent=None,quit='q'):
        expected=dict(files);expected.update(changed or {})
        cases.append(dict(name=name,kind=kind,purpose=purpose,
            command=['hx','--config','.configuration/config.toml',*(['main.txt'] if paths is None else paths)],
            steps=[*steps,*command(quit),{'exit':0}],snapshot_after_step=len(steps),
            snapshot_rows=[1,29],timeout_ms=10000,expected_files=expected,
            absent_paths=absent or [],expected_exit=0,
            snapshot_exclusion='Only transient bottom command/status messages are excluded. Content, buffer identity, mode and position remain in rows 1–29; explicit command outcomes and exact independent files complement the capture.'))
    updated='Reviewed project café 雪\nProtected second line.\n'
    add('normal-project','normal','Replace and save a complete Unicode document while preserving its neighbor',
        [expect('ORIGINAL MAIN TOKEN'),*replace(updated),expect('Reviewed project café 雪'),*save()],changed={'main.txt':updated})
    add('normal-buffer-switch','normal','Switch to a second buffer, save a real change and return to the first',
        [expect('ORIGINAL MAIN TOKEN'),*command('buffer-next'),expect('SECOND BUFFER TOKEN'),
         *replace('SECOND REVISED TOKEN\n'),*save('second.txt'),*command('buffer-previous'),expect('ORIGINAL MAIN TOKEN')],
        paths=['main.txt','second.txt'],changed={'second.txt':'SECOND REVISED TOKEN\n'})
    add('normal-nested-open','normal','Open a spaced Unicode path through the command prompt and edit its content',
        [expect('ORIGINAL MAIN TOKEN'),*command('open "nested/notes café.txt"'),expect('NESTED NOTES TOKEN'),
         *replace('NESTED REVISED TOKEN\n'),*command('w'),expect("notes café.txt' written")],changed={'nested/notes café.txt':'NESTED REVISED TOKEN\n'})
    cases[-1]['baseline_suffix_by_host']={'Linux':'-unix','Darwin':'-unix'}
    add('normal-selection-replace','normal','Replace one selected word and preserve surrounding words and lines',
        [expect('alpha bravo charlie'),text('e'),text('c'),text('ALPHA'),key('Escape'),expect('ALPHA bravo charlie'),*save('selection.txt')],
        paths=['selection.txt'],changed={'selection.txt':'ALPHA bravo charlie\nProtected neighboring line.\n'})
    add('normal-undo-redo','normal','Undo and redo a substantive edit before saving its exact final bytes',
        [expect('ORIGINAL MAIN TOKEN'),*replace('UNDO REDO TOKEN\n'),expect('UNDO REDO TOKEN'),text('u'),expect('ORIGINAL MAIN TOKEN'),
         text('U'),expect('UNDO REDO TOKEN'),*save()],changed={'main.txt':'UNDO REDO TOKEN\n'})
    add('normal-create-name','normal','Create and save a new spaced Unicode filename from an empty buffer',
        [expect('NOR  [scratch]'),text('i'),expect('INS'),text('NEW FILE TOKEN café 雪'),key('Escape'),expect('NOR'),
         *command('write "created café.txt"'),expect("'created café.txt' written")],paths=[],changed={'created café.txt':'NEW FILE TOKEN café 雪\n'})
    add('edge-unsaved-quit','edge','Reject an ordinary quit with unsaved bytes, then explicitly discard them',
        [expect('ORIGINAL MAIN TOKEN'),*replace('UNSAVED NEVER PERSIST TOKEN\n'),*command('q'),expect('unsaved buffer'),expect('UNSAVED NEVER PERSIST TOKEN')],quit='q!')
    add('edge-invalid-command','edge','Recover from a genuine unknown command and still save a useful edit',
        [expect('ORIGINAL MAIN TOKEN'),*command('not-a-real-command'),expect("no such command: 'not-a-real-command'"),
         *replace('RECOVERY SAVED TOKEN\n'),*save()],changed={'main.txt':'RECOVERY SAVED TOKEN\n'})
    add('edge-cancel-command','edge','Cancel a partially entered destructive command and continue with intact files',
        [expect('ORIGINAL MAIN TOKEN'),text(':quit!'),expect(':quit!'),key('Escape'),{'expect_not':':quit!'},text('j'),expect('2:1')])
    add('edge-no-match-recovery','edge','Search for a missing token, cancel, and search a real noninitial line',
        [expect('ORIGINAL MAIN TOKEN'),text('/'),text('ABSENT NEVER TOKEN'),key('Enter'),text('n'),expect('No more matches'),
         key('Escape'),{'expect_not':'No more matches'},text('/'),expect('search:'),text('Protected second line'),key('Enter'),
         {'expect_not':'search:'},expect('Protected second line.')])
    add('edge-invalid-save','edge','Attempt to save over an occupied directory, recover and preserve protected bytes',
        [expect('ORIGINAL MAIN TOKEN'),*replace('SAVE RECOVERY TOKEN\n'),*command('write occupied'),
         expect('file modified by an external process'),*command('write! main.txt'),
         expect("'main.txt' written")],changed={'main.txt':'SAVE RECOVERY TOKEN\n'})
    # Unix directory mtimes depend on fixture-copy timing. Explicit force skips
    # that preliminary check and exercises the real directory-write refusal.
    # Keep this contract separate from the observed Windows mtime refusal.
    cases[-1]['baseline_suffix_by_host']={'Linux':'-unix'}
    cases[-1]['steps_by_host']={'Linux':[
        {'expect':'Is a directory (os error 21)'} if step=={'expect':'file modified by an external process'} else
        {'text':':write! occupied'} if step=={'text':':write occupied'} else step
        for step in cases[-1]['steps']]}
    add('edge-resize-scroll','edge','Repeatedly resize and navigate a long Unicode document without saving unwanted edits',
        [expect('line 00: long text café 雪'),{'resize':{'width':80,'height':24}},text('ge'),expect('line 59: long text café 雪'),
         {'resize':{'width':120,'height':35}},text('gg'),expect('line 00: long text café 雪'),
         {'resize':{'width':100,'height':30}},text('ge'),expect('line 59: long text café 雪')],paths=['long.txt'])
    (package/'scenarios.json').write_text(json.dumps(dict(project='helix',fixture='fixtures',environment={'TERM':'xterm-256color'},cases=cases),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Declared',len(cases),'Helix intentions; actual authoring review is still required')


if __name__=='__main__':main()
