"""Run three declared bounded batches of the unchanged intermittent fff case."""
import asyncio
import platform
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_fff_cases import environment
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


async def main():
    if platform.system()!='Linux':raise RuntimeError('the incident reproduction profile is native Linux only')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/fff'
    declaration=load(docs/'r3-batch-declaration.json')
    source=RAW/'fff/host-contracts';freeze=load(docs/'reviewed-contract-freeze.json')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=freeze['all_package_inputs']:
        raise RuntimeError('original reviewed fff package changed before investigation')
    binary,candidate,cell=runner('migration-v2');env=environment()
    root=RAW/'fff/r3-batches'/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'intent.json',dict(declaration_sha256=sha256(docs/'r3-batch-declaration.json'),
        candidate_version=candidate['version'],runner_sha256=cell['binary_sha256'],
        archive_sha256=cell['archive_sha256'],contract_sha256=sha256(source/'E03.json'),
        canonical_package_inputs=freeze['all_package_inputs'],planned_attempts=150,final_archive_credit=0))
    for batch in declaration['batches']:
        folder=root/('batch-'+str(batch['number']));folder.mkdir()
        package=folder/('relocated caf\u00e9 \u96ea' if batch['number']==3 else 'contracts')
        shutil.copytree(source,package)
        if {p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}!=freeze['all_package_inputs']:
            raise RuntimeError('batch relocation changed approved inputs')
        rows=[]
        for number in range(50):
            identity=uuid.uuid4().hex;report=folder/(identity+'.json')
            loaded=batch['number']==2 and number%10==0
            immutable_json(folder/(identity+'-planned.json'),dict(batch=batch['number'],number=number,
                seed=batch['seed'],controlled_two_second_worker=loaded,contract_sha256=sha256(package/'E03.json')))
            try:
                attempt=await execute([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
                    (folder/(identity+'-evidence')).relative_to(ROOT),(package/'E03.json').relative_to(ROOT)],
                    'fff','r3-E03-batch-'+str(batch['number'])+'-attempt-'+str(number),
                    env=env,timeout=130,load=loaded,campaign=Campaign())
                child=attempt['id']
            except RuntimeError:
                # Preserve failures and continue only with a complete public
                # report and positively confirmed target/workspace cleanup.
                if not report.is_file():raise
                child=None
            value=load(report);result=value['results'][0]
            if (value['runner_version']!=candidate['version'] or value['summary']['total']!=1
                    or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']):
                raise RuntimeError('bounded incident attempt lacks actual outcome or cleanup')
            if result['status']=='passed' and any(s['status']!='passed' for s in result['steps']):
                raise RuntimeError('incident pass lacks positive step evidence')
            for step in result['steps']:
                if 'state' in step and (step['state']['invocation_id']!=result['invocation_id']
                        or step['state']['workspace_id']!=result['workspace']['id']):
                    raise RuntimeError('incident state belongs to another execution')
            row=dict(number=number,report=report.relative_to(ROOT).as_posix(),report_sha256=sha256(report),
                status=result['status'],failure=result.get('failure'),successful_command=child)
            immutable_json(folder/(identity+'-observed.json'),row);rows.append(row)
            print('R3 batch',batch['number'],'attempt',number,result['status'],flush=True)
        immutable_json(folder/'complete.json',dict(attempts=rows,observed=50,
            passed=sum(r['status']=='passed' for r in rows),failed=sum(r['status']!='passed' for r in rows),
            scope='Bounded incident evidence; passing repetitions do not erase the first failure.',final_archive_credit=0))
    immutable_json(root/'complete.json',dict(completed_batches=3,observed=150,final_archive_credit=0))


if __name__=='__main__':asyncio.run(main())
