"""Audit actual generated CI context, source fault, results and native removal."""
import argparse
import asyncio
import hashlib
import json
from pathlib import PurePosixPath, PureWindowsPath
import tarfile

from adversarial_process import execute
from next20_check import RAW, ROOT, DOC, NAME, NextCampaign, owned_environment
from next20_verify_jrnl import require, source_hashes
from readiness_compact_native import compact, verify
from readiness_evidence import immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'],required=True)
    parser.add_argument('--mode',choices=['baseline','fault','recovered'],required=True)
    parser.add_argument('--route',choices=['source','private-archive'],required=True)
    parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    root=RAW/'native'/args.run;label='Linux' if args.host=='linux' else 'Windows'
    public=root/('playtestr-'+label);base=root/('next20-jrnl-delivered-'+label)
    def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
    metadata_path=root/'run-metadata.json'
    if not metadata_path.exists():
        actual=await execute(['gh','run','view',args.run,'--json','databaseId,status,conclusion,headSha,event,jobs,url'],
            'core','inspect-delivered-ci-actual-provider',cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign())
        immutable_json(metadata_path,json.loads(actual['output']))
    metadata=load(metadata_path);require(str(metadata['databaseId'])==args.run and metadata['event']=='workflow_dispatch','wrong actual CI provider run/event')
    require(metadata['status']=='completed','CI run not complete')
    jobs=[j for j in metadata['jobs'] if ('ubuntu-24.04' if args.host=='linux' else 'windows-2025') in j['name']]
    require(len(jobs)==1,'missing actual native delivered CI job');job=jobs[0]
    expected='failure' if args.mode=='fault' else 'success'
    require(job['conclusion']==expected,'wrong delivered CI provider conclusion')
    steps={s['name']:s['conclusion'] for s in job['steps']}
    for name in ['Build exact candidate runner','Explicit target build','Select committed suite and capture exact context',
                 'Render offline evidence','Accessible outcome summary','Restore actual source and checked-remove owned target']:
        require(steps.get(name)=='success','missing delivered CI proof: '+name)
    require(steps.get('Test recorded interactions')==expected,'wrong generated test exit mapping')
    require(sum(s['conclusion']=='success' and s['name'].startswith('Run actions/upload-artifact@') for s in job['steps'])==2,'missing actual report/provenance uploads')
    context=load(public/'context.json');report=load(public/'results.json')
    prepared=load(base/'jrnl/delivered-ci/prepared.json');restored=load(base/'jrnl/delivered-ci/restored.json')
    require(context['event']=='workflow_dispatch' and context['run_id']==prepared['ci_run_id']==args.run and context['tested_sha']==metadata['headSha'],'CI context/provider identity mismatch')
    require(prepared['mode']==restored['mode']==args.mode and prepared['route']==restored['route']==args.route,'wrong explicit CI route/phase')
    require(context['runner_sha256']==prepared['runner_sha256'],'actual CI runner changed')
    selected='artifacts/'+NAME+'/jrnl/host-contracts/normal-delete.json'
    require(context['selected_specs']==[selected] and len(report['results'])==1,'generated CI selected wrong suite')
    package=base/'jrnl/host-contracts';spec=load(package/'normal-delete.json')
    canonical=load(DOC/'jrnl/normal-delete.json');canonical['command'][0]=spec['command'][0]
    require(spec==canonical,'CI changed the reviewed interaction or oracle')
    require(sha256(package/'normal-delete.json')==prepared['spec_sha256'],'CI executed spec changed')
    for name,digest in context['contract_files'].items():
        prefix='artifacts/'+NAME+'/'
        require(name.startswith(prefix),'CI contract escapes campaign')
        relative=name.removeprefix(prefix);path=base/relative
        require('..' not in PurePosixPath(relative).parts and sha256(path)==digest,'CI context contract bytes mismatch')
        if not name.endswith('/normal-delete.json'):
            require(sha256(DOC/'jrnl'/relative.removeprefix('jrnl/host-contracts/'))==digest,'CI fixture/snapshot not canonical')
    retained=base/'jrnl/retained-source';runtime=load(retained/'runtime.json');inventory=load(retained/'installed-inventory.json')
    require(sha256(retained/'runtime.json')==prepared['runtime_sha256'] and sha256(retained/'installed-inventory.json')==prepared['installed_inventory_sha256']==runtime['installed_inventory_sha256'],'actual installed runtime inventory changed')
    require(list(context['target_binaries'].values())==[runtime['python_sha256']],'actual CI target executable not bound')
    provenance=load(DOC/'jrnl/source-provenance.json');fault=load(DOC/'jrnl/fault-declaration.json')['faults'][2]
    expected_source=dict(provenance['files'])
    if args.mode=='fault':
        with tarfile.open(RAW/'jrnl/retained-source/source.tar.gz','r:gz') as archive:
            entries=[m for m in archive if m.isfile() and m.name.endswith('/'+fault['path'])]
            require(len(entries)==1 and entries[0].size<1024**2,'canonical source fault member missing/ambiguous')
            original=archive.extractfile(entries[0]).read(1024**2)
        require(hashlib.sha256(original).hexdigest()==provenance['files'][fault['path']] and original.count(fault['before'].encode())==1,'canonical mutation input changed')
        expected_source[fault['path']]=hashlib.sha256(original.replace(fault['before'].encode(),fault['after'].encode())).hexdigest()
    require(prepared['source_files']==expected_source and prepared['source_executed_sha256']==expected_source[fault['path']],'actual CI target source differs from declared real fault/original')
    row=report['results'][0];require(row['spec_path'].replace('\\','/')==selected and report['os']==args.host,'wrong CI report target')
    require(row['status']==('failed' if args.mode=='fault' else 'passed') and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'wrong actual CI result or cleanup')
    require(row['invocation_id']==row['workspace']['id'],'cross-execution CI workspace')
    for step in row['steps']:
        if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-execution CI saved evidence')
    if args.mode=='fault':
        index=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
        require(row['failure']['category']=='state_assertion_failure' and all(s['status']=='passed' for s in row['steps'][:index]),'saved corruption rejected before successful terminal/exit')
        require('state_assertion_failure' in (public/'report.html').read_text(encoding='utf-8'),'missing rendered CI diagnosis')
    else:require(len(row['steps'])==len(spec['steps']) and all(s['status']=='passed' for s in row['steps']),'missing positive CI steps')
    cleanup=load(retained/'cleanup-inventory.json');removed=load(retained/'removed.json');process=load(base/'jrnl/process-proof.json')
    require(restored['source_restored_exact'] and restored['target_absent'] and restored['source_sha256']==provenance['files'][fault['path']],'missing actual exact CI recovery/removal')
    require(restored['report_sha256']==sha256(public/'results.json')==sha256(base/'jrnl/delivered-ci/results.json'),'CI cleanup used another report')
    require(removed['removed'] and removed['source_restored_exact'] and removed['owned_relative_path']=='active/jrnl' and removed['cleanup_inventory_sha256']==sha256(retained/'cleanup-inventory.json'),'unsafe/unbound actual native source removal')
    require(process['confirmed_no_matching_live_processes'] and not process['matching_live_processes'] and cleanup['process_proof_sha256']==sha256(base/'jrnl/process-proof.json'),'unconfirmed owned CI processes')
    PathType=PureWindowsPath if args.host=='windows' else PurePosixPath
    require(tuple(PathType(cleanup['owned_target']).parts[-4:])==('artifacts',NAME,'active','jrnl'),'unsafe cleanup target')
    for name,digest in inventory['files'].items():require(cleanup['files']['venv/'+name]['sha256']==digest,'CI installed module changed before removal')
    for name,digest in provenance['files'].items():require(cleanup['files']['src/'+name]['sha256']==digest,'CI source not exactly restored before removal')
    native=RAW/'jrnl'/('retained-native-v1' if args.host=='linux' else 'retained-native-v2')
    native_index=load(native/'index.json');verify(native/'packets.tar.gz',native_index['files'])
    native_payloads={r['sha256'] for r in native_index['files'].values()}
    for name,digest in cleanup['retained'].items():
        if name.startswith('wheels/') or name=='source.tar.gz':require(digest in native_payloads,'CI source/wheel omitted without matching retained native payload')
    if args.route=='private-archive':
        freeze=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json')
        cell=next(c for c in freeze['cells'] if c['host']==args.host)
        installed=load(base/('candidate/'+args.host+'/installed.json'))
        require(context['runner_sha256']==installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256'],'CI override not exact frozen archive')
        require(report['runner_version']==freeze['version'],'wrong archive runner version')
    else:require(report['runner_version']=='source-294d6e42f6c0965a4e090aa11835941984d32a0a','source route relabelled as archive')
    # Bind actual preparation and cleanup wrappers to the provider's checkout.
    for path in (base/'events').glob('*-identified.json'):
        event=load(path);reference=event['identity'];manifest=base/reference['manifest']
        require(sha256(manifest)==reference['sha256'],'changed CI prelaunch identity')
        identity=load(manifest)
        if 'base' in identity:
            reference=identity['base'];manifest=base/reference['manifest']
            require(sha256(manifest)==reference['sha256'],'changed CI base identity');identity=load(manifest)
        require(identity['files']['scripts/acceptance/next20_jrnl_ci.py'] in source_hashes(metadata['headSha'],'scripts/acceptance/next20_jrnl_ci.py'),'stale CI preparation/removal source')
    output=compact(RAW,'jrnl',[args.run],generation=args.generation)
    immutable_json(output/'delivered-ci-audit.json',dict(schema_version=1,run=args.run,host=args.host,mode=args.mode,route=args.route,
        archive_sha256=sha256(output/'packets.tar.gz'),index_sha256=sha256(output/'index.json'),
        provider_job=job['databaseId'],context_sha256=sha256(public/'context.json'),report_sha256=sha256(public/'results.json'),
        runner_sha256=context['runner_sha256'],invocation=row['invocation_id'],source_restored=True,target_removed=True,
        native_dependency_index_sha256=sha256(native/'index.json'),new_project_credit=0))
    print('Independently audited generated jrnl CI:',args.run,args.host,args.mode,args.route,'; checked expansion removal still required.')


if __name__=='__main__':asyncio.run(main())
