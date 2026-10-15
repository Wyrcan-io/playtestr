"""Prepare synthetic Ranger inputs; only actual recording establishes contracts."""
import argparse
import copy
import json
from adversarial_process import DOC


def main():
    package=DOC/'ranger'
    path=package/'scenarios.json'
    if path.exists():raise RuntimeError('Refuse replacing declared Ranger intentions')
    files={
        'alpha.txt':'RANGER ALPHA ORIGINAL TOKEN\nProtected alpha second line.\n',
        'bravo.txt':'RANGER BRAVO ORIGINAL TOKEN\n',
        'protected.txt':'RANGER PROTECTED NEIGHBOR TOKEN\n',
        'nested/notes caf\u00e9.txt':'RANGER NESTED UNICODE TOKEN\nProtected nested bytes.\n',
        'occupied/keep.txt':'RANGER OCCUPIED DIRECTORY TOKEN\n',
        'long.txt':''.join('line %03d: ranger caf\u00e9 \u96ea TOKEN\n'%i for i in range(120)),
    }
    for name,value in files.items():
        target=package/'fixtures'/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():raise RuntimeError('Refuse replacing synthetic Ranger input')
        target.write_bytes(value.encode('utf-8'))
    (package/'fixtures/empty').mkdir(exist_ok=True)
    command=['ranger','--clean','--cmd=set preview_files true',
             '--cmd=set use_preview_script false','--cmd=set confirm_on_delete always',
             '--cmd=set hostname_in_titlebar false','.']
    case=dict(name='explore-startup',kind='exploration',
              purpose='Observe ordinary clean Ranger startup and natural quit; no scenario credit',
              command=command,steps=[{'expect':'alpha.txt'},{'text':'q'},{'exit':0}],
              snapshot_after_step=1,snapshot_rows=[2,28],timeout_ms=10000,
              expected_files=files,expected_directories=['empty','nested','occupied'],
              empty_directories=['empty'],exact_tree=True)
    path.write_bytes((json.dumps(dict(project='ranger',fixture='fixtures',
        environment={'TERM':'screen-256color'},cases=[case]),indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
    (package/'fixture-directories.json').write_bytes(b'["fixtures/empty"]\n')
    print('Prepared exploratory inputs only; actual contracts and qualification remain pending')


def promote():
    package=DOC/'ranger';path=package/'scenarios.json'
    config=json.loads(path.read_text(encoding='utf-8'))
    if [c['name'] for c in config['cases']]!=['explore-startup']:
        raise RuntimeError('Primary promotion requires the original exploratory intentions')
    archive=package/'exploratory-scenarios.json'
    if archive.exists():raise RuntimeError('Refuse replacing exploration history')
    archive.write_bytes(path.read_bytes())
    case=copy.deepcopy(config['cases'][0])
    case.update(name='normal-project',kind='normal',
        purpose='Create a spaced Unicode file through the ordinary command console and preserve the complete fixture',
        steps=[{'expect':'alpha.txt'},{'expect':'All'},{'text':':'},
               {'expect_not':'All'},{'expect':':'},
               {'text':'touch created caf\u00e9.txt'},{'expect':':touch created caf\u00e9.txt'},
               {'key':'Enter'},{'expect_not':':touch created caf\u00e9.txt'},{'expect':'created caf\u00e9.txt'},
               {'text':'q'},{'exit':0}],snapshot_after_step=10)
    case['expected_files']['created caf\u00e9.txt']=''
    config['cases']=[case]
    path.write_bytes((json.dumps(config,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))


def extend():
    package=DOC/'ranger';path=package/'scenarios.json'
    config=json.loads(path.read_text(encoding='utf-8'))
    if [c['name'] for c in config['cases']]!=['normal-project']:
        raise RuntimeError('Extension requires the single reviewed primary intention')
    primary=config['cases'][0];files=dict(primary['expected_files'])
    files.pop('created caf\u00e9.txt')
    text=lambda value:{'text':value}
    expect=lambda value:{'expect':value}
    absent=lambda value:{'expect_not':value}
    key=lambda value:{'key':value}
    observed=json.loads((package/'snapshots/explore-startup.rows.json').read_text(encoding='utf-8'))['text']
    def row(name):
        line=next(line for line in observed.splitlines() if name in line)
        return line[line.index(name):]
    def console(command,resume=True):
        full=':'+command
        return [expect('All'),text(':'),absent('All'),expect(':'),text(command),
                expect(full),key('Enter'),absent(full),*([expect('All')] if resume else [])]
    def select(query,relative,preview=None):
        return [text('/'),expect(':search'),text(query),expect(':search '+query),
                key('Enter'),absent(':search '+query),expect('/fixture/'+relative),
                *([expect(preview)] if preview else [])]
    def into_nested():
        return [*select('nested','nested'),text('l'),expect('/fixture/nested/notes caf\u00e9.txt'),
                expect('RANGER NESTED UNICODE TOKEN')]
    def add(name,kind,purpose,steps,*,changed=None,missing=(),dirs=(),empty=(),position=None,rows=(2,28),fixture=None,expected=None):
        data=dict(files if expected is None else expected);data.update(changed or {})
        for removed in missing:data.pop(removed,None)
        case=dict(name=name,kind=kind,purpose=purpose,command=primary['command'],
            steps=[expect('alpha.txt') if fixture is None else expect('/fixture/file 000.txt'),*steps,text('q'),{'exit':0}],
            snapshot_after_step=1+(len(steps) if position is None else position),snapshot_rows=list(rows),
            timeout_ms=10000,expected_files=data,absent_paths=list(missing),
            expected_directories=['empty','nested','occupied',*dirs] if fixture is None else list(dirs),
            empty_directories=['empty',*empty] if fixture is None else list(empty),exact_tree=True,
            snapshot_exclusion='Exclude random header path, login and dynamic footer; preserve live file/tree/pager body')
        if fixture:case['fixture']=fixture
        return case
    cases=[primary]
    cases.append(add('normal-directory','normal','Create and enter nested Unicode directories, including a truly empty new leaf',
        [*console('mkdir created caf\u00e9/sub'),expect('created caf\u00e9'),
         *select('created','created caf\u00e9'),text('l'),expect('/fixture/created caf\u00e9/sub'),
         text('l'),expect('0/0')],dirs=['created caf\u00e9','created caf\u00e9/sub'],empty=['created caf\u00e9/sub']))
    cases.append(add('normal-rename','normal','Rename a noninitial file and verify original-path absence and exact bytes',
        [*select('bravo','bravo.txt','RANGER BRAVO ORIGINAL TOKEN'),*console('rename renamed caf\u00e9.txt'),
         expect('/fixture/renamed caf\u00e9.txt')],changed={'renamed caf\u00e9.txt':files['bravo.txt']},missing=['bravo.txt']))
    cases.append(add('normal-copy','normal','Copy protected multi-line bytes into a nested directory and return to the parent',
        [*select('alpha','alpha.txt','RANGER ALPHA ORIGINAL TOKEN'),*console('copy'),*into_nested(),
         *console('paste'),expect(row('alpha.txt')),*select('alpha','nested/alpha.txt','RANGER ALPHA ORIGINAL TOKEN'),
         text('h'),expect(row('protected.txt'))],changed={'nested/alpha.txt':files['alpha.txt']}))
    cases.append(add('normal-move','normal','Move a noninitial file, inspect its bytes and verify the old path disappears',
        [*select('bravo','bravo.txt','RANGER BRAVO ORIGINAL TOKEN'),*console('cut'),*into_nested(),
         *console('paste'),expect(row('bravo.txt')),*select('bravo','nested/bravo.txt','RANGER BRAVO ORIGINAL TOKEN'),
         text('h'),expect(row('protected.txt'))],changed={'nested/bravo.txt':files['bravo.txt']},missing=['bravo.txt']))
    cases.append(add('normal-nested-navigation','normal','Navigate and return between distinct directories with actual selected-file content',
        [*into_nested(),text('h'),expect(row('protected.txt')),*select('occupied','occupied'),
         text('l'),expect('/fixture/occupied/keep.txt'),expect('RANGER OCCUPIED DIRECTORY TOKEN')]))
    pager=[*select('long','long.txt','line 000:'),text('i'),absent('alpha.txt'),expect('line 027:'),key('PageDown'),
           expect('line 055:'),absent('line 000:')]
    cases.append(add('normal-long-pager','normal','Open the built-in text pager, page through Unicode content, return home and close it',
        [*pager,key('Home'),expect('line 000:'),key('Escape'),expect(row('protected.txt'))],position=len(pager)))
    cases.append(add('edge-empty-directory','edge','Enter a genuinely empty directory and quit without manufacturing files',
        [text('l'),expect('0/0')]))
    cases.append(add('edge-empty-filter-recovery','edge','Apply a no-match filter stack, clear it, then select a useful existing file',
        [*console('filter_stack add name ^NO_SUCH_ENTRY$'),expect('0/0'),
         *console('filter_stack clear'),expect(row('alpha.txt')),*select('bravo','bravo.txt','RANGER BRAVO ORIGINAL TOKEN')]))
    for suffix,command in [('create','touch not-created caf\u00e9.txt'),('rename','rename cancelled caf\u00e9.txt')]:
        steps=select('bravo','bravo.txt','RANGER BRAVO ORIGINAL TOKEN') if suffix=='rename' else []
        steps += [expect('All'),text(':'),absent('All'),expect(':'),text(command),expect(':'+command),
                  key('Escape'),absent(':'+command),expect('All')]
        cases.append(add('edge-cancel-'+suffix,'edge','Cancel a populated '+suffix+' command without altering any fixture entry',steps))
    cases.append(add('edge-occupied-rename','edge','Refuse a rename onto a protected existing file while preserving both originals',
        [*select('bravo','bravo.txt','RANGER BRAVO ORIGINAL TOKEN'),*console('rename protected.txt',False),
         expect("Can't rename: file already exists!")]))
    confirmation='Confirm deletion of 1 items: protected.txt (y/N)'
    cases.append(add('edge-delete-cancelled','edge','Decline an actual permanent-deletion confirmation and preserve every file',
        [*select('protected','protected.txt','RANGER PROTECTED NEIGHBOR TOKEN'),*console('delete',False),
         expect(confirmation),text('n'),absent(confirmation),expect('All')]))
    cases.append(add('edge-key-prefix-cancel','edge','Cancel an incomplete ordinary yank key chain, then perform useful search navigation',
        [text('y'),expect('copy mode=remove'),key('Escape'),absent('copy mode=remove'),
         *select('protected','protected.txt','RANGER PROTECTED NEIGHBOR TOKEN')]))
    narrow=[*select('long','long.txt','line 000:'),text('i'),absent('alpha.txt'),expect('line 027:'),
            {'resize':{'width':80,'height':24}},{'wait_for_redraw':True},absent('line 027:'),expect('line 021:'),
            key('PageDown'),expect('line 043:'),absent('line 000:')]
    cases.append(add('edge-resize-pager','edge','Resize a live built-in pager, observe redraw and scroll before restoring the ordinary view',
        [*narrow,{'resize':{'width':100,'height':30}},{'wait_for_redraw':True},expect('line 049:'),
         key('Home'),expect('line 000:'),key('Escape'),expect(row('protected.txt'))],position=len(narrow),rows=(2,22)))
    bulk={'file %03d.txt'%i:'RANGER BULK %03d TOKEN\n'%i for i in range(200)}
    for name,value in bulk.items():
        target=package/'fixtures-large'/name;target.parent.mkdir(exist_ok=True)
        if target.exists():raise RuntimeError('Refuse replacing large-tree fixture')
        target.write_bytes(value.encode('utf-8'))
    last=[expect('RANGER BULK 000 TOKEN'),expect('1/200  Top'),
          text('G'),expect('/fixture/file 199.txt'),expect('RANGER BULK 199 TOKEN')]
    cases.append(add('edge-large-directory','edge','Navigate to the last entry of a 200-file tree, inspect it and return home',
        [*last,key('Home'),expect('/fixture/file 000.txt')],fixture='fixtures-large',expected=bulk,position=len(last)))
    config['cases']=cases
    path.write_bytes((json.dumps(config,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
    print('Declared',len(cases),'intentions; actual recording and qualification still required')


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group()
    group.add_argument('--promote',action='store_true');group.add_argument('--extend',action='store_true')
    args=parser.parse_args()
    extend() if args.extend else promote() if args.promote else main()
