"""Tamper with an owned copy of actual archive-journey evidence, never originals."""
import argparse
import asyncio
import copy
import json
from pathlib import Path
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--id',required=True);args=parser.parse_args()
    if len(args.id)!=32 or any(c not in '0123456789abcdef' for c in args.id):raise RuntimeError('invalid journey id')
    original=RAW/'archive-experience'/args.id;receipt=load(original/'experience.json')
    if receipt['series']!='migration-v2' or receipt['host']!='windows':raise RuntimeError('actual rc.5 Windows journey required')
    root=RAW/'archive-auditor-controls'/uuid.uuid4().hex;packet=root/'packet'
    duplicate=packet/'archive-experience'/args.id
    shutil.copytree(original,duplicate,ignore=lambda directory,names:
        {'cache','gopath','modules','tmp'} & set(names) if Path(directory).name=='build' else set())
    for identity in receipt['attempts'].values():
        for kind in ['started','identified','launched','finished']:
            path=RAW/'events'/(identity+'-'+kind+'.json');out=packet/'events'/path.name
            out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,out)
        reference=load(RAW/'events'/(identity+'-identified.json'))['identity']['manifest']
        path=RAW/reference;out=packet/reference;out.parent.mkdir(parents=True,exist_ok=True)
        if not out.exists():shutil.copyfile(path,out)
        path=RAW/'core'/identity/'console.log';out=packet/'core'/identity/'console.log'
        out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,out)
    initial={p.relative_to(packet).as_posix():sha256(p) for p in packet.rglob('*') if p.is_file()}
    immutable_json(root/'declared.json',dict(source_journey=args.id,source_receipt_sha256=sha256(original/'experience.json'),
        copied_inputs=initial,controls=9,scope='Actual intermediate rc.5 archive journey evidence. Controlled metadata/binary changes only in this owned copy; original bytes remain untouched. No final-matrix or original 33-control credit.'))
    command=[sys.executable,ROOT/'scripts/acceptance/readiness_verify_archive_experience.py','--series','migration-v2',
             '--id',args.id,'--packet',packet,'--check-only']
    calls={}
    refusal_reasons={
        'actual-installed-binary':'actual source-free installed package differs',
        'candidate-archive-identity':'different actual candidate',
        'missing-command':'missing or unexpected archive journey commands',
        'false-command-exit':'calibration child outcome/cleanup differs',
        'coherently-rehashed-wrong-runner':'actual executed archive binary differs',
        'changed-console':'changed command output',
        'coherently-rehashed-cross-workspace-state':'cross-execution state proof',
        'wrong-rollback-archive':'different rollback archive',
        'nonempty-source-free-path':'source-free PATH is no longer empty'}
    async def audit(label,expected):
        result=await execute(command,'core','archive-auditor-'+label,expected=expected,timeout=120,campaign=Campaign())
        if expected and refusal_reasons[label] not in result['output']:
            raise RuntimeError('auditor failed for an unintended reason: '+label)
        calls[label]=dict(attempt=result['id'],expected_exit=expected)
    await audit('unaltered-copy',0)
    summary=duplicate/'experience.json';package=duplicate/'relocated caf\u00e9 \u96ea'
    bad=receipt['attempts']['file-changed'];identified=packet/'events'/(bad+'-identified.json')
    manifest=packet/load(identified)['identity']['manifest']
    changes=[]
    binary=duplicate/'upgrade caf\u00e9 \u96ea/playtestr.exe';data=binary.read_bytes()
    changes.append(('actual-installed-binary',{binary:bytes([data[0]^1])+data[1:]}))
    row=copy.deepcopy(receipt);row['current_archive_sha256']='0'*64
    changes.append(('candidate-archive-identity',{summary:encoded(row)}))
    row=copy.deepcopy(receipt);row['attempts'].pop('current-reads-previous-report')
    changes.append(('missing-command',{summary:encoded(row)}))
    finish=packet/'events'/(bad+'-finished.json');start=packet/'events'/(bad+'-started.json')
    end=load(finish);begin=load(start);end['exit_code']=0;begin['expected_exit']=0
    changes.append(('false-command-exit',{finish:encoded(end),start:encoded(begin)}))
    payload=load(manifest)
    binary_key='artifacts/runner-readiness-ten-project-pass/archive-experience/'+args.id+'/upgrade caf\u00e9 \u96ea/playtestr.exe'
    payload['files'][binary_key]='0'*64;new_manifest=encoded(payload)
    import hashlib
    reference=load(identified);reference['identity']['sha256']=hashlib.sha256(new_manifest).hexdigest()
    changes.append(('coherently-rehashed-wrong-runner',{manifest:new_manifest,identified:encoded(reference)}))
    console=packet/'core'/bad/'console.log'
    changes.append(('changed-console',{console:console.read_bytes()+b'changed evidence\n'}))
    report=package/'file-changed.json';value=load(report)
    state=next(s['state'] for s in value['results'][0]['steps'] if 'state' in s)
    state['workspace_id']='different-execution';new_report=encoded(value)
    row=copy.deepcopy(receipt);row['reports']['file-changed']=hashlib.sha256(new_report).hexdigest()
    changes.append(('coherently-rehashed-cross-workspace-state',{report:new_report,summary:encoded(row)}))
    row=copy.deepcopy(receipt);row['old_archive_sha256']='0'*64
    changes.append(('wrong-rollback-archive',{summary:encoded(row)}))
    changes.append(('nonempty-source-free-path',{duplicate/'empty-path/unexpected.txt':b'synthetic probe\n'}))
    for label,mutation in changes:
        originals={p:p.read_bytes() if p.exists() else None for p in mutation}
        try:
            for path,data in mutation.items():
                path.resolve().relative_to(packet.resolve());path.write_bytes(data)
            await audit(label,1)
        finally:
            for path,data in originals.items():
                if data is None:path.unlink()
                else:path.write_bytes(data)
    if initial!={p.relative_to(packet).as_posix():sha256(p) for p in packet.rglob('*') if p.is_file()}:
        raise RuntimeError('controlled copy was not exactly restored')
    if sha256(original/'experience.json')!=load(root/'declared.json')['source_receipt_sha256']:
        raise RuntimeError('original receipt changed')
    await audit('exact-restored-copy',0)
    immutable_json(root/'verified.json',dict(declared_sha256=sha256(root/'declared.json'),calls=calls,
        negative_controls=9,originals_unchanged=True,copy_restored_exactly=True,final_archive_credit=0))
    print('Nine independent archive-evidence tamper controls rejected; original and restored copy preserved:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
