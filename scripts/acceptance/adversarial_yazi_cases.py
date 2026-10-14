"""Declare synthetic Yazi intentions; recording must establish actual contracts."""
import argparse
import copy
import json
from adversarial_process import DOC


def main():
    package=DOC/'yazi'
    fixture=package/'fixtures'
    files={
        'alpha.txt':'ALPHA ORIGINAL TOKEN\nProtected alpha second line.\n',
        'bravo.txt':'BRAVO ORIGINAL TOKEN\n',
        'protected.txt':'PROTECTED NEIGHBOR TOKEN\n',
        'nested/notes café.txt':'NESTED UNICODE NOTES TOKEN\nOther nested bytes.\n',
        'occupied/keep.txt':'OCCUPIED DIRECTORY TOKEN\n',
        'long.txt':''.join('line %02d: long café 雪 TOKEN\n'%i for i in range(80)),
    }
    for name,value in files.items():
        path=fixture/name
        path.parent.mkdir(parents=True,exist_ok=True)
        data=value.encode('utf-8')
        if path.exists() and path.read_bytes()!=data:
            raise RuntimeError('Refuse changing synthetic reviewed input: '+name)
        if not path.exists():path.write_bytes(data)
    (fixture/'empty').mkdir(exist_ok=True)
    scenarios=package/'scenarios.json'
    if scenarios.exists():raise RuntimeError('Refuse replacing declared Yazi intentions')
    def add(name,kind,purpose,steps,changed=None):
        expected=dict(files);expected.update(changed or {})
        return dict(name=name,kind=kind,purpose=purpose,command=['yazi','.'],
                    steps=[*steps,{'text':'q'},{'exit':0}],snapshot_after_step=len(steps),
                    snapshot_rows=[2,28],timeout_ms=10000,expected_files=expected,
                    absent_paths=[],snapshot_exclusion='Exclude dynamic absolute header path and footer metadata; preserve live selected file/tree/preview content.')
    cases=[
        add('explore-startup','exploration','Observe the actual ordinary startup and quit; no scenario credit',
            [{'expect':'alpha.txt'}]),
        add('normal-project','normal','Create a real spaced Unicode file and preserve all neighboring bytes',
            [{'expect':'alpha.txt'},{'text':'a'},{'expect':'Create'},
             {'text':'created café.txt'},{'expect':'created café.txt'},{'key':'Enter'},
             {'expect_not':'Create'},{'expect':'󰈙 created café.txt'}],
            {'created café.txt':''}),
    ]
    scenarios.write_text(json.dumps(dict(project='yazi',fixture='fixtures',
        environment={'TERM':'screen-256color'},cases=cases),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (package/'fixture-directories.json').write_text(json.dumps(['fixtures/empty'],indent=2)+'\n',encoding='utf-8')
    print('Declared exploratory startup and first real creation intention; qualification remains pending')


def extend():
    package=DOC/'yazi';path=package/'scenarios.json'
    config=json.loads(path.read_text(encoding='utf-8'))
    if any(c['name']=='normal-rename' for c in config['cases']):
        raise RuntimeError('Refuse replacing extended intentions')
    primary=next(c for c in config['cases'] if c['name']=='normal-project')
    files={k:v for k,v in primary['expected_files'].items() if k!='created café.txt'}
    text=lambda value:{'text':value}
    key=lambda value:{'key':value}
    expect=lambda value:{'expect':value}
    absent=lambda value:{'expect_not':value}
    def select(query,name,directory=False):
        return [text('/'),expect('Find next:'),text(query),key('Enter'),
                absent('Find next:'),expect('(find: '+query+')'),
                expect(''+('' if directory else '󰈙')+' '+name),key('Escape'),
                absent('(find: '+query+')')]
    def add(name,kind,purpose,steps,*,changed=None,missing=None,dirs=None):
        expected=dict(files);expected.update(changed or {})
        for name_missing in missing or []:expected.pop(name_missing,None)
        return dict(name=name,kind=kind,purpose=purpose,command=['yazi','.'],
            steps=[expect('alpha.txt'),*steps,text('q'),{'exit':0}],
            snapshot_after_step=1+len(steps),snapshot_rows=[2,28],timeout_ms=10000,
            expected_files=expected,absent_paths=missing or [],expected_directories=['empty',*(dirs or [])],
            snapshot_exclusion=primary['snapshot_exclusion'])
    edit=[key('CtrlU'),key('CtrlK')]
    protected=[*select('protected','protected.txt'),expect('PROTECTED NEIGHBOR TOKEN')]
    cases=[primary]
    cases.append(add('normal-directory','normal','Create nested Unicode directories and verify actual directory types',
        [text('a'),expect('Create:'),text('created dir café/sub/'),key('Enter'),absent('Create:'),
         expect('/fixture/created dir café'),expect(' sub'),text('l'),
         expect('/fixture/created dir café/sub'),expect('No items')],dirs=['created dir café','created dir café/sub']))
    cases.append(add('normal-rename','normal','Rename a noninitial file and verify the old path disappears',
        [*select('bravo','bravo.txt'),text('r'),expect('Rename:'),*edit,text('renamed café.txt'),
         key('Enter'),absent('Rename:'),expect('󰈙 renamed café.txt'),expect('BRAVO ORIGINAL TOKEN')],
        changed={'renamed café.txt':files['bravo.txt']},missing=['bravo.txt']))
    def into_nested():
        return [*select('nested','nested',True),text('l'),expect('/fixture/nested'),
                expect('󰈙 notes café.txt')]
    cases.append(add('normal-copy','normal','Copy protected bytes into a nested directory and return to the parent',
        [*select('alpha','alpha.txt'),text('y'),*into_nested(),text('p'),
         expect('󰈙 alpha.txt'),expect('ALPHA ORIGINAL TOKEN'),text('h'),expect(' fixture')],
        changed={'nested/alpha.txt':files['alpha.txt']}))
    cases.append(add('normal-move','normal','Move a noninitial file and verify destination bytes and original absence',
        [*select('bravo','bravo.txt'),text('x'),*into_nested(),text('p'),
         expect('󰈙 bravo.txt'),expect('BRAVO ORIGINAL TOKEN'),text('h'),expect(' fixture')],
        changed={'nested/bravo.txt':files['bravo.txt']},missing=['bravo.txt']))
    cases.append(add('normal-nested-navigation','normal','Navigate two distinct directories and inspect their actual text files',
        [*into_nested(),expect('NESTED UNICODE NOTES TOKEN'),text('h'),expect(' fixture'),
         *select('occupied','occupied',True),text('l'),expect('/fixture/occupied'),expect('OCCUPIED DIRECTORY TOKEN')]))
    cases.append(add('normal-long-preview','normal','Scroll a long Unicode text preview using ordinary preview keys',
        [*select('long','long.txt'),expect('line 00:'),text('JJ'),expect('line 40:'),absent('line 00:')]))
    cases.append(add('edge-empty-directory','edge','Enter a truly empty directory and exit naturally',
        [*select('empty','empty',True),text('l'),expect('/fixture/empty'),expect('No items')]))
    cases.append(add('edge-no-match-recovery','edge','Recover from a genuinely empty filter and perform useful selection',
        [*protected,text('f'),expect('Filter:'),text('ABSENTNEVERTOKEN'),key('Enter'),absent('Filter:'),
         expect('No filter results'),expect('(filter: ABSENTNEVERTOKEN)'),key('Escape'),
         absent('(filter: ABSENTNEVERTOKEN)'),*select('bravo','bravo.txt'),expect('BRAVO ORIGINAL TOKEN')]))
    cases.append(add('edge-cancel-create','edge','Cancel a partially entered creation without creating a destination',
        [text('a'),expect('Create:'),text('CANCEL NEVER café.txt'),expect('CANCEL NEVER café.txt'),
         key('CtrlC'),absent('Create:'),*protected],missing=['CANCEL NEVER café.txt']))
    cases.append(add('edge-cancel-rename','edge','Cancel edited rename input and preserve the original exact bytes',
        [*select('bravo','bravo.txt'),text('r'),expect('Rename:'),*edit,text('CANCEL RENAME café.txt'),
         expect('CANCEL RENAME café.txt'),key('CtrlC'),absent('Rename:'),*protected],missing=['CANCEL RENAME café.txt']))
    cases.append(add('edge-overwrite-declined','edge','Decline overwriting an occupied file and preserve its bytes',
        [text('a'),expect('Create:'),text('alpha.txt'),key('Enter'),expect('Overwrite file?'),
         text('n'),absent('Overwrite file?'),*protected]))
    cases.append(add('edge-delete-cancelled','edge','Cancel permanent deletion of a synthetic selected file',
        [*select('bravo','bravo.txt'),text('D'),expect('Permanently delete 1 selected file?'),
         text('n'),absent('Permanently delete 1 selected file?'),*protected]))
    cases.append(add('edge-resize-preview','edge','Resize with observed redraw, scroll new content and return to the beginning',
        [*select('long','long.txt'),expect('line 00:'),{'resize':{'width':80,'height':24}},
         {'wait_for_redraw':True},text('JJ'),expect('line 30:'),expect('line 40:'),absent('line 00:'),
         {'resize':{'width':100,'height':30}},{'wait_for_redraw':True},text('KK'),
         expect('line 00:'),absent('line 40:')]))
    config['cases']=cases
    path.write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Declared fourteen useful intentions; actual recordings and native qualification remain required')


def windows_contracts():
    package=DOC/'yazi';path=package/'scenarios.json'
    config=json.loads(path.read_text(encoding='utf-8'))
    for case in config['cases']:
        if not any('/fixture/' in step.get('expect','') for step in case['steps']):continue
        if case.get('baseline_suffix_by_host',{}).get('Windows'):
            raise RuntimeError('Refuse replacing a declared Windows contract')
        name=case['name'];suffix='-windows'
        steps=copy.deepcopy(case['steps'])
        for step in steps:
            if '/fixture/' in step.get('expect',''):step['expect']=step['expect'].replace('/','\\')
        spec=json.loads((package/(name+'.json')).read_text(encoding='utf-8'))
        for step in spec['steps']:
            if '/fixture/' in step.get('expect',''):step['expect']=step['expect'].replace('/','\\')
            if 'snapshot' in step:step['snapshot']=name+suffix+'.rows.json'
        output=package/(name+suffix+'.json');baseline=package/'snapshots'/(name+suffix+'.rows.json')
        if output.exists() or baseline.exists():raise RuntimeError('Refuse existing projected Windows contract')
        output.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        baseline.write_bytes((package/'snapshots'/(name+'.rows.json')).read_bytes())
        case['steps_by_host']={'Windows':steps}
        case['baseline_suffix_by_host']={'Windows':suffix}
    path.write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Projected Windows path contracts from pinned native path display; actual Windows qualification remains pending')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--extend',action='store_true')
    parser.add_argument('--windows-contracts',action='store_true')
    args=parser.parse_args()
    if args.extend and args.windows_contracts:parser.error('Select one construction stage')
    windows_contracts() if args.windows_contracts else extend() if args.extend else main()
