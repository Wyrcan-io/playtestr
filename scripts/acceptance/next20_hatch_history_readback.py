"""Preserve actual Hatch report failures and original authoring failures separately."""
import hashlib
import json

from next20_check import DOC,RAW
from next20_target_cleanup import cleanup_reports
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    package=DOC/'hatch';scope='artifacts/'+RAW.name+'/'
    reports=[];failures=[];invocations=set()
    for path,document,digest in cleanup_reports(RAW/'hatch',['retained-complete-final-v1']):
        for result in document['results']:
            require(result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'historical target/workspace cleanup incomplete')
            invocations.add(result['invocation_id'])
            row=dict(report=path.relative_to(RAW).as_posix(),sha256=digest,invocation=result['invocation_id'],status=result['status'])
            if result['status']=='failed':
                frame=result['evidence']['screen_path'].replace('\\','/').removeprefix(scope)
                require(not frame.startswith(('/','../')) and ':' not in frame,'historical failure frame escapes campaign')
                body=(RAW/frame).read_bytes();require(body,'original failure frame missing')
                row.update(category=result['failure']['category'],frame=frame,frame_sha256=hashlib.sha256(body).hexdigest());failures.append(row)
            reports.append(row)
    commands=[]
    for path in sorted((RAW/'events').glob('*-started.json')):
        started=json.loads(path.read_text(encoding='utf-8-sig'))
        if started['project']!='hatch' and 'hatch' not in started['label'].lower():continue
        eid=started['id'];finished_path=RAW/'events'/(eid+'-finished.json')
        if not finished_path.exists():continue # Current readback wrapper is pending, explicitly outside this cutoff.
        finished=json.loads(finished_path.read_text(encoding='utf-8-sig'))
        console=RAW/started['project']/eid/'console.log'
        require(console.is_file() and sha256(console)==finished['console_sha256'],'original command console changed/missing')
        commands.append(dict(id=eid,label=started['label'],project=started['project'],phase=started['phase'],
            started_sha256=sha256(path),finished_sha256=sha256(finished_path),category=finished['category'],console_sha256=sha256(console)))
    original_ids=['0838339de39949d187fb9473bf185e01','1cc16f7ed8b641819053150ad7d46333','9d31760e68c44e9eac9fa71541676d1a']
    for eid in original_ids:require(any(c['id']==eid and c['category']!='passed' for c in commands),'original authoring rejection omitted')
    for digest in ['779f1a663a0d05687761ab8625e994ba4a65f539f0f092099084448124a1bc14','5296f572ba619cc637f4fed4e93c59d34ee069b69bead96827b10f997c7c2e73']:
        require(sha256(RAW/'hatch/helper-source-revisions'/(digest+'.py'))==digest,'original authoring helper source missing')
    require(any(f['category']=='state_assertion_failure' for f in failures),'historical state failure absent')
    immutable_json(package/'all-attempt-evidence.json',dict(schema_version=1,project='hatch',actual_local_report_documents=len(reports),
        distinct_local_report_invocations=len(invocations),reports=reports,original_failed_report_frames=failures,commands=commands,
        original_authoring_rejections=original_ids,initial_authoring_failure_sha256=sha256(package/'initial-authoring-failure.json'),
        initial_twenty_control_target_met=False,project_admissions=0,
        scope='Point-in-time completed local Hatch-labeled command/report readback, including both original public authoring rejections and every original failed report screen. Current wrapper and subsequent audit commands are outside this cutoff and must be closed by the final campaign delta. Native full packets are audited separately. No retries removed or failures reconstructed.'))
    print('Read back',len(reports),'local reports,',len(failures),'original failed report screens,',len(commands),'completed commands; original authoring rejections remain failed.')


if __name__=='__main__':main()
