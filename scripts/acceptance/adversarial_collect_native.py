"""Retain compact actual native evidence; never infer success from configuration."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from adversarial_process import ROOT,DOC,RAW,run,append

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--download',type=Path,required=True)
    args=parser.parse_args()
    info=json.loads(run(['gh','run','view',args.run,'--json','status,conclusion,headSha,jobs,url'],
        'evidence','inspect-native-run')['output'])
    metadata=json.loads(run(['gh','api','repos/Wyrcan-io/playtestr/actions/runs/'+args.run+'/artifacts'],
        'evidence','native-artifact-metadata')['output'])
    destination=DOC/'native'/args.run
    destination.mkdir(parents=True,exist_ok=False)
    records=[]
    known={(r['id'],r['event']) for r in map(json.loads,(DOC/'attempts.jsonl').read_text(encoding='utf-8').splitlines())}
    matrix=json.loads((DOC/'coverage-matrix.json').read_text(encoding='utf-8'))
    for artifact in metadata['artifacts']:
        folder=args.download/artifact['name']
        if not folder.is_dir():
            raise RuntimeError('Actual downloaded artifact missing: '+artifact['name'])
        retained=destination/artifact['name']
        retained.mkdir()
        record={'artifact':artifact['name'],'id':artifact['id'],'archive_digest':artifact['digest'],
            'files':{},'run':args.run,'source':info['headSha']}
        events=list(folder.rglob('test-events.jsonl'))
        if events:
            if len(events)!=1: raise RuntimeError('Ambiguous product events')
            event_data=[json.loads(line) for line in events[0].read_text(encoding='utf-8').splitlines()]
            passed={r.get('Test') for r in event_data if r.get('Action')=='pass'}
            record['passed_mapped_controls']=[c['id'] for c in matrix['controls'] if c['test'] in passed]
            shutil.copyfile(events[0],retained/'test-events.jsonl')
            record['files']['test-events.jsonl']=hashlib.sha256(events[0].read_bytes()).hexdigest()
            for control in matrix['controls']:
                if control['test'] in passed:
                    control['evidence'].append({'run':args.run,'artifact_id':artifact['id'],
                        'source':info['headSha'],'artifact':artifact['name'],
                        'events_sha256':record['files']['test-events.jsonl']})
        for ledger in folder.rglob('attempts.jsonl'):
            for row in map(json.loads,ledger.read_text(encoding='utf-8').splitlines()):
                key=(row['id'],row['event'])
                if key not in known:
                    append(row)
                    known.add(key)
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
        for pattern in ['native-cookiecutter-*.json','cleanup-*.json','mutation-controls-*.json']:
            for path in folder.rglob(pattern):
                shutil.copyfile(path,retained/path.name)
                record['files'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        # Keep every distinct mutation's first actual red/false-green report.
        for path in folder.rglob('*-control.json'):
            fault=json.loads(path.read_text(encoding='utf-8'))
            report_path=folder/Path(fault['report'])
            if not report_path.is_file(): raise RuntimeError('Mutation report missing')
            name=fault['name']+'-report.json'
            shutil.copyfile(report_path,retained/name)
            shutil.copyfile(path,retained/path.name)
            record['files'][name]=hashlib.sha256(report_path.read_bytes()).hexdigest()
        records.append(record)
    (destination/'manifest.json').write_text(json.dumps({'run':info,'artifacts':records,
        'scope':'Actual development evidence; final campaign freeze still pending'},indent=2)+'\n',encoding='utf-8')
    (DOC/'coverage-matrix.json').write_text(json.dumps(matrix,indent=2)+'\n',encoding='utf-8')
    print('Retained native evidence',args.run,info['conclusion'])

if __name__=='__main__': main()
