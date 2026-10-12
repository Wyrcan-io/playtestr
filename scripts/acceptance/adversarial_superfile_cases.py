"""Declare useful superfile workflows; exact checkpoints are reviewed in real runs."""
import json
from adversarial_process import DOC


def main():
    package=DOC/'superfile'
    fixture=package/'fixtures'
    original={p.relative_to(fixture).as_posix():p.read_bytes().decode('utf-8')
              for p in fixture.rglob('*') if p.is_file()}
    cases=[]
    def text(value):return {'text':value}
    def key(value):return {'key':value}
    def expect(value):return {'expect':value}
    def start(token='ALPHA PREVIEW TOKEN'):
        return [expect('Thanks for using superfile'),key('Enter'),
                {'expect_not':'Thanks for using superfile'},expect(token)]
    def search(value,token):
        return [text('/'),text(value),key('Enter'),expect(token)]
    def add(name,kind,purpose,steps,*,paths=None,changed=None,absent=None):
        expected=dict(original)
        for name_to_remove in absent or []:expected.pop(name_to_remove,None)
        expected.update(changed or {})
        position=len(steps)
        cases.append(dict(name=name,kind=kind,purpose=purpose,
            command=['superfile','--config-file','.configuration/config.toml',*(paths or ['source'])],
            steps=[*steps,text('q'),{'exit':0}],snapshot_after_step=position,snapshot_rows=[4,20],
            timeout_ms=10000,expected_files=expected,absent_paths=absent or [],expected_exit=0,
            snapshot_exclusion='Rows 1–3 contain the random managed directory header; rows 21–30 contain host metadata, progress durations and clipboard paths. Explicit preview/transition checkpoints and exact independent file state remain required.'))
    add('normal-project','normal','Rename to a spaced Unicode name and inspect the preserved neighboring file',
        [*start(),key('CtrlR'),key('CtrlA'),key('CtrlK'),text('atlas café.txt'),key('Enter'),
         key('ArrowDown'),expect('BRAVO MOVE TOKEN')],
        changed={'source/atlas café.txt':original['source/alpha.txt']},absent=['source/alpha.txt'])
    add('normal-search-preview','normal','Search a noninitial nested file and inspect its exact preview',
        [*start('NESTED NOTES TOKEN'),*search('plan.txt','NONINITIAL PLAN TOKEN'),expect('Second exact line.')],paths=['nested'])
    add('normal-create-state','normal','Create a nested spaced Unicode file with its parent directory through the ordinary prompt',
        [*start(),key('CtrlN'),expect('transcend folders'),text('fresh folder/new café.txt'),key('Enter'),
         text('/'),text('fresh folder'),key('Enter'),expect('>  fresh folder'),key('ArrowRight'),expect('>  new café.txt')],
        changed={'source/fresh folder/new café.txt':''})
    for name,source,action,token in [('normal-panel-copy','alpha.txt','CtrlC','ALPHA PREVIEW TOKEN'),
                                   ('normal-panel-move','bravo.txt','CtrlX','BRAVO MOVE TOKEN')]:
        steps=start()
        if source=='bravo.txt':steps += [key('ArrowDown'),expect(token)]
        steps += [key(action),key('Tab'),expect('No metadata present'),key('CtrlV'),expect(token)]
        add(name,'normal','Built-in '+('copy' if action=='CtrlC' else 'move')+' into a different open panel',
            steps,paths=['source','destination'],changed={'destination/'+source:original['source/'+source]},
            absent=['source/'+source] if action=='CtrlX' else [])
    add('normal-multiple-selection','normal','Select two nonadjacent files and copy the exact set into another panel',
        [*start(),text('v'),key('Enter'),key('ArrowDown'),key('ArrowDown'),key('Enter'),key('CtrlC'),key('Tab'),
         expect('No metadata present'),key('CtrlV'),expect('ALPHA PREVIEW TOKEN')],
        paths=['source','destination'],changed={'destination/alpha.txt':original['source/alpha.txt'],
            'destination/charlie.txt':original['source/charlie.txt']})
    add('edge-empty-recovery','edge','Start in an empty directory and recover through another useful panel',
        [*start('No such file or directory'),key('Tab'),expect('ALPHA PREVIEW TOKEN')],paths=['empty','source'])
    add('edge-no-match-recovery','edge','Filter to no matching item, clear the search, and select a genuine file',
        [*start(),text('/'),text('absent-never-name'),expect('No such file or directory'),key('Escape'),
         expect('ALPHA PREVIEW TOKEN'),key('ArrowDown'),expect('BRAVO MOVE TOKEN')])
    add('edge-cancel-edited-rename','edge','Cancel after editing a filename and preserve exact original and neighboring bytes',
        [*start(),key('CtrlR'),key('CtrlA'),key('CtrlK'),text('abandoned-name.txt'),expect('abandoned-name.txt'),
         key('Escape'),{'expect_not':'abandoned-name.txt'},key('ArrowDown'),expect('BRAVO MOVE TOKEN')],
        absent=['source/abandoned-name.txt'])
    add('edge-cancel-delete','edge','Decline a destructive permanent-delete confirmation and preserve exact files',
        [*start(),text('D'),expect('This operation cannot be undone'),key('Escape'),
         {'expect_not':'This operation cannot be undone'},key('ArrowDown'),expect('BRAVO MOVE TOKEN')])
    add('edge-name-conflict','edge','Decline replacing an occupied file with different content',
        [*start(),key('CtrlR'),key('CtrlA'),key('CtrlK'),text('occupied.txt'),key('Enter'),
         expect('This operation will override'),key('Escape'),{'expect_not':'This operation will override'},
         key('ArrowDown'),expect('BRAVO MOVE TOKEN')])
    add('edge-resize-scroll','edge','Resize repeatedly, search an initially offscreen item and inspect Unicode long content',
        [*start(),{'resize':{'width':80,'height':24}},*search('scroll-34.txt','SCROLL ITEM 34 TOKEN'),
         text('/'),key('CtrlA'),key('CtrlK'),text('long.txt'),key('Enter'),
         expect('line 00: long preview café 雪'),
         {'resize':{'width':120,'height':35}},expect('line 20: long preview café 雪'),
         {'resize':{'width':100,'height':30}},text('/'),key('CtrlA'),key('CtrlK'),text('scroll-33.txt'),key('Enter'),expect('SCROLL ITEM 33 TOKEN')])
    (package/'scenarios.json').write_text(json.dumps(dict(project='superfile',fixture='fixtures',
        environment={'TERM':'xterm-256color'},cases=cases),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (package/'fixture-directories.json').write_text(json.dumps(['fixtures/empty','fixtures/destination'],indent=2)+'\n')
    print('Declared',len(cases),'superfile intentions; real recorder review and independent state required')


if __name__=='__main__':main()
