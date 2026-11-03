"""Close the new rebuild-proof reports and commands after the original cutoff."""
import hashlib
import json

from next20_check import DOC, RAW
from next20_peco_cell_readback import Evidence
from next20_target_cleanup import report_documents
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    package=DOC/'peco';history=json.loads((package/'all-attempt-evidence.json').read_text());old={r['report'] for r in history['local_reports']}
    e=Evidence('windows');rows=[];frames=[]
    for path,document in report_documents(RAW/'peco'):
        name=path.relative_to(RAW).as_posix()
        if name in old:continue
        require(len(document['results'])==1,'unexpected new report cardinality');row=document['results'][0]
        require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'new target cleanup incomplete')
        value=dict(report=name,sha256=sha256(path),status=row['status'],invocation=row['invocation_id'])
        if row['status']=='failed':
            frame=e.logical(row['evidence']['screen_path']);raw=e.data(frame)
            require(raw,'new actual mutation frame missing');value.update(frame=frame,frame_sha256=hashlib.sha256(raw).hexdigest());frames.append(value)
        rows.append(value)
    require(len(rows)==9 and len(frames)==3,'normal recovery local report/frame delta differs')
    n=Evidence('linux','41713430365',4,'next20-peco-linux-rebuild-recovery');complete=n.load('peco/rebuild-recovery-summary-v1.json');faults=n.load(complete['fault_summary'])
    native=[]
    for fault in faults['faults']:
        for phase in fault['outcomes']:
            row=n.load(phase['report'])['results'][0];require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'new native recovery cleanup incomplete')
            value=dict(report=phase['report'],sha256=n.sha(phase['report']),phase=phase['phase'],invocation=row['invocation_id'])
            if row['status']=='failed':value.update(frame=row['evidence']['screen_path'],frame_sha256=n.sha(row['evidence']['screen_path']))
            native.append(value)
    require(len(native)==9,'new native recovery delta differs')
    original_ids={r['id'] for r in history['commands']};commands=[];pending=[]
    for path in (RAW/'events').glob('*-started.json'):
        started=json.loads(path.read_text());eid=started['id']
        if eid in original_ids or started['project']!='peco' and 'peco' not in started['label'].lower():continue
        end=RAW/'events'/(eid+'-finished.json')
        if not end.exists():
            require(started['label']=='peco-normal-rebuild-history-cutoff-delta','unclosed new project command');pending.append(eid);continue
        finished=json.loads(end.read_text());console=RAW/started['project']/eid/'console.log'
        require(console.is_file() and sha256(console)==finished['console_sha256'],'new command console missing/changed')
        commands.append(dict(id=eid,label=started['label'],category=finished['category'],console=console.relative_to(RAW).as_posix(),console_sha256=sha256(console),finished_sha256=sha256(end)))
    immutable_json(package/'normal-rebuild-history-delta-v1.json',dict(schema_version=1,original_history_sha256=sha256(package/'all-attempt-evidence.json'),local_new_reports=rows,native_new_reports=native,commands=commands,
        actual_local_report_total=len(history['local_reports'])+len(rows),actual_local_target_total=history['distinct_local_target_invocations']+len(rows),original_unlaunched_count=3,
        normal_rebuild_local_failed_frames=frames,all_original_failure_history_preserved=True,outside_cutoff_current_wrapper=pending,project_admissions=0,
        scope='New normal-rebuild9phases per host plus every completed project-labeled command since original cutoff. Original materialization/metadata/timeout failures remain in their denominators. Current wrapper/subsequent closing commands require final campaign delta.'))
    print('Closed9new local and9native recovery reports,allnew failure frames and',len(commands),'completed command deltas; original history preserved.')


if __name__=='__main__':main()
