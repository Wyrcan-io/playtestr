"""Declare twenty complete peco workflows after the positive public recorder route."""
import base64
import copy
import json

from next20_check import DOC,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def expect(text):return dict(expect=text)
def key(text):return dict(key=text)
def absent(text):return dict(expect_not=text)


def main():
    package=DOC/'peco';target=RAW/'active/peco'
    if not (package/'first-use.json').is_file() or (package/'scenarios.json').exists():raise ValueError('positive public first route required; preserve existing cases')
    original=json.loads((package/'normal-selection.json').read_text());base_config=json.loads((package/'fixture/config.json').read_text());base_input=(package/'fixture/candidates.txt').read_bytes();sentinel=(package/'fixture/sentinel.txt').read_bytes();cases=[];tasks=[]
    def record(cid,name,task,risks,fixture,spec):
        cases.append(dict(id=cid,kind='normal' if cid.startswith('N') else 'edge',spec=name,task=task,risk='; '.join(risks),combined_risks=risks,startup_evidence='exact-first-exit' if cid=='E10' else 'terminal-output',
            initial_fixture=fixture,expected_exit=next(s['exit'] for s in spec['steps'] if 'exit' in s),hosts=['windows','linux'],width=spec['width'],height=spec['height'],spec_sha256=sha256(package/name),
            native_generated_text_paths=['selected.txt'],oracle='Independently declared actual selected stdout bytes,all preserved fixture bytes and complete workspace entries; positive real tcell checkpoints/exact target exit. Capture fixture never generates expected values.'))
        tasks.append(dict(id=cid,task=task,risks=risks))
    record('N01','normal-selection.json','Filter candidate lines and select beta draft',['Real filter/query rendering','Reviewed pre-exit snapshot','Exact selected stdout and unchanged input/config'], 'fixture',original)
    def add(cid,task,risks,steps,selected,*,data=base_input,args=(),configuration=None,yaml=None,width=100,height=24,exit_code=0):
        fixture='fixtures/'+cid.lower();folder=package/fixture;folder.mkdir(parents=True,exist_ok=False)
        config=copy.deepcopy(base_config);config.update(configuration or {})
        config_name='config.json' if yaml is None else 'config.yaml';config_body=(json.dumps(config,sort_keys=True,indent=2)+'\n').encode() if yaml is None else yaml
        expected={'candidates.txt':data,config_name:config_body,'sentinel.txt':sentinel,'selected.txt':selected}
        for name,body in expected.items():
            if name!='selected.txt':(folder/name).write_bytes(body)
        spec=copy.deepcopy(original);spec.update(name=task,width=width,height=height,timeout_ms=10000,run_timeout_ms=30000,startup_timeout_ms=2000,max_output_bytes=2_000_000)
        if cid=='E10':spec.update(startup_timeout_ms=0,timeout_ms=2000,run_timeout_ms=2000)
        spec['workspace']['fixture']=fixture
        spec['command']=original['command'][:6]+['--rcfile',config_name,*args,'candidates.txt']
        spec['steps']=copy.deepcopy(steps)+[dict(exit=exit_code)]
        for name,body in sorted(expected.items()):spec['steps'].append(dict(state=dict(path=name,kind='file',bytes_base64=base64.b64encode(body).decode())))
        spec['steps'].append(dict(state=dict(path='.',kind='entries',entries=sorted(expected))))
        filename=cid.lower()+'.json';immutable_json(package/filename,spec);record(cid,filename,task,risks,fixture,spec)
    ready=[expect('gamma release')]
    def query(text,mode='IgnoreCase',matches=1):return [dict(text=text),expect('Select> '+text),expect(mode+' ['+str(matches)+' (1/1)]')]
    add('N02','Select two candidates in input order',['Custom built-in key binding','Rendered saved/current selection markers','Stable multi-selection output order'],
        ready+[expect('> alpha notes'),key('Tab'),expect('* alpha notes'),expect('> beta draft'),key('Tab'),expect('* beta draft'),expect('> gamma release'),key('Enter')],b'alpha notes\nbeta draft\n',configuration={'SelectionPrefix':'>','Keymap':{'Tab':'peco.ToggleSelectionAndSelectNext'}})
    add('N03','Use initial CLI query and print it with the result',['CLI/config precedence','Initial filter completion','Query and selected output'],
        [expect('Select> gamma'),expect('IgnoreCase [1 (1/1)]'),expect('gamma release'),key('Enter')],b'gamma\ngamma release\n',args=['--query','gamma','--print-query'])
    mixed=b'alpha notes\nbeta draft\nBETA approval\ngamma release\n'
    add('N04','Select the case-sensitive uppercase candidate',['Case-sensitive filter','Unicode-safe input routing','Exact selected identity'],ready+query('BETA','CaseSensitive')+[key('Enter')],b'BETA approval\n',data=mixed,args=['--initial-filter','CaseSensitive'])
    add('N05','Filter by an anchored regular expression',['Built-in regular expression','Rendered filter readiness','Selected data integrity'],ready+query('^gamma','Regexp')+[key('Enter')],b'gamma release\n',args=['--initial-filter','Regexp'])
    add('N06','Rotate filter semantics without changing the query',['Filter rotation key','Two-to-one result transition','Case-sensitive exact result'],ready+query('BETA',matches=2)+[key('CtrlR'),expect('CaseSensitive [1 (1/1)]'),key('Enter')],b'BETA approval\n',data=mixed)
    yaml=b'Prompt: Select>\nQueryExecutionDelay: 0\nOnCancel: error\nInitialFilter: IgnoreCase\nFilters: [IgnoreCase, CaseSensitive, Regexp]\nSuppressStatusMsg: true\nLayout: bottom-up\n'
    add('N07','Load owned YAML configuration and select in bottom-up layout',['YAML configuration','Bottom-up viewport','Independent selected-file oracle'],ready+query('beta')+[key('Enter')],b'beta draft\n',yaml=yaml)
    add('N08','Find a candidate with a fuzzy subsequence',['Built-in fuzzy filter','Noncontiguous query semantics','Exact source-line output'],ready+query('gmr','Fuzzy')+[key('Enter')],b'gamma release\n',configuration={'Filters':['Fuzzy'],'InitialFilter':'Fuzzy'})
    unicode_input='alpha notes\ncaf\u00e9 \u96ea release\ngamma release\n'.encode()
    add('E01','Preserve Unicode selection through paste and resize',['BMP Unicode/accent/CJK','Pasted query','Resize and redraw','Exact UTF-8 bytes'],
        ready+query('caf\u00e9')+[dict(resize=dict(width=80,height=18)),dict(wait_for_redraw=True),expect('caf\u00e9 \u96ea release'),expect('Select> caf\u00e9'),key('Enter')],'caf\u00e9 \u96ea release\n'.encode(),data=unicode_input)
    add('E02','Correct an unmatched query with Backspace',['No-match transition','Native Backspace','Corrected filter result'],ready+[expect('beta draft'),dict(text='betax'),expect('Select> betax'),absent('beta draft'),key('Backspace')]+[expect('Select> beta'),expect('IgnoreCase [1 (1/1)]'),key('Enter')],b'beta draft\n')
    add('E03','Clear saved selections and finish on current candidate',['Built-in clear selection','Positive saved-marker disappearance','Current-line fallback'],ready+[expect('> alpha notes'),key('Tab'),expect('* alpha notes'),expect('> beta draft'),key('CtrlG'),absent('* alpha notes'),expect('> beta draft'),key('Enter')],b'beta draft\n',configuration={'SelectionPrefix':'>','Keymap':{'Tab':'peco.ToggleSelectionAndSelectNext'}})
    nul=b'choice\x00payload-A\nchoice\x00payload-B\nother\x00payload-C\n'
    add('E04','Distinguish duplicate displayed labels from NUL payload identity',['Duplicate visible labels','NUL display/output split','Initial cursor index'],[expect('other'),expect('> choice'),key('Enter')],b'payload-B\n',data=nul,args=['--null','--initial-index','1'],configuration={'SelectionPrefix':'>'})
    long_line=b'alpha-'+b'0123456789'*16+b'-tail\n'
    add('E05','Preserve a clipped long candidate in a small viewport',['Long clipped terminal line','Narrow viewport','Full untruncated output bytes'],[expect('alpha-0123456789'),key('Enter')],long_line,data=long_line+b'other\n',width=40,height=12)
    add('E06','Refuse an unknown configured filter',['Setup refusal','Useful error category','Empty selected output and preserved inputs'],[expect('unknown filter')],b'',args=['--filter','MissingFilter'],exit_code=1,width=120)
    add('E07','Reject malformed configuration before interaction',['Configuration parser failure','Useful error text','Preserved original invalid input'],[expect('failed to decode YAML')],b'',yaml=b'Prompt: [\n',exit_code=1,width=120)
    add('E08','Cancel with explicit error exit policy',['Escape key','Expected nonzero exit','No selected output'],ready+[key('Escape')],b'',exit_code=1)
    add('E09','Cancel successfully with explicit CLI policy',['Native CtrlC handling','CLI overrides error configuration','Exact zero exit and empty output'],ready+[key('CtrlC')],b'',args=['--on-cancel','success'])
    add('E10','Exit exactly one on an empty input file',['Empty source','Early declared nonzero completion','Positive exit/state evidence without quiet-readiness inference'],[],b'',data=b'',args=['--exit-0'],exit_code=1)
    add('E11','Recover from no matches and choose a valid candidate',['Empty result set','CtrlU query clear','Restored result readiness'],ready+[dict(text='nomatch'),expect('Select> nomatch'),absent('gamma release'),key('CtrlU'),absent('Select> nomatch'),expect('gamma release'),expect('IgnoreCase [3 (1/1)]')]+query('beta')+[key('Enter')],b'beta draft\n')
    many=b''.join(('item%02d\n'%i).encode() for i in range(30))
    add('E12','Navigate distant pages and retain selection across resize',['Pagination','Native Home/End keys','Resize/redraw','Current selection marker'],
        [expect('> item00'),key('End'),expect('> item29'),dict(resize=dict(width=65,height=12)),dict(wait_for_redraw=True),expect('> item29'),key('Home'),expect('> item00'),key('Enter')],b'item00\n',data=many,configuration={'SelectionPrefix':'>'},width=65,height=10)
    if len(cases)!=20 or sum(c['kind']=='normal' for c in cases)!=8:raise ValueError('wrong peco case matrix')
    immutable_json(package/'scenario-plan-v1.json',dict(schema_version=1,project='peco',normal=tasks[:8],edge=tasks[8:],faults_declared=False,scope='All exact expected file bytes and meaningful actions declared before first20-case development. No target writer computes expected output. Real-source faults declared after positive frozen development.'))
    immutable_json(package/'scenarios.json',dict(schema_version=1,project='peco',cases=cases,canonical_scenarios=20,normal=8,edge=12,project_admissions=0))
    compiled=json.loads((target/'build.json').read_text())['compiled_files']
    immutable_json(target/'launch-runtime-catalog.json',dict(schema_version=1,runtime_root=(target/'bin').relative_to(ROOT).as_posix(),files=compiled,executable=json.loads((target/'runtime.json').read_text())['native'],scope='Both actual target and stdout-capture executable bytes,verified before/after development.'))
    print('Declared20 peco workflows,8normal/12edge,all exact actual-output/preserved-file/entry oracles before development. No admission.')


if __name__=='__main__':main()
