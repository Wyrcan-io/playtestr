"""Prepare synthetic nnn intentions; actual public recording establishes contracts."""
import argparse
import copy
import json
from adversarial_process import DOC


def main():
    package=DOC/'nnn';path=package/'scenarios.json'
    if path.exists():raise RuntimeError('Refuse replacing declared nnn intentions')
    files={
        'alpha.txt':'NNN ALPHA ORIGINAL TOKEN\nProtected alpha second line.\n',
        'bravo.txt':'NNN BRAVO ORIGINAL TOKEN\n',
        'protected.txt':'NNN PROTECTED NEIGHBOR TOKEN\n',
        'caf\u00e9 \u96ea.txt':'NNN ROOT UNICODE TOKEN\n',
        'nested/notes caf\u00e9.txt':'NNN NESTED UNICODE TOKEN\nProtected nested bytes.\n',
        'occupied/keep.txt':'NNN OCCUPIED DIRECTORY TOKEN\n',
        '.hidden-synthetic.txt':'NNN SYNTHETIC HIDDEN TOKEN\n',
    }
    for relative,value in files.items():
        target=package/'fixtures'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():raise RuntimeError('Refuse replacing synthetic nnn input')
        target.write_bytes(value.encode('utf-8'))
    (package/'fixtures/empty').mkdir(exist_ok=True)
    case=dict(name='explore-startup',kind='exploration',
        purpose='Observe ordinary nnn startup and natural quit; no scenario credit',
        command=['nnn','-A','-C','.'],steps=[{'expect':'alpha.txt'},{'text':'q'},{'exit':0}],
        snapshot_after_step=1,snapshot_rows=[3,25],timeout_ms=10000,
        expected_files=files,expected_directories=['empty','nested','occupied'],
        empty_directories=['empty'],exact_tree=True)
    configuration=dict(project='nnn',fixture='fixtures',
        environment={'TERM':'screen-256color'},cases=[case])
    path.write_text(json.dumps(configuration,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (package/'fixture-directories.json').write_text('["fixtures/empty"]\n',encoding='utf-8')
    print('Prepared exploratory synthetic inputs only; no nnn scenario qualified')


def promote():
    package=DOC/'nnn';path=package/'scenarios.json'
    config=json.loads(path.read_text(encoding='utf-8'))
    if [case['name'] for case in config['cases']]!=['explore-startup']:
        raise RuntimeError('Promotion requires the single exploratory intention')
    archive=package/'exploratory-scenarios.json'
    if archive.exists():raise RuntimeError('Refuse replacing nnn exploration history')
    archive.write_bytes(path.read_bytes())
    case=copy.deepcopy(config['cases'][0])
    case.update(name='normal-project',kind='normal',
        purpose='Create an ordinary spaced Unicode file through the public nnn creation prompts',
        steps=[{'expect':'alpha.txt'},{'text':'n'},
               {'expect':"['f'ile]/'d'ir/'s'ym/'h'ard?"},{'text':'f'},
               {'expect':'[path/]name:'},{'text':'created caf\u00e9.txt'},
               {'expect':'[path/]name: created caf\u00e9.txt'},{'key':'Enter'},
               {'expect_not':'[path/]name:'},{'expect':'created caf\u00e9.txt'},
               {'text':'q'},{'exit':0}],snapshot_after_step=10,snapshot_rows=[3,25])
    case['expected_files']['created caf\u00e9.txt']=''
    config['cases']=[case]
    path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Declared actual-source creation intention; public recording and fresh replay remain required')


def extend():
    package=DOC/'nnn';path=package/'scenarios.json'
    config=json.loads(path.read_text(encoding='utf-8'))
    if [case['name'] for case in config['cases']]!=['normal-project']:
        raise RuntimeError('Extension requires the single reviewed primary intention')
    primary=config['cases'][0];files=dict(primary['expected_files']);files.pop('created caf\u00e9.txt')
    text=lambda value:{'text':value}
    expect=lambda value:{'expect':value}
    absent=lambda value:{'expect_not':value}
    key=lambda value:{'key':value}
    mode='str [/], ic [:]'
    def select(query,needle=None):
        other='bravo.txt' if query=='alpha' else 'alpha.txt'
        return [text('/'),expect(mode),text(query),expect('/'+query),absent(other),
                key('Escape'),absent(mode),expect(needle or query+'.txt*')]
    def restore_root(other):
        return [key('CtrlL'),expect(other)]
    def add(name,kind,purpose,steps,*,expected=None,absences=(),dirs=(),empty=(),position=None,
            fixture='fixtures',rows=(3,25),prefix=None):
        beginning=prefix if prefix is not None else [expect('alpha.txt'),expect('bravo.txt')]
        return dict(name=name,kind=kind,purpose=purpose,command=primary['command'],
            steps=[*beginning,*steps,text('q'),{'exit':0}],
            snapshot_after_step=len(beginning)+(len(steps) if position is None else position),
            snapshot_rows=list(rows),timeout_ms=10000,fixture=fixture,
            expected_files=files if expected is None else expected,
            expected_directories=['empty','nested','occupied',*dirs] if fixture=='fixtures' else list(dirs),
            empty_directories=['empty',*empty] if fixture=='fixtures' else list(empty),
            absent_paths=list(absences),exact_tree=True,
            snapshot_exclusion='Exclude random path/context header and dynamic status; preserve the complete intended list body')
    def create(kind,name):
        return [text('n'),expect("['f'ile]/'d'ir/'s'ym/'h'ard?"),text(kind),
                expect('[path/]name:'),text(name),expect('[path/]name: '+name),
                key('Enter'),absent('[path/]name:')]
    cases=[primary]
    first=[*create('d','created caf\u00e9/sub'),expect('created caf\u00e9/'),text('l'),
           expect('/fixture/created caf\u00e9'),expect('sub/')]
    cases.append(add('normal-directory','normal','Create a nested Unicode directory tree and verify its empty leaf',
        [*first,text('l'),expect('/fixture/created caf\u00e9/sub'),absent('sub/')],
        dirs=['created caf\u00e9','created caf\u00e9/sub'],empty=['created caf\u00e9/sub'],position=len(first)))
    renamed=dict(files);renamed['renamed caf\u00e9.txt']=renamed.pop('bravo.txt')
    cases.append(add('normal-rename','normal','Filter a noninitial file, rename it and preserve exact bytes',
        [*select('bravo'),key('CtrlR'),key('CtrlU'),text('renamed caf\u00e9.txt'),
         expect('renamed caf\u00e9.txt'),key('Enter'),absent('bravo.txt*'),
         expect('renamed caf\u00e9.txt*'),expect('alpha.txt')],expected=renamed,absences=['bravo.txt']))
    for action,source in [('copy','alpha'),('move','bravo')]:
        opposite='bravo.txt' if source=='alpha' else 'alpha.txt'
        start=[*select(source),text(' '),expect('+'+source+'.txt*'),*restore_root(opposite),
               *select('nested','nested/'),text('l'),expect('/fixture/nested'),expect('notes caf\u00e9.txt*'),
               text('p' if action=='copy' else 'v'),expect(source+'.txt*')]
        expected=dict(files);expected['nested/'+source+'.txt']=files[source+'.txt']
        if action=='move':expected.pop(source+'.txt')
        cases.append(add('normal-'+action,'normal','Select and '+action+' one file into a nested directory, then return',
            [*start,text('h'),absent('/fixture/nested'),expect('protected.txt*')],expected=expected,
            absences=[source+'.txt'] if action=='move' else [],position=len(start)))
    contexts=[*select('nested','nested/'),text('l'),expect('/fixture/nested'),expect('notes caf\u00e9.txt*'),
        text('2'),text('h'),absent('/fixture/nested'),expect('protected.txt*'),
        text('1'),expect('/fixture/nested'),expect('notes caf\u00e9.txt*'),
        text('2'),absent('/fixture/nested'),expect('protected.txt*')]
    cases.append(add('normal-context-navigation','normal','Maintain distinct nested/root context locations and recover after closing a context',
        [*contexts,text('q'),expect('/fixture/nested'),expect('notes caf\u00e9.txt*')],position=len(contexts)))
    multi=[*select('alpha'),text(' '),expect('+alpha.txt*'),*restore_root('bravo.txt'),
           *select('bravo'),text(' '),expect('+bravo.txt*'),*restore_root('alpha.txt'),
           *select('nested','nested/'),text('l'),expect('/fixture/nested'),expect('notes caf\u00e9.txt*'),
           text('p'),expect('alpha.txt*'),expect('bravo.txt*')]
    copied=dict(files,**{'nested/alpha.txt':files['alpha.txt'],'nested/bravo.txt':files['bravo.txt']})
    cases.append(add('normal-multi-selection-copy','normal','Accumulate two filtered selections and copy both with exact preserved source/destination bytes',multi,expected=copied))
    cases.append(add('edge-empty-directory','edge','Enter a genuinely empty directory while preserving all other fixture entries',
        [*select('empty','empty/'),text('l'),expect('/fixture/empty'),absent('empty/'),expect('0/0')],rows=(30,30)))
    recovery=[text('/'),expect(mode),text('nZe'),expect('/ne'),absent('alpha.txt'),
        key('CtrlL'),absent('/ne'),expect('alpha.txt'),key('Escape'),absent(mode),
        *select('nested','nested/'),text('l'),expect('/fixture/nested'),expect('notes caf\u00e9.txt*')]
    cases.append(add('edge-no-match-filter-recovery','edge','Reject an unmatched filter suffix, accept subsequent valid typing, then clear and navigate',recovery))
    cancelled='discarded caf\u00e9.txt'
    cases.append(add('edge-cancel-create','edge','Cancel a populated Unicode creation prompt without creating its path',
        [text('n'),expect("['f'ile]/'d'ir/'s'ym/'h'ard?"),text('f'),expect('[path/]name:'),
         text(cancelled),expect('[path/]name: '+cancelled),key('Escape'),
         absent('[path/]name: '+cancelled),expect('alpha.txt')],absences=[cancelled]))
    cases.append(add('edge-cancel-rename','edge','Cancel a changed rename prompt and preserve the original selected file',
        [*select('bravo'),key('CtrlR'),key('CtrlU'),text(cancelled),expect(cancelled),
         key('Escape'),absent(cancelled),expect('bravo.txt*')],absences=[cancelled]))
    cases.append(add('edge-occupied-rename','edge','Refuse overwriting a protected neighbor during rename and preserve both files',
        [*select('bravo'),key('CtrlR'),key('CtrlU'),text('protected.txt'),expect('protected.txt'),
         key('Enter'),expect('overwrite?'),text('n'),absent('overwrite?'),expect('bravo.txt*')]))
    cases.append(add('edge-occupied-create','edge','Refuse creation over an existing protected file and preserve its nonempty bytes',
        [*create('f','protected.txt'),expect('overwrite?'),text('n'),absent('overwrite?'),expect('protected.txt*')]))
    chooser="'c'urrent/'s'el?"
    cases.append(add('edge-delete-cancelled','edge','Cancel the destructive current/selection chooser before deletion and preserve selected bytes',
        [*select('protected'),text(' '),expect('+protected.txt*'),text('x'),expect(chooser),
         key('Escape'),absent(chooser),expect('protected.txt*')]))
    cases.append(add('edge-hidden-toggle','edge','Reveal a real hidden file, hide it again and preserve its exact contents',
        [text('.'),expect('.hidden-synthetic.txt*'),text('.'),absent('.hidden-synthetic.txt*'),expect('alpha.txt')]))
    bulk={'entry %03d.txt'%i:'NNN BULK %03d TOKEN\n'%i for i in range(200)}
    for name,value in bulk.items():
        target=package/'fixtures-large'/name;target.parent.mkdir(exist_ok=True)
        if target.exists():raise RuntimeError('Refuse replacing large nnn fixture')
        target.write_bytes(value.encode('utf-8'))
    end=[key('End'),expect('200/200'),expect('entry 199.txt*')]
    cases.append(add('edge-large-directory','edge','Navigate to the final entry of a 200-file directory and return home',
        [*end,key('Home'),expect('1/200'),expect('entry 000.txt*')],fixture='fixtures-large',
        expected=bulk,prefix=[expect('entry 000.txt*'),expect('1/200')],position=len(end),rows=(3,28)))
    narrow=[*end,{'resize':{'width':80,'height':24}},{'wait_for_redraw':True},
            key('Home'),expect('1/200'),expect('entry 000.txt*')]
    cases.append(add('edge-resize-recovery','edge','Resize a scrolled 200-file list, navigate home, restore geometry and return to the last entry',
        [*narrow,{'resize':{'width':100,'height':30}},{'wait_for_redraw':True},
         key('End'),expect('200/200'),expect('entry 199.txt*')],fixture='fixtures-large',expected=bulk,
        prefix=[expect('entry 000.txt*'),expect('1/200')],position=len(narrow),rows=(3,22)))
    config['cases']=cases
    path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Declared',len(cases),'nnn intentions; all require actual recording and fresh replay')


def faults():
    package=DOC/'nnn/faults';package.mkdir(exist_ok=True)
    destination=package/'definitions.json'
    if destination.exists():raise RuntimeError('Refuse replacing nnn source controls')
    copy_anchor='''if (sel != SEL_CPMVAS && spawn(utils[UTIL_SH_EXEC], g_buf, NULL, NULL, F_CLI | F_CHKRTN)) {
\t\tprintmsg(messages[MSG_FAILED]);
\t\treturn FALSE;
\t}

\t/* Clear selection */'''
    payload='''\tif (sel == SEL_CP && nselected == 1 && selbufpos) {
\t\tchar probe_copy_path[PATH_MAX];
\t\tmkpath(path, xbasename(pselbuf), probe_copy_path);
\t\tFILE *probe_copy = fopen(probe_copy_path, "r+");
\t\tif (probe_copy) {
\t\t\tchar probe_first_line[4096];
\t\t\tif (fgets(probe_first_line, sizeof(probe_first_line), probe_copy)) {
\t\t\t\tlong probe_second_line = ftell(probe_copy);
\t\t\t\tif (probe_second_line >= 0 && fgetc(probe_copy) != EOF &&
\t\t\t\t    fseek(probe_copy, probe_second_line, SEEK_SET) == 0)
\t\t\t\t\tfputc('X', probe_copy);
\t\t\t}
\t\t\tfclose(probe_copy);
\t\t}
\t}
'''
    definitions=[
        dict(name='new-file-becomes-directory',case='normal-project',file='src/nnn.c',
             old="ret = xmktree(tmp, r == 'f' ? FALSE : TRUE, TRUE);",
             new='ret = xmktree(tmp, TRUE, TRUE);'),
        dict(name='rename-silently-does-nothing',case='normal-rename',file='src/nnn.c',
             old='rename(pdents[cur].name, tmp)',new='rename(pdents[cur].name, pdents[cur].name)'),
        dict(name='unmatched-filter-character-retained',case='edge-no-match-filter-recovery',file='src/nnn.c',
             old='if (r == 0)\n\t\t\t\tunget_wch(KEY_BACKSPACE);',
             new='if (r < 0)\n\t\t\t\tunget_wch(KEY_BACKSPACE);'),
        dict(name='copy-corrupts-second-line',case='normal-copy',file='src/nnn.c',state_only=True,
             old=copy_anchor,new=copy_anchor.replace('\t/* Clear selection */',payload+'\n\t/* Clear selection */')),
    ]
    destination.write_text(json.dumps(definitions,indent=2)+'\n',encoding='utf-8')
    print('Prepared four C-source controls; unique anchors and actual execution still required')


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group()
    group.add_argument('--promote',action='store_true');group.add_argument('--extend',action='store_true')
    group.add_argument('--faults',action='store_true')
    args=parser.parse_args()
    if args.promote:promote()
    elif args.extend:extend()
    elif args.faults:faults()
    else:main()
