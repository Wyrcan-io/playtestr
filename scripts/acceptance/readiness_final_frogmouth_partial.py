"""Account for cancelled original Frogmouth evidence without qualifying it."""
import argparse
from collections import Counter
from pathlib import Path

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'],required=True);args=parser.parse_args()
    require(args.run=='39680492184','this disposition is bound to the original cancelled series')
    parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='cancelled','actual cancelled run required')
    packet=parent/('final-frogmouth-'+('Linux' if args.host=='linux' else 'Windows'));target=packet/'frogmouth'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/frogmouth'
    candidate=load(docs.parent/'migration-candidate-freeze.json');cell=next(c for c in candidate['cells'] if c['host']==args.host)
    installed=load(packet/'private-install/migration-v2'/(args.host+'-amd64')/'installation.json')
    require(installed['archive_sha256']==cell['archive_sha256'] and installed['binary_sha256']==cell['binary_sha256'],'wrong actual archive')
    intent=load(target/'final-series/intent.json')
    require(intent['declaration_file']=='final-series-declaration.json' and intent['declaration_sha256']==sha256(docs/'final-series-declaration.json'),
        'original declaration changed')
    profile=docs if args.host=='linux' else docs/'native-profiles/windows';frozen=load(profile/'reviewed-contract-freeze.json')
    for name,digest in frozen['all_package_inputs'].items():require(sha256(target/'host-contracts'/name)==digest,'original reviewed native package changed')
    events={};partial_files=[]
    for path in (packet/'events').glob('*'):
        if path.suffix!='.json':partial_files.append(path.name);continue
        value=load(path);require(path.name==value['id']+'-'+value['event']+'.json','event identity differs')
        events.setdefault(value['id'],{})[value['event']]=value
    ordinary=[];counts=Counter();invocations=set();report_paths=set()
    for identity,event in events.items():
        start=event.get('started',{});label=start.get('label','')
        if not label.startswith('final-batch-'):continue
        batch,name=label.removeprefix('final-batch-').split('-',1)
        require(start['project']=='frogmouth' and start['phase']=='final-archive' and start['ci_run_id']==args.run,'foreign ordinary event')
        launched='launched' in event;row=dict(attempt=identity,batch=int(batch),spec=name,launched=launched,
            finished='finished' in event,reported=False)
        if 'identified' in event:
            files=load_manifest(packet,event['identified']['identity'])['files']
            require(files[installed['binary']]==cell['binary_sha256'],'ordinary launch used another archive binary')
        path=target/'final-series'/batch/(name+'.report.json')
        if path.is_file():
            value=load(path);result=value['results'][0]
            require(launched and value['runner_version']==candidate['version'] and result['spec_version']==3
                and Path(result['spec_path'].replace('\\','/')).name==name,'foreign/unlaunched ordinary report')
            require(result['invocation_id']==result['workspace']['id'] and result['invocation_id'] not in invocations,'reused reported invocation')
            invocations.add(result['invocation_id'])
            for step in result['steps']:
                if 'state' in step:require(step['state']['invocation_id']==result['invocation_id']
                    and step['state']['workspace_id']==result['workspace']['id'],'cross-execution reported state')
            if result['status']=='passed':require(result['cleanup']['confirmed_exited'] and result['workspace']['cleaned']
                and all(s['status']=='passed' for s in result['steps']),'positive report lacks complete evidence')
            counts[result['status']]+=1;report_paths.add(path)
            row.update(reported=True,status=result['status'],invocation_id=result['invocation_id'],report_sha256=sha256(path),
                cleanup_confirmed=result['cleanup']['confirmed_exited'],workspace_cleaned=result['workspace']['cleaned'])
        ordinary.append(row)
    require(report_paths==set((target/'final-series').glob('*/*.report.json')),'orphan ordinary report')
    calibrations=[]
    for path in (target/'faults').glob('*/*.json'):
        value=load(path)
        if 'results' not in value:continue
        result=value['results'][0]
        require(value['runner_version']==candidate['version'] and result['invocation_id']==result['workspace']['id']
            and result['invocation_id'] not in invocations,'invalid calibration identity')
        invocations.add(result['invocation_id'])
        calibrations.append(dict(report=path.relative_to(packet).as_posix(),status=result['status'],report_sha256=sha256(path),
            invocation_id=result['invocation_id'],cleanup_confirmed=result['cleanup']['confirmed_exited'],workspace_cleaned=result['workspace']['cleaned']))
    cleanup=target/'retained-source/removed.json';removed=load(cleanup) if cleanup.is_file() else None
    unconfirmed=list(target.glob('runtime-unconfirmed-*.json'))
    receipt=dict(run=args.run,host=args.host,ordinary_starts=len(ordinary),ordinary_runner_launches=sum(r['launched'] for r in ordinary),
        ordinary_reported=len(report_paths),ordinary_reported_statuses=dict(counts),
        ordinary_unreported_launches=sum(r['launched'] and not r['reported'] for r in ordinary),
        public_calibration_executions=len(calibrations),calibration_observations=calibrations,ordinary_observations=ordinary,
        incomplete_event_ids=[identity for identity,event in events.items() if not {'started','identified','launched','finished'}<=set(event)],
        partial_event_files=partial_files,source_runtime_removed=bool(removed and removed['removed']),
        source_cleanup_receipt_sha256=sha256(cleanup) if cleanup.exists() else None,
        unconfirmed_process_receipts=[dict(file=p.relative_to(packet).as_posix(),sha256=sha256(p)) for p in unconfirmed],
        final_archive_credit=0,scope='Actual original cancelled series accounting only. Reported positive outcomes, unreported launches, calibration calls and cleanup dispositions remain separate. The helper-runtime ownership hazard was confirmed by a bounded native probe; Windows reported an unconfirmed runtime check. No stronger PID-cause inference or qualification is claimed.')
    immutable_json(docs/('final-first-series-'+args.host+'.json'),receipt)
    print('Accounted unqualified original Frogmouth:',args.host,'launches',receipt['ordinary_runner_launches'],
        'reports',receipt['ordinary_reported_statuses'],'calibration',len(calibrations),'source removed',receipt['source_runtime_removed'])


if __name__=='__main__':main()
