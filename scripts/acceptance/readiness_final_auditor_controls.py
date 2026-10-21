"""Challenge a real final native packet in an owned, exactly restored copy."""
import argparse
import asyncio
import json
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid run')
    source=RAW/'native'/args.run;packet=source/'final-plop-Linux'
    root=RAW/'final-auditor-controls'/uuid.uuid4().hex;copy=root/'payload'
    root.mkdir(parents=True)
    def inventory(base):
        result={};total=0
        for path in base.rglob('*'):
            require(not path.is_symlink() and not path.is_junction(),'linked auditor control input')
            if path.is_file():
                require(path.stat().st_size<=4*1024**2,'auditor control member bound')
                total+=path.stat().st_size;require(total<=32*1024**2 and len(result)<10000,'auditor control storage bound')
                result[path.relative_to(base).as_posix()]=sha256(path)
        return result,total
    canonical,total=inventory(packet)
    immutable_json(root/'intent.json',dict(run=args.run,project='plop',host='linux',original_packet_files=canonical,
        original_packet_bytes=total,copy_cap_bytes=32*1024**2,controls=12,
        scope='Real completed final packet, one owned copy restored byte-for-byte between controls; originals never changed. Per-cell auditor controls, not a declaration of completed global matrix gates.'))
    shutil.copytree(packet,copy/'final-plop-Linux');shutil.copyfile(source/'run-metadata.json',copy/'run-metadata.json')
    copied=copy/'final-plop-Linux';baseline,_=inventory(copy)
    argv=[sys.executable,ROOT/'scripts/acceptance/readiness_final_plop_verify.py','--run',args.run,'--host','linux',
        '--packet-root',copy,'--check-only']
    positive=await execute(argv,'core','actual-final-auditor-positive-copy',timeout=90,campaign=Campaign())
    batch=copied/'plop/final-series/0';names=sorted(p.name.removesuffix('.observed.json') for p in batch.glob('*.observed.json'))
    name=names[0];observed=batch/(name+'.observed.json');report=batch/(name+'.report.json');identity=load(observed)['attempt']
    identified=copied/'events'/(identity+'-identified.json')
    manifest=copied/load(identified)['identity']['manifest'].replace('\\','/')
    originals={}
    def change(path,operation):
        originals.setdefault(path,path.read_bytes());value=load(path);operation(value)
        path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    def report_change(operation):
        change(report,operation);change(observed,lambda v:v.update(report_sha256=sha256(report)))
    def identity_change(operation):
        change(manifest,operation);change(identified,lambda v:v['identity'].update(sha256=sha256(manifest)))
    def remove(path):originals.setdefault(path,path.read_bytes());path.unlink()
    source_key=next(k for k in load(manifest)['files'] if k.endswith('/packages/plop/src/plop.js'))
    runner_key=next(k for k in load(manifest)['files'] if '/private-install/migration-v2/' in k and k.endswith('/playtestr'))
    installed=next((copied/'private-install/migration-v2').glob('*/installation.json'))
    native_fixture=copied/'plop/host-contracts/fixture/existing.txt'
    # Choose a later case for duplication: the first case may not yet have seen
    # the other identity. Reusing an earlier ordinary invocation is unambiguous.
    def duplicate_later():
        later=batch/(names[1]+'.report.json');later_observed=batch/(names[1]+'.observed.json')
        first=load(report)['results'][0]['invocation_id']
        def edit(value):
            row=value['results'][0];row['invocation_id']=row['workspace']['id']=first
            for step in row['steps']:
                if 'state' in step:step['state'].update(invocation_id=first,workspace_id=first)
        change(later,edit);change(later_observed,lambda v:v.update(invocation_id=first,report_sha256=sha256(later)))
    def fixture_change():
        originals.setdefault(native_fixture,native_fixture.read_bytes());native_fixture.write_bytes(b'unreviewed bytes\n')
    def cross_state(value):
        next(s['state'] for s in value['results'][0]['steps'] if 'state' in s)['workspace_id']='different-owned-execution'
    cases=[
        ('missing-launch',lambda:remove(copied/'events'/(identity+'-launched.json')),'missing launch witness'),
        ('wrong-archive',lambda:change(installed,lambda v:v.update(archive_sha256='0'*64)),'different native private archive'),
        ('wrong-executed-runner',lambda:identity_change(lambda v:v['files'].update({runner_key:'0'*64})),'actual exact archive differs'),
        ('missing-report',lambda:remove(report),'No such file or directory'),
        ('duplicate-invocation',duplicate_later,'reused invocation/workspace'),
        ('unconfirmed-cleanup',lambda:report_change(lambda v:v['results'][0]['workspace'].update(cleaned=False)),'actual result/cleanup differs'),
        ('cross-execution-state',lambda:report_change(cross_state),'cross-execution state'),
        ('wrong-fixture',fixture_change,'native canonical input changed'),
        ('wrong-target-source',lambda:identity_change(lambda v:v['files'].update({source_key:'0'*64})),'actual interpreted source/lock differs'),
        ('missing-source-faults',lambda:remove(next((copied/'plop/faults').glob('*/summary.json'))),'ambiguous source fault batch'),
        ('missing-positive-step',lambda:report_change(lambda v:v['results'][0]['steps'][0].update(status='failed')),'incomplete positive evidence'),
        ('wrong-phase',lambda:change(copied/'events'/(identity+'-started.json'),lambda v:v.update(phase='development')),'missing final-phase launch'),
    ]
    results=[]
    for label,mutate,message in cases:
        try:
            mutate()
            result=await execute(argv,'core','actual-final-auditor-negative-'+label,timeout=90,expected=1,campaign=Campaign())
            require(message in result['output'],'auditor refused for a different reason: '+label)
            results.append(dict(control=label,attempt=result['id'],specific_refusal=message))
        finally:
            for path,value in originals.items():path.write_bytes(value)
            originals.clear()
        require(inventory(copy)[0]==baseline,'auditor copy failed exact restoration')
    recovered=await execute(argv,'core','actual-final-auditor-restored-positive',timeout=90,campaign=Campaign())
    require(inventory(packet)[0]==canonical and inventory(copy)[0]==baseline,'original/restored packet changed')
    target=copy.resolve(strict=True);owned=(RAW/'final-auditor-controls').resolve(strict=True)
    target.relative_to(owned);require(target==root.resolve(strict=True)/'payload' and target.is_relative_to(ROOT.resolve()),'unsafe auditor copy removal')
    shutil.rmtree(target);require(not target.exists(),'owned auditor copy remains')
    receipt=dict(run=args.run,host='linux',project='plop',controls=results,positive_attempt=positive['id'],
        restored_positive_attempt=recovered['id'],original_packet_unchanged=True,owned_copy_removed=True,
        scope='Twelve specific refusals against a real final native packet, including rebound provenance and report identities. Global matrix gates remain open.',final_archive_credit=0)
    immutable_json(root/'verified.json',receipt)
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/final-cell-auditor-negative-controls.json',receipt)
    print('Verified twelve specific actual final-packet refusals, exact restoration and owned-copy removal.')


if __name__=='__main__':asyncio.run(main())
