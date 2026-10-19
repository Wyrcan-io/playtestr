"""Audit each native suite and maintenance packet before combined admission."""
import argparse
import base64

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_rclone_verify_first_use import require,verify_native


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'],required=True);args=parser.parse_args()
    first=verify_native(args.run,publish=False,hosts=[args.host]);cell=first['cells'][0]
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'
    replica=docs/('replica-source-faults-'+args.host+'-'+args.run+'.json');faults=load(replica)
    require(faults['run']==args.run and faults['host']==args.host and faults['workflow_conclusion']=='success'
            and len(faults['faults'])==3 and not any(f['original_heldout'] for f in faults['faults']), 'missing complete replica audit')
    run=RAW/'native'/args.run;packet=run/('playtestr-'+('Linux' if args.host=='linux' else 'Windows'))
    target=packet/'rclone';profile=docs if args.host=='linux' else docs/'native-profiles/windows'
    frozen=load(profile/'reviewed-contract-freeze.json');package=target/'host-contracts'
    build=load(target/'retained-source/build.json');review=load(docs/'source-review.json')
    installed=load(packet/('private-install/provisional-v1/'+args.host+'-amd64/installation.json'))
    ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts()
    prefix='artifacts/runner-readiness-ten-project-pass/active/rclone/'
    def witness(identity,expected=0):
        event=events[identity];finished=event['finished'];reference=event['identified']['identity']
        require('launched' in event and event['started']['expected_exit']==expected and finished['category']=='passed'
                and finished['exit_code']==expected and not finished['cleanup_errors']
                and finished['harness_cleanup']=='harness_process_reaped','actual suite/maintenance outcome differs')
        manifest=packet_file(packet,reference['manifest'],2*1024**2)
        require(sha256(manifest)==reference['sha256'],'actual prelaunch identity changed')
        actual=load(manifest,maximum=2*1024**2);files=actual['files']
        require({n[len(prefix+'src/'):]:d for n,d in files.items() if n.startswith(prefix+'src/')}==review['reviewed_inputs']
                and actual['runtime_executables']['go']==build['compiler_sha256']
                and files[prefix+build['binary_relative_path']]==build['binary_sha256']
                and files[installed['binary']]==cell['runner_sha256'],'actual original target/compiler/runner differs')
        console=packet/event['started']['project']/identity/'console.log'
        require(sha256(console)==finished['console_sha256'],'actual command output changed')
        return files,console.read_text(encoding='utf-8-sig')
    def result_ok(value,status):
        require(value['status']==status and value['cleanup']['confirmed_exited'] and value['workspace']['cleaned'],
                'public result/cleanup differs')
        if status=='passed':require(all(s['status']=='passed' for s in value['steps']),'passing report contains incomplete steps')
        for step in value['steps']:
            if 'state' in step:
                require(step['state']['invocation_id']==value['invocation_id']
                        and step['state']['workspace_id']==value['workspace']['id'],'cross-execution state proof')
    suites=list((target/'suites').glob('*/results.json'));require(len(suites)==1,'missing or ambiguous full native suite')
    suite=load(suites[0]);require(suite['runner_version']=='v0.4.0-rc.4' and suite['summary']==
        dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'wrong native suite denominator/version')
    require({r['spec_path'].replace('\\','/').split('/')[-1] for r in suite['results']}==set(frozen['contracts'])
            and len({r['invocation_id'] for r in suite['results']})==20,'missing/duplicate actual native case')
    for result in suite['results']:result_ok(result,'passed')
    calls=[identity for identity,event in events.items() if event['started']['label']=='public-recorded-suite']
    require(len(calls)==1,'ambiguous actual full suite command');files,_=witness(calls[0])
    for name,digest in frozen['all_package_inputs'].items():
        require(sha256(packet_file(package,name,1024**2))==digest
                and files['artifacts/runner-readiness-ten-project-pass/rclone/host-contracts/'+name]==digest,
                'actual full native input differs')
    journeys=list(target.glob('maintenance*/journey.json'));require(len(journeys)==1,'missing complete public maintenance journey')
    journey=load(journeys[0]);root=journeys[0].parent
    labels=['intended-file-change','offline-diagnosis','selected-file-update','selected-file-replay',
        'intended-viewport-change','selected-screen-update','selected-screen-replay','fresh-suffix-rerecord',
        'suffix-ordinary-replay','relocated-N01','relocated-N02','relocated-rerecorded-suffix','generate-ordinary-workflow']
    require([a['label'] for a in journey['attempts']]==labels and len({a['id'] for a in journey['attempts']})==13,
            'wrong public maintenance sequence')
    require(journey['runner_sha256']==cell['runner_sha256'] and journey['provisional_archive_sha256']==cell['archive_sha256'],
            'maintenance private runner/archive differs')
    for attempt in journey['attempts']:
        _,output=witness(attempt['id'],int(attempt['label'].startswith('intended-')))
        if attempt['label'] in {'selected-file-update','fresh-suffix-rerecord'}:
            require('Exported ' in output and 'Recorder:' not in output,'recording contains failed requested controls')
    for label in ['intended-file-change','selected-file-replay','intended-viewport-change','selected-screen-update',
            'selected-screen-replay','suffix-ordinary-replay','relocated-N01','relocated-N02','relocated-rerecorded-suffix']:
        report=load(root/(label+'.json'));red=label.startswith('intended-')
        require(report['runner_version']=='v0.4.0-rc.4' and report['summary']==dict(total=1,passed=int(not red),
            failed=int(red),cancelled=0,not_run=0),'wrong maintenance denominator/version')
        result_ok(report['results'][0],'failed' if red else 'passed')
        if red:require(report['results'][0]['failure']['category']==
            ('state_assertion_failure' if label=='intended-file-change' else 'snapshot_mismatch'),'wrong intended-change diagnosis')
        if label=='intended-file-change':
            failed=next(s for s in report['results'][0]['steps'] if s['status']=='failed')
            require(failed.get('state',{}).get('path')=='sentinel.bin','intended file change failed on unrelated state')
    original=load(package/'N01.json');updated=load(root/'package/N01.json')
    index=next(i for i,s in enumerate(original['steps']) if s.get('state',{}).get('path')=='sentinel.bin')
    require(base64.b64decode(updated['steps'][index]['state']['bytes_base64'])==b'reviewed sentinel revision two\x00\r\n',
            'selected sentinel expectation differs')
    updated['steps'][index]=original['steps'][index];require(updated==original,'selected file update changed unrelated expectations')
    screen=load(root/'package/N02.json');old=load(package/'N02.json')
    require(screen['height']==29,'wrong reviewed viewport');screen['height']=old['height'];require(screen==old,'screen update changed unrelated expectations')
    name=next(s['snapshot'] for s in old['steps'] if 'snapshot' in s)
    require((root/'package/snapshots'/name).read_bytes()==b'Edit advanced config?\n'+(package/'snapshots'/name).read_bytes(),
            'updated snapshot differs from predeclared exact additional row')
    suffix=load(root/'package/rerecorded-suffix.json')
    files={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in suffix['steps'] if s.get('state',{}).get('kind')=='file'}
    newline=b'\r\n' if args.host=='windows' else b'\n'
    require(files=={'rclone.conf':newline.join([b'[corrected]',b'type = alias',b'remote = .',b'',b'']),
            'sentinel.bin':b'preserve\x00existing\r\n'} and all(s.get('text')!='wrong' and s.get('expect')!='wrong' for s in suffix['steps']),
            'discarded suffix or wrong saved bytes survived')
    entries=[s['state'] for s in suffix['steps'] if s.get('state',{}).get('kind')=='entries']
    require(len(entries)==1 and entries[0]['path']=='.' and len(entries[0]['entries'])==2
            and set(entries[0]['entries'])=={'rclone.conf','sentinel.bin'},'suffix complete entries differ')
    for name in ['N01.json','N02.json','rerecorded-suffix.json']:
        require(sha256(root/'package'/name)==sha256(root/'relocated \u96ea route'/name),'relocation changed exact contract')
    require(sha256(root/'package/N01.json')==journey['maintained_spec_sha256']==journey['relocated_spec_sha256']
            and sha256(root/'package/N02.json')==journey['screen_spec_sha256']
            and sha256(root/'generated-workflow.yml')==journey['generated_workflow_sha256'] and not journey['generated_workflow_execution'],
            'maintained/generated payload identity or execution claim differs')
    require((root/'diagnosis.html').is_file() and (root/'diagnosis.html').stat().st_size>100,
            'offline maintenance diagnosis was not rendered')
    receipt=dict(run=args.run,host=args.host,scenarios=20,runner_sha256=cell['runner_sha256'],
        provisional_archive_sha256=cell['archive_sha256'],full_suite_sha256=sha256(suites[0]),
        fault_verification_sha256=sha256(replica),maintenance_sha256=sha256(journeys[0]),
        source_cleanup_sha256=sha256(target/'retained-source/removed.json'),final_archive_credit=0)
    immutable_json(docs/('development-cell-'+args.host+'-'+args.run+'.json'),receipt)
    paths=[docs/('development-cell-'+h+'-'+args.run+'.json') for h in ['linux','windows']]
    if all(p.exists() for p in paths):
        immutable_json(docs/'native-development-verification.json',dict(cells=[load(p) for p in paths],
            runner_source=load(docs.parent/'provisional-candidate-freeze.json')['source_revision'],candidate_version='v0.4.0-rc.4',
            real_faults=3,original_heldout=dict(host='linux',run=load(docs/'original-source-faults.json')['run'],fault='F03'),
            original_fault_verification_sha256=sha256(docs/'original-source-faults.json'),final_archive_credit=0))
    print('Independently verified actual native Rclone suite, maintenance, relocation and cleanup:',args.host)


if __name__=='__main__':main()
