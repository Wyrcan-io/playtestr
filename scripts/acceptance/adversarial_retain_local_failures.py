"""Keep compact original local failures without rewriting the attempt history."""
import argparse
import hashlib
import json
from adversarial_process import DOC,RAW,read_attempts

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project')
    args=parser.parse_args()
    if not args.project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.project):
        raise RuntimeError('Invalid project identity')
    destination=DOC/args.project/'local-first-failures'
    destination.mkdir(exist_ok=True)
    records=[]
    for row in read_attempts():
        if row.get('project')!=args.project or row.get('event')!='finished' or row.get('category')=='passed':continue
        if '/' in row['id'] or '\\' in row['id'] or '..' in row['id']:raise RuntimeError('Unsafe attempt identity')
        source=RAW/args.project/row['id']/'console.log'
        if not source.is_file():continue
        data=source.read_bytes()
        if len(data)>4*1024*1024:raise RuntimeError('Failure console exceeds individual retention bound')
        if hashlib.sha256(data).hexdigest()!=row['console_sha256']:raise RuntimeError('Original failure hash mismatch')
        output=destination/(row['id']+'.log')
        if output.exists() and output.read_bytes()!=data:raise RuntimeError('Refuse replacing retained failure')
        output.write_bytes(data)
        records.append(dict(attempt=row,file=output.name,sha256=row['console_sha256']))
    index=destination/('inventory-'+str(len(records))+'.json')
    content=(json.dumps(records,indent=2)+'\n').encode('utf-8')
    if index.exists() and index.read_bytes()!=content:raise RuntimeError('Failure inventory conflict')
    index.write_bytes(content)
    faults=DOC/args.project/'local-fault-evidence'
    fault_records=[]
    for source in sorted((RAW/args.project).glob('*-control.json')):
        control=json.loads(source.read_text(encoding='utf-8'))
        if not control.get('restored') or not control.get('contracts_unchanged'):
            raise RuntimeError('Cannot retain a control as restored without actual restoration')
        faults.mkdir(exist_ok=True)
        retained={}
        def preserve(original,label):
            data=original.read_bytes()
            if len(data)>4*1024*1024:raise RuntimeError('Fault evidence retention bound')
            output=faults/(source.stem+'-'+label)
            if output.exists() and output.read_bytes()!=data:raise RuntimeError('Fault evidence conflict')
            output.write_bytes(data)
            retained[output.name]=hashlib.sha256(data).hexdigest()
        preserve(source,'control.json')
        from adversarial_process import ROOT
        report=(ROOT/control['report']).resolve(strict=True)
        report.relative_to((RAW/args.project).resolve(strict=True))
        preserve(report,'report.json')
        data=json.loads(report.read_text(encoding='utf-8'))
        for result in data['results']:
            for key,reference in (result.get('evidence') or {}).items():
                if key not in {'screen_path','diff_path'}:continue
                original=(ROOT/reference).resolve(strict=True)
                original.relative_to((RAW/args.project).resolve(strict=True))
                preserve(original,key+'.txt')
        if control.get('state_probe_evidence_id'):
            preserve(RAW/args.project/control['state_probe_evidence_id']/'harness-error.json','state-error.json')
        fault_records.append(dict(control=control,files=retained))
    if fault_records:
        manifest=faults/('manifest-'+str(len(fault_records))+'.json')
        data=(json.dumps(fault_records,indent=2)+'\n').encode('utf-8')
        if manifest.exists() and manifest.read_bytes()!=data:raise RuntimeError('Fault manifest conflict')
        manifest.write_bytes(data)
    print('Retained',len(records),'actual nonpassing local attempts; intentional negative controls remain distinguishable by ledger labels')
    print('Retained',len(fault_records),'actual restored source controls and their original evidence')

if __name__=='__main__':main()
