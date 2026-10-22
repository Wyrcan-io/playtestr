"""Independent actual-packet audit of a complete frozen jrnl native cell."""
import argparse
import copy
import hashlib
from functools import lru_cache
import json
import posixpath
from pathlib import PurePosixPath, PureWindowsPath
import subprocess
import tarfile
import uuid

from next20_check import RAW,ROOT,DOC,NAME
from readiness_compact_native import verify
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def json_payloads(retained,index):
    wanted={}
    for name,row in index['files'].items():
        if name.endswith('.json'):
            require(row['bytes']<=4*1024**2,'audit JSON file bound')
            wanted.setdefault(row.get('member',name),[]).append(name)
    result={}
    with tarfile.open(retained/'packets.tar.gz','r|gz') as archive:
        for member in archive:
            if member.name not in wanted:continue
            require(member.isfile() and member.size<=4*1024**2,'unsafe actual JSON payload')
            data=archive.extractfile(member).read(4*1024**2+1)
            for name in wanted[member.name]:
                row=index['files'][name]
                require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'changed actual JSON payload')
                result[name]=json.loads(data.decode('utf-8-sig'))
    require(set(result)=={n for names in wanted.values() for n in names},'missing actual JSON payload')
    return result


@lru_cache(maxsize=128)
def source_hashes(revision,name):
    blob=subprocess.check_output(['git','show',revision+':'+name])
    return {hashlib.sha256(blob).hexdigest(),hashlib.sha256(blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()}


def build_model(retained,run,host):
    index=json.loads((retained/'index.json').read_text(encoding='utf-8'))
    require(sha256(retained/'packets.tar.gz')==index['archive_sha256'],'retained native archive changed')
    verify(retained/'packets.tar.gz',index['files'])
    payloads=json_payloads(retained,index)
    artifact='next20-jrnl-'+('Windows' if host=='windows' else 'Linux')
    prefix='native/'+run+'/'+artifact+'/'
    metadata=payloads['native/'+run+'/run-metadata.json']
    require(str(metadata['databaseId'])==run,'wrong provider run')
    jobs=[j for j in metadata['jobs'] if ('windows-2025' if host=='windows' else 'ubuntu-24.04') in j['name']]
    require(len(jobs)==1 and jobs[0]['conclusion']=='success','missing successful actual native job')
    steps={s['name']:s['conclusion'] for s in jobs[0]['steps']}
    for batch in range(12):require(steps.get(f'Final fresh-state batch {batch+1} of twelve')=='success','missing actual complete final provider batch')
    require(steps.get('Three actual source faults and unchanged-contract recovery')=='success','missing actual source fault provider step')
    revision=metadata['headSha']
    candidate=json.loads((ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json').read_text())
    expected=next(c for c in candidate['cells'] if c['host']==host)
    declaration=json.loads((DOC/'jrnl/final-series-declaration.json').read_text())
    canonical=json.loads((DOC/'jrnl/scenarios.json').read_text())
    provenance=json.loads((DOC/'jrnl/source-provenance.json').read_text())
    def path(relative):return prefix+relative
    def get(relative):
        name=path(relative);require(name in payloads,'actual packet JSON omitted: '+relative)
        return payloads[name]
    def digest(relative):return index['files'][path(relative)]['sha256']
    def command(eid):
        events={event:get('events/'+eid+'-'+event+'.json') for event in ['started','identified','launched','finished']}
        require(all(e['campaign']==NAME and e['id']==eid for e in events.values()),'cross-campaign command identity')
        started=events['started'];finish=events['finished']
        require(started['ci_run_id']==run and finish['category']=='passed' and finish['harness_cleanup']=='harness_process_reaped','failed/incomplete actual command')
        def manifest(reference):
            relative=reference['manifest'].replace('\\','/')
            require(not relative.startswith('/') and '..' not in relative.split('/'),'unsafe actual manifest reference')
            require(digest(relative)==reference['sha256'],'changed actual launch identity')
            return get(relative)
        identity=manifest(events['identified']['identity'])
        base=manifest(identity['base']);target=manifest(identity['target_catalog'])
        normalized={}
        for name,value in base['files'].items():
            logical=posixpath.normpath(name.replace('\\','/'))
            require(not logical.startswith(('/','../')) and ':' not in logical,'launch metadata path escapes workspace')
            require(logical not in normalized or normalized[logical]==value,'ambiguous actual executable/input alias')
            normalized[logical]=value
        # Retain original manifest/hash; normalize only workspace-relative path
        # spelling for identity lookup, never fixture/oracle/report bytes.
        base=dict(base,files=normalized)
        for name in ['scripts/acceptance/next20_check.py','scripts/acceptance/adversarial_process.py',
                     'scripts/acceptance/readiness_evidence.py']:
            require(base['files'].get(name) in source_hashes(revision,name),'stale actual native helper source')
        helper='scripts/acceptance/'+('next20_jrnl_final.py' if started['label'].startswith('final-batch-') else 'next20_jrnl_faults.py')
        require(base['files'].get(helper) in source_hashes(revision,helper),'stale actual ordinary/fault execution helper')
        require(base['files'].get('artifacts/'+NAME+'/candidate/'+host+'/playtestr'+('.exe' if host=='windows' else ''))==expected['binary_sha256'],'actual launched runner executable mismatch')
        actual_source={name.split('/src/',1)[1]:value for name,value in target['files'].items() if '/active/jrnl/src/' in name}
        require(set(actual_source)==set(provenance['files']),'actual target source identity coverage incomplete')
        return dict(events=events,base=base,target=target,source=actual_source)
    runtime=get('jrnl/retained-source/runtime.json')
    inventory=get('jrnl/retained-source/installed-inventory.json')
    cleanup=get('jrnl/retained-source/cleanup-inventory.json')
    removed=get('jrnl/retained-source/removed.json')
    owner=get('jrnl/retained-source/task-owned.json')
    process=get('jrnl/process-proof.json')
    def core_operation(label,helper):
        candidates=[(n,v) for n,v in payloads.items() if n.startswith(prefix+'events/') and n.endswith('-started.json') and v.get('label')==label]
        require(len(candidates)==1,'missing/duplicate actual native cleanup operation')
        _,started=candidates[0];eid=started['id']
        identified=get('events/'+eid+'-identified.json');finish=get('events/'+eid+'-finished.json')
        reference=identified['identity'];relative=reference['manifest'].replace('\\','/')
        require(digest(relative)==reference['sha256'],'changed native cleanup identity')
        identity=get(relative)
        require(identity['files'].get(helper) in source_hashes(revision,helper),'stale native cleanup subprocess source')
        require(finish['category']=='passed' and finish['exit_code']==0 and finish['harness_cleanup']=='harness_process_reaped','native cleanup operation did not complete successfully')
        require(index['files'][path('core/'+eid+'/console.log')]['sha256']==finish['console_sha256'],'changed actual native cleanup console')
    core_operation('native-jrnl-source-runtime-removal','scripts/acceptance/'+('next20_remove_target.ps1' if host=='windows' else 'next20_target_cleanup.py'))
    if host=='windows':core_operation('native-jrnl-owned-process-proof','scripts/acceptance/next20_target_process_proof.ps1')
    require(owner['pin']==provenance['pin'] and owner['campaign']==NAME and owner['slug']=='jrnl','wrong actual target ownership/pin')
    pure=PureWindowsPath if host=='windows' else PurePosixPath
    expected_target=str(pure(owner['workspace'])/'artifacts'/NAME/'active/jrnl')
    require(pure(cleanup['owned_target'])==pure(expected_target)==pure(process['owned_target']),'unsafe or mismatched cleanup root')
    require(pure(owner['workspace']).name=='playtestr','unexpected native checkout ownership root')
    require(process['confirmed_no_matching_live_processes'] and not process['matching_live_processes'],'unconfirmed native process termination')
    require(removed['removed'] and removed['owned_relative_path']=='active/jrnl' and removed['source_restored_exact'] and cleanup['source_restored_exact'],'missing exact restored source/runtime removal')
    require(removed['cleanup_inventory_sha256']==digest('jrnl/retained-source/cleanup-inventory.json'),'cleanup inventory changed')
    require(cleanup['process_proof_sha256']==digest('jrnl/process-proof.json'),'native process proof changed')
    require(cleanup['actual_reports_with_confirmed_cleanup']==249,'target cleanup did not account for all actual final reports')
    for name,target in cleanup['owned_links'].items():
        require(host=='linux' and name in {'venv/lib64','venv-pair-0/lib64','venv-pair-1/lib64'} and target=='lib','unsafe runtime cleanup link')
    acquisition=get('jrnl/retained-source/acquisition.json')
    require(acquisition['source_files']==provenance['files'],'retained source provenance differs')
    require(digest('jrnl/retained-source/source.tar.gz')==acquisition['archive_sha256'],'retained canonical source archive changed')
    wheels=get('jrnl/retained-source/wheels.json')
    for name,row in wheels.items():require(digest('jrnl/retained-source/wheels/'+name)==row['sha256'],'missing/changed retained actual dependency wheel')
    require(runtime['installed_inventory_sha256']==digest('jrnl/retained-source/installed-inventory.json'),'retained runtime dependency identity mismatch')
    host_cases=get('jrnl/host-contracts/scenarios.json')['cases']
    native_python=str(pure(runtime['python']).relative_to(pure(owner['workspace']))).replace('\\','/')
    for case in canonical['cases']:
        native_base=get('jrnl/host-contracts/'+case['spec'])
        reviewed=json.loads((DOC/'jrnl'/case['spec']).read_text(encoding='utf-8'))
        reviewed['command'][0]=posixpath.relpath(native_python,'artifacts/'+NAME+'/jrnl/host-contracts')
        if host=='linux' and case['id']=='N06':
            position=next(i for i,s in enumerate(reviewed['steps']) if s.get('key')=='CtrlZ')
            require(reviewed['steps'][position+1]=={'key':'Enter'},'canonical EOF group changed')
            reviewed['steps']=reviewed['steps'][:position]+[{'key':'CtrlD'}]+reviewed['steps'][position+2:]
        require(native_base==reviewed,'native base silently changed canonical semantics/oracles')
        declared=next(c for c in host_cases if c['id']==case['id'])
        require(declared['canonical_sha256']==case['spec_sha256'] and declared['spec_sha256']==digest('jrnl/host-contracts/'+case['spec']),'stale canonical/native base contract binding')
    model=dict(project='jrnl',host=host,run=run,revision=revision,provider_job=jobs[0]['databaseId'],
        runner_sha256=expected['binary_sha256'],archive_sha256=expected['archive_sha256'],ordinary=[],faults=[],
        cleanup=dict(removed=True,source_restored=True,target_root=expected_target,process_confirmed=True),
        canonical_cases=[c['id'] for c in canonical['cases']],first_development_disposition_sha256=sha256(DOC/'jrnl/first-development-disposition.json'))
    seen=set()
    def normalize(report):
        require(report['report_version']==3 and report['runner_version']=='v0.4.0-rc.5' and report['os']==host and report['arch']=='amd64','wrong actual native runner/report identity')
        require(len(report['results'])==1,'not an individual actual execution report')
        row=report['results'][0]
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in seen,'duplicate/cross-invocation native execution')
        seen.add(row['invocation_id'])
        return dict(invocation=row['invocation_id'],workspace=row['workspace']['id'],status=row['status'],
            cleaned=row['workspace']['cleaned'],confirmed_exited=row['cleanup']['confirmed_exited'],
            category=row.get('failure',{}).get('category'),steps=[dict(action=s['action'],status=s['status'],state=s.get('state')) for s in row['steps']])
    for batch in range(12):
        summary=get(f'jrnl/final-series/{batch}/summary.json');prepared=get(f'jrnl/final-series/{batch}/prepared.json')
        catalog=get(f'jrnl/final-series/{batch}/runtime-catalog.json')
        require(catalog['files']==inventory['files'],'actual executed runtime dependency bytes differ')
        require(catalog['executable']==prepared['actual_python'] and catalog['executable_sha256']==runtime['python_sha256'],'wrong copied/normal interpreter')
        require(prepared['actual_runtime_catalog_sha256']==digest(f'jrnl/final-series/{batch}/runtime-catalog.json'),'stale actual runtime catalog')
        runtime_relative=catalog['runtime_root'].split('/active/jrnl/',1)[1]
        for name,value in catalog['files'].items():
            require(cleanup['files'][runtime_relative+'/'+name]['sha256']==value,'runtime changed between actual launch and cleanup')
        require(len(summary['observations'])==20 and summary['batch']==batch,'partial native batch summary')
        package=f'jrnl/final-series/{batch}/'+('relocated café 雪' if batch==5 else 'contracts')
        for observation in summary['observations']:
            cid=observation['case'];case=next(c for c in canonical['cases'] if c['id']==cid)
            planned=get(f'jrnl/final-series/{batch}/{cid}.planned.json')
            spec=get(package+'/'+case['spec'])
            report=get(f'jrnl/final-series/{batch}/{cid}.report.json')
            require(digest(package+'/'+case['spec'])==planned['spec_sha256']==observation['spec_sha256'],'actual executed spec mismatch')
            require(digest(f'jrnl/final-series/{batch}/{cid}.report.json')==observation['report_sha256'],'actual report reference changed')
            launch=command(observation['attempt'])
            require(launch['events']['started']['phase']=='final-archive','wrong-phase ordinary execution')
            require(launch['source']==provenance['files'],'ordinary run used mutated/wrong target source')
            require(launch['base']['files'].get(planned['spec'])==planned['spec_sha256'],'prelaunch actual contract identity missing')
            require(launch['base']['files'].get(prepared['actual_python'])==runtime['python_sha256'],'actual target executable not bound at launch')
            require(launch['target']['files'].get('artifacts/'+NAME+'/active/jrnl/launch-runtime-catalog.json')==prepared['actual_runtime_catalog_sha256'],'actual runtime catalog missing from prelaunch identity')
            actual=normalize(report)
            require(actual['invocation']==observation['invocation'],'observed report from another invocation')
            require(len(actual['steps'])==len(spec['steps']) and [s['action'] for s in actual['steps']]==[next(iter(s)) for s in spec['steps']],'actual positive step sequence differs')
            # Fixture and approved expectation data stay exact on every variant.
            native_base=get('jrnl/host-contracts/'+case['spec'])
            expected_spec=copy.deepcopy(native_base)
            expected_spec['command'][0]=posixpath.relpath(prepared['actual_python'],posixpath.dirname(planned['spec']))
            if batch==4:expected_spec.update(width=expected_spec['width']+10,height=expected_spec['height']+2)
            if batch==7:
                steps=[]
                for step in expected_spec['steps']:
                    if set(step)=={'text'} and len(step['text'])>1 and all(ord(c)>=32 and ord(c)!=127 for c in step['text']):
                        steps.extend({'text':step['text'][i:i+3]} for i in range(0,len(step['text']),3))
                    else:steps.append(step)
                expected_spec['steps']=steps
            if batch==10 and cid=='N01':expected_spec['height']=12
            if batch==11:expected_spec['startup_timeout_ms']=2000
            require(spec==expected_spec,'undeclared final variant/oracle change')
            frozen=json.loads((DOC/'jrnl/development-test-freeze.json').read_text())
            for name,value in frozen['inputs'].items():
                if name.startswith(case['initial_fixture']+'/') or name.startswith('snapshots/') and any(s.get('snapshot')==name.removeprefix('snapshots/') for s in spec['steps']):
                    require(digest(package+'/'+name)==value,'actual fixture/snapshot byte mismatch')
            actual.update(batch=batch,case=cid,spec_sha256=planned['spec_sha256'],runner_sha256=planned['runner_sha256'],
                archive_sha256=planned['archive_sha256'],phase=planned['phase'])
            model['ordinary'].append(actual)
    summaries=[(n,v) for n,v in payloads.items() if n.startswith(prefix+'jrnl/faults/') and n.endswith('/summary.json')]
    require(len(summaries)==1,'missing/ambiguous actual source fault matrix')
    name,summary=summaries[0]
    require(summary['phase']=='final-archive' and len(summary['faults'])==3,'wrong-phase/incomplete actual source faults')
    for fault in summary['faults']:
        require(fault['original_sha256']==fault['restored_sha256']==provenance['files'][fault['source']] and fault['restored_exact'],'missing exact actual fault restoration')
        outcomes=[]
        for outcome in fault['outcomes']:
            relative=outcome['report'].removeprefix('artifacts/'+NAME+'/')
            report=get(relative);require(digest(relative)==outcome['report_sha256'],'source fault report changed')
            launch=command(outcome['attempt'])
            expected_source=dict(provenance['files'])
            if outcome['phase']=='mutated':expected_source[fault['source']]=fault['mutated_sha256']
            require(launch['source']==expected_source,'actual source mutation/restoration not bound to named invocation')
            actual=normalize(report);actual.update(phase=outcome['phase'],expected_category=next(f['category'] for f in json.loads((DOC/'jrnl/fault-declaration.json').read_text())['faults'] if f['id']==fault['id']))
            outcomes.append(actual)
        model['faults'].append(dict(id=fault['id'],restored_exact=True,outcomes=outcomes))
    return model,index


def validate(model):
    require(model['project']=='jrnl' and model['host'] in {'linux','windows'},'missing/canonical native project identity')
    require(model['cleanup']['removed'] and model['cleanup']['source_restored'] and model['cleanup']['process_confirmed'],'unsafe/unconfirmed target cleanup')
    require(len(model['ordinary'])==240 and {r['case'] for r in model['ordinary']}==set(model['canonical_cases']),'partial ordinary native series')
    require(len(model['canonical_cases'])==20,'missing canonical scenarios')
    require(model['first_development_disposition_sha256']==sha256(DOC/'jrnl/first-development-disposition.json'),'missing original first-failure disposition')
    seen=set()
    def outcome(row,status):
        require(row['status']==status and row['cleaned'] and row['confirmed_exited'],'failed or unclean actual execution')
        require(row['invocation']==row['workspace'] and row['invocation'] not in seen,'cross-execution or duplicated report')
        seen.add(row['invocation'])
        if status=='passed':require(all(s['status']=='passed' for s in row['steps']),'missing positive step evidence')
        for step in row['steps']:
            if step['state']:require(step['state']['invocation_id']==row['invocation'] and step['state']['workspace_id']==row['workspace'],'state from another execution')
    for batch in range(12):
        rows=[r for r in model['ordinary'] if r['batch']==batch]
        require(len(rows)==20 and {r['case'] for r in rows}==set(model['canonical_cases']),'partial batch/duplicate case')
    for row in model['ordinary']:
        require(row['phase']=='final-archive' and row['runner_sha256']==model['runner_sha256'] and row['archive_sha256']==model['archive_sha256'],'wrong phase or mixed final candidate')
        outcome(row,'passed')
    require(len(model['faults'])==3 and {f['id'] for f in model['faults']}=={'F01','F02','F03'},'missing real source fault')
    for fault in model['faults']:
        require(fault['restored_exact'] and len(fault['outcomes'])==3 and {o['phase'] for o in fault['outcomes']}=={'baseline','mutated','restored'},'missing source restoration phase')
        for row in fault['outcomes']:
            outcome(row,'failed' if row['phase']=='mutated' else 'passed')
            if row['phase']=='mutated':
                require(row['category']==row['expected_category'],'wrong actual mutation rejection')
                if fault['id']=='F03':
                    index=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
                    require(all(s['status']=='passed' for s in row['steps'][:index]),'saved corruption failed before terminal/exit completion')
    return dict(ordinary=240,calibrations=9,cases=20,real_faults=3,native_cells=1)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--host',choices=['linux','windows'],required=True)
    parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    retained=RAW/'jrnl'/('retained-native-v'+str(args.generation))
    model,index=build_model(retained,args.run,args.host);counts=validate(model)
    destination=RAW/'jrnl/audits'/uuid.uuid4().hex;destination.mkdir(parents=True)
    immutable_json(destination/'actual-model.json',model)
    immutable_json(destination/'verified.json',dict(schema_version=1,run=args.run,host=args.host,
        actual_model_sha256=sha256(destination/'actual-model.json'),archive_sha256=index['archive_sha256'],
        index_sha256=sha256(retained/'index.json'),**counts,overall_project_admissions=0))
    print('Independently audited actual complete native jrnl cell:',args.host,counts,'Project admission still requires both cells and checked retention/removal.')


if __name__=='__main__':main()
