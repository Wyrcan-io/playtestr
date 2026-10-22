"""Declare useful independent jrnl outcomes after its public first-use route."""
import base64
import copy
import json
from pathlib import Path

from next20_check import DOC,RAW,ROOT
from readiness_evidence import immutable_json,sha256

ALPHA='[2020-01-01 09:00] alpha ready.\nFirst body.\n'
BETA='[2020-01-02 10:15] beta retained.\nSecond body.\n'
BASE=ALPHA+'\n'+BETA
NO_EDITS='No edits to save, because nothing was changed'


def expect(text):return dict(expect=text)
def key(name):return dict(key=name)
def text(value):return dict(text=value)
def answer(value):return [text(value),key('Enter')]


def main():
    package=DOC/'jrnl'
    if not (package/'first-use.json').exists():raise ValueError('first useful route must precede handwritten cases')
    declaration=package/'scenarios.json'
    if declaration.exists():raise ValueError('case declaration already exists; preserve and revise explicitly')
    template=json.loads((package/'normal-delete.json').read_text())
    config=(package/'fixture/config.yaml').read_bytes()
    cases=[]
    def add(cid,filename,task,risk,args,steps,expected=BASE,initial=BASE,fixture_extra=None,
            states_extra=None,exit_code=0,width=80,height=24,combined=None,config_name='config.yaml',journal='journal.txt',
            config_override=None,directory_journal=False,directory_config=False):
        fixture='fixtures/'+cid.lower()+('-config-dir' if directory_config else '')
        folder=package/fixture;folder.mkdir(parents=True)
        cfg=config if config_override is None else config_override
        if directory_config:
            (folder/config_name).mkdir();(folder/config_name/'owned-marker.txt').write_bytes(b'synthetic directory at config path\n')
        else:
            with (folder/config_name).open('xb') as stream:stream.write(cfg)
        if directory_journal:
            (folder/journal).mkdir();(folder/journal/'owned-marker.txt').write_bytes(b'synthetic wrong-type directory\n')
        else:
            with (folder/journal).open('xb') as stream:stream.write(initial.encode('utf-8'))
        for name,payload in (fixture_extra or {}).items():
            with (folder/name).open('xb') as stream:stream.write(payload.encode('utf-8'))
        spec=copy.deepcopy(template)
        spec.update(name=task,width=width,height=height,timeout_ms=10000)
        spec['workspace']['fixture']=fixture
        spec['command']=template['command'][:4]+['--config-file',config_name]+args
        spec['steps']=steps+[dict(exit=exit_code)]
        if directory_journal:
            spec['steps'].append(dict(state=dict(path=journal,kind='directory')))
        else:
            spec['steps'].append(dict(state=dict(path=journal,kind='file',bytes_base64=base64.b64encode(expected.encode('utf-8')).decode())))
        for name,payload in (states_extra or {}).items():
            spec['steps'].append(dict(state=dict(path=name,kind='file',bytes_base64=base64.b64encode(payload.encode('utf-8')).decode())))
        if directory_config:spec['steps'].append(dict(state=dict(path=config_name,kind='directory')))
        spec['steps'].append(dict(state=dict(path='.',kind='entries',entries=sorted([config_name,journal,*list((fixture_extra or {}).keys())]))))
        immutable_json(package/filename,spec)
        cases.append(dict(id=cid,kind='normal' if cid.startswith('N') else 'edge',spec=filename,task=task,risk=risk,
            initial_fixture=fixture,expected_exit=exit_code,hosts=['linux','windows'],width=width,height=height,
            combined_risks=combined or [],oracle='Independently declared exact synthetic journal bytes, positive target result and same-execution state before cleanup',
            spec_sha256=sha256(package/filename)))
    cases.append(dict(id='N01',kind='normal',spec='normal-delete.json',task='Delete only alpha and preserve beta',
        risk='Selective destructive action with exact retained data',initial_fixture='fixture',expected_exit=0,
        hosts=['linux','windows'],width=80,height=24,combined_risks=[],
        oracle='Recorder output independently checked against manually reviewed beta bytes',spec_sha256=sha256(package/'normal-delete.json')))
    add('N02','normal-keep.json','Decline deletion and preserve all original bytes','Explicit negative confirmation',
        ['-contains','alpha','--delete'],[expect('alpha ready.'),*answer('n'),expect(NO_EDITS)])
    add('N03','normal-selective.json','Delete alpha but keep beta in a multi-entry session','Distinct prompt-to-entry association',
        ['--delete'],[expect('alpha ready.'),*answer('y'),expect('beta retained.'),*answer('n'),expect('1 entry deleted')],expected=BETA)
    retimed='[2030-02-03 04:05] alpha ready.\nFirst body.\n'
    add('N04','normal-retime.json','Retime alpha and reorder without changing beta','Timestamp change and persisted ordering',
        ['-contains','alpha','--change-time','2030-02-03 04:05'],[expect('Change time for'),*answer('y'),expect('1 entry modified')],expected=BETA+'\n'+retimed)
    add('N05','normal-keep-time.json','Decline timestamp update without changing journal','Negative timestamp confirmation',
        ['-contains','alpha','--change-time','2030-02-03 04:05'],[expect('Change time for'),*answer('n'),expect(NO_EDITS)])
    add('N06','normal-compose.json','Compose a dated new entry interactively and persist it','Multiline stdin and native EOF',[],
        [expect('Writing Entry'),text('2020-01-03 11:20: gamma saved. Third body.'),key('Enter'),key('CtrlZ'),key('Enter'),expect('Entry added to default journal')],
        expected=BASE+'\n[2020-01-03 11:20] gamma saved.\nThird body.\n')
    work='[2020-02-01 09:00] work important.\nOwned work journal.\n'
    workconfig=config.replace(b'editor:',b'  work:\n    journal: work.txt\neditor:')
    add('N07','normal-named-journal.json','Delete from named work journal while preserving default','Journal namespace isolation',
        ['work','--delete'],[expect('work important.'),*answer('y'),expect('1 entry deleted')],
        fixture_extra={'work.txt':work},states_extra={'work.txt':''},config_override=workconfig)
    starred=ALPHA.replace('alpha ready.','alpha ready. *')+'\n'+BETA
    add('N08','normal-starred.json','Delete starred entry and preserve unstarred data','Starred semantic subset',
        ['-starred','--delete'],[expect('alpha ready.'),*answer('y'),expect('1 entry deleted')],initial=starred,expected=BETA)
    add('E01','edge-empty.json','Handle empty journal without fabricating a deletion','Zero-entry boundary',
        ['--delete'],[expect('no entries found')],initial='',expected='')
    add('E02','edge-no-match.json','Preserve nonempty journal when date search finds nothing','No-match destructive search',
        ['-on','2021-01-01','--delete'],[expect('no entries found')])
    add('E03','edge-invalid-confirm.json','Reject non-yes confirmation through safe default','Invalid destructive answer defaults to no',
        ['-contains','alpha','--delete'],[expect('alpha ready.'),*answer('perhaps'),expect(NO_EDITS)])
    add('E04','edge-interrupted-multi.json','Cancel after choosing one deletion before final confirmation','Partial destructive operation interrupted',
        ['--delete'],[expect('alpha ready.'),*answer('y'),expect('beta retained.'),key('CtrlC'),expect('Aborted by user')],
        exit_code=1,combined=['partial destructive choice','interruption','original state preservation'])
    duplicate='[2020-01-01 09:00] same message.\nFirst body.\n\n[2020-01-02 10:15] same message.\nSecond body.\n'
    add('E05','edge-duplicate-labels.json','Delete dated duplicate title without deleting the other entry','Ambiguous labels separated by date and body',
        ['-on','2020-01-02','--delete'],[expect('2020-01-02 10:15'),*answer('y'),expect('1 entry deleted')],
        initial=duplicate,expected='[2020-01-01 09:00] same message.\nFirst body.\n',combined=['duplicate labels','date filtering','exact retained body'])
    unicode=ALPHA.replace('alpha ready.','café 雪 ready.')+'\n'+BETA
    unicodecfg=config.replace(b'journal.txt','journal 雪.txt'.encode())
    add('E06','edge-unicode-path.json','Delete Unicode entry through spaced Unicode configuration and journal paths','Unicode input/data/path portability',
        ['-contains','café','--delete'],[expect('café 雪 ready.'),*answer('y'),expect('1 entry deleted')],
        initial=unicode,expected=BETA,config_name='config café.yaml',journal='journal 雪.txt',config_override=unicodecfg,
        combined=['Unicode title','spaced Unicode config path','exact Unicode state path'])
    add('E07','edge-resize-confirm.json','Resize a small confirmation viewport then delete the intended entry','Quiet resize while awaiting destructive input',
        ['-contains','alpha','--delete'],[expect('Delete entry'),dict(resize=dict(width=100,height=30)),*answer('y'),expect('1 entry deleted')],
        expected=BETA,width=40,height=12,combined=['small viewport','resize during confirmation','exact selected deletion'])
    long=ALPHA.replace('alpha ready.','alpha '+('long wrapped title '*14).strip()+'.')+'\n'+BETA
    add('E08','edge-wrapped-correction.json','Correct a typed no answer before confirming a wrapped entry','Wrapped prompt and actual line editing',
        ['-contains','alpha','--delete'],[expect('Delete entry'),text('n'),key('Backspace'),*answer('y'),expect('1 entry deleted')],
        initial=long,expected=BETA,width=50,height=16,combined=['long wrapped title','backspace correction','correct persisted selection'])
    tagged=ALPHA.replace('alpha ready.','alpha @work ready.')+'\n'+BETA.replace('beta retained.','beta @work @todo retained.')
    add('E09','edge-tag-intersection.json','Delete only entry matching both tags and keep partial match','AND versus OR false-positive risk',
        ['@work','@todo','-and','--delete'],[expect('beta @work @todo retained.'),*answer('y'),expect('1 entry deleted')],
        initial=tagged,expected=ALPHA.replace('alpha ready.','alpha @work ready.'),combined=['overlapping tags','strict intersection','unselected data preservation'])
    add('E10','edge-malformed-config.json','Refuse malformed configuration without damaging existing journal','Owned invalid configuration',
        ['--delete'],[expect('Error')],config_override=b'journals: [unterminated\n',exit_code=1)
    add('E11','edge-wrong-type.json','Refuse a directory supplied as the configuration file and preserve journal','Directory where configuration file is required',
        ['--delete'],[expect('Error')],exit_code=1,directory_config=True)
    add('E12','edge-no-editor.json','Refuse selected editing without an editor and preserve bytes','Unavailable editor configuration',
        ['-contains','alpha','--edit'],[expect('There is no editor configured')],exit_code=1)
    immutable_json(declaration,dict(schema_version=1,project='jrnl',source_pin='90de4948d79a4fca8c7238dd2487b599f458c903',
        status='development-declaration-not-final-freeze',normal=8,edge=12,cases=cases,
        native_profiles={'windows':'Copied venv Scripts/python.exe; CtrlZ then Enter for interactive EOF',
            'linux':'Copied venv bin/python; CtrlD for interactive EOF. Exact journal bytes remain LF on both.'},
        limits=dict(scenario_seconds=120,step_seconds=10,workspace_bytes=64*1024**2,output_bytes=2000000),
        variation_schedule=['ordinary-cold-1','ordinary-warm-1','ordinary-cold-2','ordinary-warm-2',
            'viewport-small','spaced-unicode-path','ordinary-input','segmented-printable-input',
            'bounded-contention-1','bounded-contention-2','highest-risk-boundary-1','highest-risk-boundary-2'],
        all_scenarios_qualified=False,real_faults_selected_after_freeze=0))
    print('Declared eight normal/twelve edge jrnl tasks, six combined-risk cases. Source faults and final qualification remain unexecuted.')


if __name__=='__main__':main()
