"""Retain compact actual native evidence; never infer success from configuration."""
import argparse
import hashlib
import json
from pathlib import Path
from adversarial_process import ROOT,DOC,RAW,run,append,read_attempts,read_ledger
from adversarial_coverage import recorded_source_digest

def persist(path,data):
    """Resume partial collection without replacing different retained bytes."""
    if path.exists():
        if path.read_bytes()!=data:
            raise RuntimeError('Retained native evidence conflict: '+str(path))
        return
    path.write_bytes(data)

def prepare_destination(destination,artifacts,download,*,resume=False):
    for artifact in artifacts:
        if not (download/artifact['name']).is_dir():
            raise RuntimeError('Actual downloaded artifact missing: '+artifact['name'])
    if destination.exists():
        if not resume or (destination/'manifest.json').exists():
            raise RuntimeError('Existing native collection requires explicit incomplete resume')
    destination.mkdir(parents=True,exist_ok=resume)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--download',type=Path,required=True)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    info=json.loads(run(['gh','run','view',args.run,'--json','status,conclusion,headSha,jobs,url'],
        'evidence','inspect-native-run')['output'])
    metadata=json.loads(run(['gh','api','repos/Wyrcan-io/playtestr/actions/runs/'+args.run+'/artifacts'],
        'evidence','native-artifact-metadata')['output'])
    destination=DOC/'native'/args.run
    prepare_destination(destination,metadata['artifacts'],args.download,resume=args.resume)
    records=[]
    source_cache={}
    known={(r['id'],r['event']) for r in read_attempts()}
    matrix=json.loads((DOC/'coverage-matrix.json').read_text(encoding='utf-8'))
    for artifact in metadata['artifacts']:
        folder=args.download/artifact['name']
        if not folder.is_dir():
            raise RuntimeError('Actual downloaded artifact missing: '+artifact['name'])
        retained=destination/artifact['name']
        retained.mkdir(exist_ok=args.resume)
        record={'artifact':artifact['name'],'id':artifact['id'],'archive_digest':artifact['digest'],
            'files':{},'run':args.run,'source':info['headSha']}
        report_inventory=[]
        state_inventory=[]
        harness_failures=[]
        def retain_evidence(result):
            for key,reference in (result.get('evidence') or {}).items():
                if key not in {'screen_path','diff_path'}: continue
                relative=Path(reference.replace('\\','/'))
                if relative.is_absolute() or '..' in relative.parts or ':' in reference:
                    raise RuntimeError('Unsafe native failure reference')
                lexical=folder/relative
                for component in [lexical,*lexical.parents]:
                    if component==folder.parent: break
                    if component.is_symlink() or getattr(component,'is_junction',lambda:False)():
                        raise RuntimeError('Linked native failure reference')
                original=lexical.resolve(strict=True)
                if not original.is_relative_to(folder.resolve()) or original.stat().st_size>4*1024*1024:
                    raise RuntimeError('Native failure evidence escapes bounds')
                output=retained/'fault-evidence'/relative
                output.parent.mkdir(parents=True,exist_ok=True)
                if output.exists() and output.read_bytes()!=original.read_bytes():
                    raise RuntimeError('Native failure evidence conflict')
                persist(output,original.read_bytes())
                record['files'][output.relative_to(retained).as_posix()]=hashlib.sha256(output.read_bytes()).hexdigest()
        for path in folder.rglob('*.json'):
            if path.stat().st_size>4*1024*1024:
                raise RuntimeError('Native evidence JSON file exceeds retention bound')
            data=json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data,dict) and 'summary' in data and 'results' in data:
                for result in data['results']:
                    if result.get('status')=='failed': retain_evidence(result)
                report_inventory.append({'path':path.relative_to(folder).as_posix(),
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'summary':data['summary'],'results':[{key:result.get(key) for key in
                        ['run_id','name','status','cleanup','failure']} for result in data['results']]})
            if path.name=='state-oracle.json':
                state_inventory.append({'attempt_id':path.parent.name,
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'observed':data})
            if path.name in {'harness-error.json','cleanup-errors.json'}:
                harness_failures.append({'attempt_id':path.parent.name,
                    'kind':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'observed':data})
        for name,inventory in [('report-inventory.json',report_inventory),('state-inventory.json',state_inventory),
                               ('harness-failures.json',harness_failures)]:
            output=retained/name
            persist(output,(json.dumps(inventory,indent=2)+'\n').encode('utf-8'))
            record['files'][name]=hashlib.sha256(output.read_bytes()).hexdigest()
        events=list(folder.rglob('test-events.jsonl'))
        if events:
            if len(events)!=1: raise RuntimeError('Ambiguous product events')
            event_data=[json.loads(line) for line in events[0].read_text(encoding='utf-8').splitlines()]
            passed={r.get('Test') for r in event_data if r.get('Action')=='pass'}
            record['passed_mapped_controls']=[]
            record['historical_definition_controls']=[]
            persist(retained/'test-events.jsonl',events[0].read_bytes())
            record['files']['test-events.jsonl']=hashlib.sha256(events[0].read_bytes()).hexdigest()
            for control in matrix['controls']:
                if control['test'] in passed:
                    actual=recorded_source_digest(info['headSha'],control['source'],source_cache)
                    matches=actual==control['test_source_sha256']
                    record['passed_mapped_controls' if matches else 'historical_definition_controls'].append(control['id'])
                    control['evidence'].append({'run':args.run,'artifact_id':artifact['id'],
                        'source':info['headSha'],'artifact':artifact['name'],
                        'test_source_sha256':actual,'matches_current_test_source':matches,
                        'events_sha256':record['files']['test-events.jsonl']})
        race_events=list(folder.rglob('race-events.jsonl'))
        if race_events:
            if len(race_events)!=1: raise RuntimeError('Ambiguous native race events')
            race=[json.loads(line) for line in race_events[0].read_text(encoding='utf-8').splitlines()]
            record['race_failed_tests']=[r.get('Test',r.get('Package')) for r in race if r.get('Action')=='fail']
            record['race_passed_tests']=[r['Test'] for r in race if r.get('Action')=='pass' and r.get('Test')]
            persist(retained/'race-events.jsonl',race_events[0].read_bytes())
            record['files']['race-events.jsonl']=hashlib.sha256(race_events[0].read_bytes()).hexdigest()
        ledger_files=[*folder.rglob('attempts.jsonl'),*folder.rglob('attempts-v2.jsonl')]
        ledgers=[(ledger,read_ledger(ledger)) for ledger in ledger_files]
        started_by_directory={}
        for ledger,ledger_rows in ledgers:
            started_by_id=started_by_directory.setdefault(ledger.parent,{})
            for row in ledger_rows:
                if row['event']=='started':started_by_id.setdefault(row['id'],row)
        for ledger,ledger_rows in ledgers:
            for row in ledger_rows:
                key=(row['id'],row['event'])
                if key not in known:
                    append(row)
                    known.add(key)
                if row['event']=='finished' and row['label'] in {'detached-startup-before','detached-startup-after',
                        'workspace-short-path-before','workspace-short-path-after'}:
                    started=started_by_directory[ledger.parent].get(row['id'])
                    if started is None:raise RuntimeError('Native startup attempt lacks its original started record')
                    console=folder/started['evidence']/'console.log'
                    if not console.is_file():
                        continue # Historical ledger entries are not this host's executions.
                    if hashlib.sha256(console.read_bytes()).hexdigest()!=row['console_sha256']:
                        raise RuntimeError('Native startup console identity mismatch')
                    output=retained/(row['label']+'.txt')
                    persist(output,console.read_bytes())
                    record['files'][output.name]=row['console_sha256']
        for identity_root in folder.rglob('identities'):
            if not identity_root.is_dir(): continue
            for manifest in identity_root.glob('*.json'):
                data=manifest.read_bytes()
                if hashlib.sha256(data).hexdigest()!=manifest.stem:
                    raise RuntimeError('Downloaded identity manifest digest mismatch')
                target=DOC/'identities'/manifest.name
                target.parent.mkdir(exist_ok=True)
                if target.exists() and target.read_bytes()!=data:
                    raise RuntimeError('Retained identity manifest conflict')
                if not target.exists(): target.write_bytes(data)
        for pattern in ['native-*.json','frozen-runner.json','cleanup-Linux.json','cleanup-Windows.json','cleanup-Darwin.json','mutation-controls-*.json','rust-pristine-build-preflight-*.json','c-pristine-build-preflight-*.json','*-restoration-failure.json']:
            for path in folder.rglob(pattern):
                persist(retained/path.name,path.read_bytes())
                record['files'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        for path in folder.rglob('external-state-*.json'):
            state_root=retained/'external-state'
            state_root.mkdir(exist_ok=True)
            persist(state_root/path.name,path.read_bytes())
            record['files']['external-state/'+path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        for path in folder.rglob('summary.json'):
            if 'wizard-reproduction' not in path.parts:continue
            summary=json.loads(path.read_text(encoding='utf-8'))
            if 'attempts' not in summary or 'failures' not in summary:continue
            relative=Path('wizard-reproduction')/path.parent.name/'summary.json'
            output=retained/relative;output.parent.mkdir(parents=True,exist_ok=True)
            persist(output,path.read_bytes())
            record['files'][relative.as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        # Keep every distinct mutation's first actual red/false-green report.
        for path in folder.rglob('*-control.json'):
            fault=json.loads(path.read_text(encoding='utf-8'))
            report_path=folder/Path(fault['report'])
            if not report_path.is_file(): raise RuntimeError('Mutation report missing')
            name=fault['name']+'-report.json'
            persist(retained/name,report_path.read_bytes())
            persist(retained/path.name,path.read_bytes())
            record['files'][name]=hashlib.sha256(report_path.read_bytes()).hexdigest()
            probe_id=fault.get('state_probe_evidence_id')
            if probe_id:
                if not all(c in '0123456789abcdef' for c in probe_id) or len(probe_id)!=32:
                    raise RuntimeError('Invalid native state fault attempt ID')
                errors=list(folder.rglob(probe_id+'/harness-error.json'))
                if len(errors)!=1: raise RuntimeError('Native state fault diagnosis missing or ambiguous')
                output=retained/(fault['name']+'-state-error.json')
                persist(output,errors[0].read_bytes())
                record['files'][output.name]=hashlib.sha256(output.read_bytes()).hexdigest()
            # Remote archives expire. Keep actual fault screens/diffs rather than
            # retaining a JSON reference to evidence that was never copied.
            report=json.loads(report_path.read_text(encoding='utf-8'))
            for result in report.get('results',[]):
                retain_evidence(result)
        records.append(record)
    (destination/'manifest.json').write_text(json.dumps({'run':info,'artifacts':records,
        'scope':('Actual frozen-campaign evidence; completion still requires all gates and verified identities'
                 if any(a['name'].startswith('adversarial-final-') for a in metadata['artifacts'])
                 else 'Actual development evidence; final campaign freeze still pending')},indent=2)+'\n',encoding='utf-8')
    (DOC/'coverage-matrix.json').write_text(json.dumps(matrix,indent=2)+'\n',encoding='utf-8')
    print('Retained native evidence',args.run,info['conclusion'])

if __name__=='__main__': main()
