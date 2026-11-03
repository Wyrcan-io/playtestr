"""Account for every original peco report, failure frame and completed command."""
import argparse
import hashlib
import json

from next20_check import DOC, RAW
from next20_native_packet_reader import read_packet
from next20_peco_cell_readback import Evidence
from next20_target_cleanup import report_documents, invalid_spec_before_launch
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-retained',action='store_true');args=parser.parse_args()
    package=DOC/'peco';e=Evidence('windows');scope='artifacts/'+RAW.name+'/'
    if args.verify_retained:
        history=json.loads((package/'all-attempt-evidence.json').read_text())
        for row in history['local_reports']:
            require(e.sha(row['report'])==row['sha256'],'original retained report changed')
            if row.get('frame'):require(e.sha(row['frame'])==row['frame_sha256'],'original retained failure frame missing/changed')
        for row in history['commands']:
            require(e.sha(row['console'])==row['console_sha256'],'original command console changed')
        print('Every original local report/frame and completed command console still reads byte-exact after retention.')
        return
    disposition=json.loads((package/'development-disposition.json').read_text())
    prelaunch=json.loads((package/'maintenance-prelaunch-disposition-v1.json').read_text())
    invalid={r['sha256'] for r in disposition['actual_reports'] if not r['target_launched']}
    require(len(invalid)==2 and len(disposition['original_failed_frames'])==10,'original development rejection history incomplete')
    reports=[];failures=[];invocations=set();unlaunched=[]
    for path,document in report_documents(RAW/'peco'):
        require(len(document['results'])==1,'unexpected historical report cardinality')
        row=document['results'][0];report=path.relative_to(RAW).as_posix();digest=sha256(path)
        observed=dict(report=report,sha256=digest,status=row['status'],category=row.get('failure',{}).get('category'))
        if digest in invalid:
            require(invalid_spec_before_launch(document,row),'original parser refusal has unexpected launch state')
            observed.update(target_launched=False,cleanup_credit=0);unlaunched.append(observed)
        elif digest==prelaunch['original_report_sha256']:
            require(row['failure']['category']=='workspace_setup_failure' and not row.get('invocation_id') and not row['cleanup']['attempted'] and not row['workspace']['prepared'] and all(s['status']=='not_run' for s in row['steps']),'original sandbox refusal unexpectedly launched target')
            observed.update(target_launched=False,cleanup_credit=0);unlaunched.append(observed)
        else:
            require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'] and row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'historical target cleanup/identity incomplete or duplicated')
            invocations.add(row['invocation_id']);observed.update(target_launched=True,invocation=row['invocation_id'])
            if row['status']=='failed':
                frame=row['evidence']['screen_path'].replace('\\','/').removeprefix(scope);body=e.data(frame)
                # Quiet early-exit startup rejection has an honestly empty
                # captured frame. Existence and exact original bytes, not an
                # invented nonempty replacement, prove its preservation.
                observed.update(frame=frame,frame_bytes=len(body),frame_sha256=hashlib.sha256(body).hexdigest());failures.append(observed)
        reports.append(observed)
    actual={r['report']:r for r in reports}
    for original in disposition['actual_reports']:
        require(original['report'] in actual and actual[original['report']]['sha256']==original['sha256'],'original technical report omitted or replaced')
    for original in disposition['original_failed_frames']:
        row=actual[original['report']]
        require(row['frame']==original['frame'] and row['frame_sha256']==original['frame_sha256'] and row['frame_bytes']==original['frame_bytes'],'original failed technical screen omitted or reconstructed')
    require(len(unlaunched)==3 and {r['sha256'] for r in unlaunched}==invalid|{prelaunch['original_report_sha256']},'unreported prelaunch history')
    commands=[];pending=[]
    for path in sorted((RAW/'events').glob('*-started.json')):
        started=json.loads(path.read_text());eid=started['id']
        if started['project']!='peco' and 'peco' not in started['label'].lower():continue
        end=RAW/'events'/(eid+'-finished.json')
        if not end.exists():
            require(started['project']=='core' and started['label']=='peco-all-original-failure-history-readback','unclosed original peco command')
            pending.append(eid);continue
        finished=json.loads(end.read_text());console=RAW/started['project']/eid/'console.log'
        require(console.is_file() and sha256(console)==finished['console_sha256'],'original engineering command console changed')
        commands.append(dict(id=eid,project=started['project'],label=started['label'],phase=started['phase'],category=finished['category'],
            console=console.relative_to(RAW).as_posix(),console_sha256=sha256(console),started_sha256=sha256(path),finished_sha256=sha256(end)))
    rejected=['a8bc27c91d7c438e9ed786836e99a7a4','a4624027cbd4466c94a90e92c0a5c681','8c2dbff1df18468aa4f5d880d1419ee3',
        '28b16aca3ecd4a75acb34052114ef11e','f625430e8d874d49a9cdcf92e840cbcf','0c70f3b5aec94c119bde61b728b79a2d','be119cb96aa54187abd4ecb0799bee42']
    for eid in rejected:require(any(c['id']==eid and c['category']!='passed' for c in commands),'original failed setup/maintenance/acquisition command omitted')
    helper_files={p.relative_to(RAW).as_posix():sha256(p) for directory in [RAW/'peco/helper-source-revisions',RAW/'peco/module-fetch-revision-v2'] for p in directory.iterdir() if p.is_file()}
    require(any(n.endswith('maintenance-v1.py') for n in helper_files) and any(n.endswith('maintenance-v2.py') for n in helper_files) and any(n.endswith('original-fetch-helper.py') for n in helper_files),'original failed helper revisions missing')
    native=[]
    for generation,run,artifact,expected in [(1,'41040606396','next20-peco-linux-development',20),(2,'41041642421','next20-peco-linux-development',20),(3,'41043810230','next20-peco-linux-final',269)]:
        _,records=read_packet('peco',generation);prefix='native/'+run+'/'+artifact+'/';found=[];frames=[]
        for name,body in records.items():
            if not name.startswith(prefix) or not name.endswith('.json') or len(body)>4*1024**2:continue
            relative=name.removeprefix(prefix)
            if {'fixture','fixtures'} & set(relative.split('/')[:-1]):continue
            document=json.loads(body.decode('utf-8-sig'))
            if not isinstance(document,dict) or 'runner_version' not in document or not isinstance(document.get('results'),list):continue
            require(len(document['results'])==1,'unexpected native historical report cardinality')
            row=document['results'][0]
            require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'] and row['invocation_id'] not in invocations,'native historical cleanup/identity incomplete')
            invocations.add(row['invocation_id']);found.append(dict(report=name,sha256=hashlib.sha256(body).hexdigest(),status=row['status'],invocation=row['invocation_id']))
            if row['status']=='failed':
                frame=row['evidence']['screen_path'].replace('\\','/').removeprefix(scope)
                require(prefix+frame in records,'original native failure frame missing')
                raw=records[prefix+frame];frames.append(dict(report=name,frame=prefix+frame,frame_bytes=len(raw),frame_sha256=hashlib.sha256(raw).hexdigest()))
        require(len(found)==expected and len(frames)==(3 if generation==3 else 0),'native historical report/failure coverage differs')
        provider=json.loads((RAW/'peco'/('retained-native-v'+str(generation))/'provider.json').read_text())
        require(provider['conclusion']==('failure' if generation==1 else 'success'),'original native provider outcome was hidden')
        native.append(dict(generation=generation,run=run,reports=found,original_failed_frames=frames,provider_conclusion=provider['conclusion']))
    immutable_json(package/'all-attempt-evidence.json',dict(schema_version=1,project='peco',local_reports=reports,actual_local_report_documents=len(reports),
        distinct_local_target_invocations=len(reports)-len(unlaunched),original_failed_report_frames=failures,unlaunched_reports=unlaunched,
        commands=commands,original_engineering_rejections=rejected,original_helper_revisions=helper_files,native_windows=native,
        development_disposition_sha256=sha256(package/'development-disposition.json'),initial_public_shell_invocations=3,initial_public_recorder_controls=16,
        initial_authoring_targets_met=True,historical_frames_complete=True,outside_cutoff_pending_current_wrapper=pending,project_admissions=0,
        scope='Every currently retained local/native report and original failed frame,including honest empty startup frame; original setup/helper/retention failures and first failed Linux cleanup remain rejected. Completed peco-labeled engineering commands at this cutoff only. Current wrapper/subsequent audit commands require campaign delta; no new breadth/final/admission credit.'))
    print('Verified',len(reports),'local reports,',len(failures),'original local failed frames,3unlaunched refusals and',sum(len(n['reports']) for n in native),'native historical reports; no failures reconstructed.')


if __name__=='__main__':main()
