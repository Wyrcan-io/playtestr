"""Independent actual-packet audit of a complete frozen jrnl native cell."""
import argparse
import copy
import hashlib
import io
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
            bound=16*1024**2 if name.endswith('/retained-source/cleanup-inventory.json') else 4*1024**2
            require(row['bytes']<=bound,'audit JSON file bound')
            wanted.setdefault(row.get('member',name),[]).append(name)
    result={}
    with tarfile.open(retained/'packets.tar.gz','r|gz') as archive:
        for member in archive:
            if member.name not in wanted:continue
            bound=max(16*1024**2 if n.endswith('/retained-source/cleanup-inventory.json') else 4*1024**2 for n in wanted[member.name])
            require(member.isfile() and member.size<=bound,'unsafe actual JSON payload')
            data=archive.extractfile(member).read(bound+1)
            for name in wanted[member.name]:
                row=index['files'][name]
                require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'changed actual JSON payload')
                result[name]=json.loads(data.decode('utf-8-sig'))
    require(set(result)=={n for names in wanted.values() for n in names},'missing actual JSON payload')
    return result


def byte_payloads(retained,index):
    """Bounded non-JSON payloads for independently checking actual compiled code."""
    wanted={}
    for name,row in index['files'].items():
        if not name.endswith('.json'):
            require(row['bytes']<=16*1024**2,'audit binary/text file bound')
            wanted.setdefault(row.get('member',name),[]).append(name)
    result={};total=0
    with tarfile.open(retained/'packets.tar.gz','r|gz') as archive:
        for member in archive:
            if member.name not in wanted:continue
            require(member.isfile() and member.size<=16*1024**2,'unsafe actual code/cache payload')
            data=archive.extractfile(member).read(16*1024**2+1);total+=len(data)
            require(total<=64*1024**2,'compiled audit payload memory bound')
            for name in wanted[member.name]:
                row=index['files'][name]
                require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'changed actual code/cache payload')
                result[name]=data
    require(set(result)=={n for names in wanted.values() for n in names},'missing actual code/cache payload')
    return result


@lru_cache(maxsize=128)
def source_hashes(revision,name):
    blob=subprocess.check_output(['git','show',revision+':'+name])
    return {hashlib.sha256(blob).hexdigest(),hashlib.sha256(blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()}


def build_model(retained,run,host,project='jrnl'):
    index=json.loads((retained/'index.json').read_text(encoding='utf-8'))
    require(sha256(retained/'packets.tar.gz')==index['archive_sha256'],'retained native archive changed')
    verify(retained/'packets.tar.gz',index['files'])
    payloads=json_payloads(retained,index)
    copied=project=='yo'
    node=project in {'cz-cli','yo'}
    binary_payloads=byte_payloads(retained,index) if node else {}
    artifact='next20-'+project+'-'+('Windows' if host=='windows' else 'Linux')
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
    declaration=json.loads((DOC/project/'final-series-declaration.json').read_text())
    canonical=json.loads((DOC/project/'scenarios.json').read_text())
    provenance=json.loads((DOC/project/'source-provenance.json').read_text())
    def path(relative):return prefix+relative
    def get(relative):
        name=path(relative);require(name in payloads,'actual packet JSON omitted: '+relative)
        return payloads[name]
    def digest(relative):return index['files'][path(relative)]['sha256']
    def raw(relative):
        if relative is None:return binary_payloads
        require(path(relative) in binary_payloads,'actual Node bytes omitted: '+relative)
        return binary_payloads[path(relative)]
    def command(eid,compiler=False):
        events={event:get('events/'+eid+'-'+event+'.json') for event in ['started','identified','launched','finished']}
        require(all(e['campaign']==NAME and e['id']==eid for e in events.values()),'cross-campaign command identity')
        started=events['started'];finish=events['finished']
        require(started['ci_run_id']==run and finish['category']=='passed' and finish['harness_cleanup']=='harness_process_reaped','failed/incomplete actual command')
        if node:require(digest(project+'/'+eid+'/console.log')==finish['console_sha256'],'actual Node execution console changed')
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
        ordinary=started['label'].startswith('final-batch-')
        helpers=(['next20_cz_cli_rebuild.py','next20_compiled_payloads.py'] if started['label'].startswith('source-fault-compile-') else ['next20_cz_cli_build.py','next20_compiled_payloads.py']) if compiler else ((['next20_jrnl_final.py'] if ordinary else ['next20_jrnl_faults.py']) if project=='jrnl' else (['next20_final.py','next20_jrnl_final.py'] if ordinary else ['next20_python_faults.py']))
        if copied and not ordinary:helpers=helpers+['next20_yo_assemble.py']
        for name in helpers:
            helper='scripts/acceptance/'+name
            require(base['files'].get(helper) in source_hashes(revision,helper),'stale actual ordinary/fault execution helper')
        if not compiler:require(base['files'].get('artifacts/'+NAME+'/candidate/'+host+'/playtestr'+('.exe' if host=='windows' else ''))==expected['binary_sha256'],'actual launched runner executable mismatch')
        actual_source={name.split('/src/',1)[1]:value for name,value in target['files'].items() if '/active/'+project+'/src/' in name}
        require(set(actual_source)==set(provenance['files']),'actual target source identity coverage incomplete')
        require(target['files'].get('artifacts/'+NAME+'/active/'+project+'/task-owned.json')==digest(project+'/retained-source/task-owned.json'),'retained source ownership not bound at actual launch')
        return dict(events=events,base=base,target=target,source=actual_source)
    runtime=get(project+'/retained-source/runtime.json')
    inventory=get(project+'/retained-source/installed-inventory.json')
    cleanup=get(project+'/retained-source/cleanup-inventory.json')
    removed=get(project+'/retained-source/removed.json')
    owner=get(project+'/retained-source/task-owned.json')
    process=get(project+'/process-proof.json')
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
    core_operation('native-'+project+'-source-runtime-removal','scripts/acceptance/'+('next20_remove_target.ps1' if host=='windows' else 'next20_target_cleanup.py'))
    if host=='windows':core_operation('native-'+project+'-owned-process-proof','scripts/acceptance/next20_target_process_proof.ps1')
    require(owner['pin']==provenance['pin'] and owner['campaign']==NAME and owner['slug']==project,'wrong actual target ownership/pin')
    pure=PureWindowsPath if host=='windows' else PurePosixPath
    expected_target=str(pure(owner['workspace'])/'artifacts'/NAME/'active'/project)
    require(pure(cleanup['owned_target'])==pure(expected_target)==pure(process['owned_target']),'unsafe or mismatched cleanup root')
    require(pure(owner['workspace']).name=='playtestr','unexpected native checkout ownership root')
    require(process['confirmed_no_matching_live_processes'] and not process['matching_live_processes'],'unconfirmed native process termination')
    require(removed['removed'] and removed['owned_relative_path']=='active/'+project and removed['source_restored_exact'] and cleanup['source_restored_exact'],'missing exact restored source/runtime removal')
    require(removed['cleanup_inventory_sha256']==digest(project+'/retained-source/cleanup-inventory.json'),'cleanup inventory changed')
    require(cleanup['process_proof_sha256']==digest(project+'/process-proof.json'),'native process proof changed')
    require(cleanup['actual_reports_with_confirmed_cleanup']==240+declaration['calibration_required']//len(declaration['hosts']),'target cleanup did not account for all actual final reports')
    for name,target in cleanup['owned_links'].items():
        require(host=='linux' and name in {'venv/lib64','venv-pair-0/lib64','venv-pair-1/lib64'} and target=='lib','unsafe runtime cleanup link')
    acquisition=get(project+'/retained-source/acquisition.json')
    require(acquisition['source_files']==provenance['files'],'retained source provenance differs')
    require(digest(project+'/retained-source/source.tar.gz')==acquisition['archive_sha256'],'retained canonical source archive changed')
    wheels={} if node else get(project+'/retained-source/wheels.json')
    for name,row in wheels.items():require(digest(project+'/retained-source/wheels/'+name)==row['sha256'],'missing/changed retained actual dependency wheel')
    if project=='commitizen-python':
        # Check foreign-platform wheel hashes against the already-reviewed full
        # primary release inventories, independently of native self-receipts.
        review=json.loads((DOC/project/'source-review.json').read_text())
        local=RAW/project/'retained-source'
        if not local.exists():local=RAW/'active'/project
        approved={}
        for dependency in review['dependencies']:
            primary=local/'dependency-review/primary'/(dependency['wheel']+'.json')
            require(primary.is_file() and sha256(primary)==dependency['primary_metadata_sha256'],'reviewed primary dependency inventory missing/changed')
            metadata=json.loads(primary.read_text(encoding='utf-8'))
            for distribution in metadata['urls']:
                if distribution['packagetype']=='bdist_wheel':
                    approved[distribution['filename']]=(distribution['digests']['sha256'],distribution['url'])
        require(len(wheels)==len(review['dependencies']),'native dependency set differs from reviewed project')
        for name,row in wheels.items():
            require(approved.get(name)==(row['sha256'],row['url']),'native wheel absent from independently reviewed primary release')
    require(runtime['installed_inventory_sha256']==digest(project+'/retained-source/installed-inventory.json'),'retained runtime dependency identity mismatch')
    execution_files=inventory['files']
    if node:
        from next20_verify_node import dependencies,compiled_payloads,host_contract
        if copied:
            from next20_verify_yo import dependencies,host_contract
        reconstructed=dependencies(get,raw,digest,host,provenance)
        build=get(project+'/retained-source/build.json')
        require(build['pin']==runtime['source_pin']==provenance['pin'] and build['runtime_sha256']==digest(project+'/retained-source/runtime.json'),'compiled target pin/runtime binding differs')
        require(build['source_inputs']==(provenance['files'] if copied else {n:v for n,v in provenance['files'].items() if n.startswith('src/')}),'initial assembled source inputs differ')
        names={'dist/'+n.removeprefix('src/') for n in provenance['files'] if n.startswith('src/') and n.endswith('.js')}
        if copied:
            require(build['mode']=='copied-interpreted-source' and build['compiled_files']=={},'yo falsely claims compiled modules')
            require(build['copied_source_files']=={n:'app/'+n for n in provenance['files'] if n.startswith('lib/')},'yo original source copy mapping differs')
        else:compiled_payloads(build,raw,names)
        execution_files={**inventory['files'],**build['compiled_files']}
        prerequisite=get(project+'/retained-source/node-prerequisite.json')
        require(runtime['kind']=='node' and runtime['node_sha256']==prerequisite['node_sha256']==prerequisite['base_node_sha256'],'owned Node prerequisite copy differs')
        require(runtime['prerequisite_sha256']==digest(project+'/retained-source/node-prerequisite.json') and int(prerequisite['version'].lstrip('v').split('.')[0])>=18,'Node prerequisite/version unbound')
        require(not cleanup['owned_links'],'unexpected Node runtime links')
        restored_source={n.removeprefix('src/'):v['sha256'] for n,v in cleanup['files'].items() if n.startswith('src/')}
        require(restored_source==provenance['files'],'actual cleanup source bytes not restored')
        for scope,files in reconstructed.items():
            folder=(runtime['app_relative_path']+'/'+scope) if copied else (runtime['app_relative_path'] if scope=='app' else scope)
            for name,value in files.items():require(cleanup['files'][folder+'/'+name]['sha256']==value,'Node compiler/runtime package changed before cleanup')
        require(cleanup['files']['node/'+('node.exe' if host=='windows' else 'node')]['sha256']==runtime['node_sha256'],'owned Node executable changed before cleanup')
        def runner_plan(planned,spec_relative,report_relative,evidence_relative,expected_exit):
            argv=planned['command']
            require(len(argv)==7 and argv[1]=='test' and argv[2]=='--report' and argv[4]=='--artifacts-dir','undeclared Node runner command flags')
            expected_runner=pure(owner['workspace'])/'artifacts'/NAME/'candidate'/host/('playtestr.exe' if host=='windows' else 'playtestr')
            require(pure(argv[0])==expected_runner and pure(planned['cwd'])==pure(owner['workspace']),'Node runner executable/cwd plan differs')
            for actual,wanted in [(argv[3],report_relative),(argv[5],evidence_relative),(argv[6],spec_relative)]:
                require(pure(actual)==pure('artifacts/'+NAME+'/'+wanted),'Node runner report/evidence/spec command differs')
            require(planned['expected_runner_exit']==expected_exit,'Node runner expected exit plan differs')
            require(planned['spec_sha256']==digest(spec_relative),'Node runner command planned another spec hash')
        def check_build(proof,receipt_relative,expected_source,initial=False):
            planned_relative=posixpath.dirname(receipt_relative)+('/build-planned.json' if initial else '/planned.json')
            planned=get(planned_relative)
            require(proof['planned_sha256']==digest(planned_relative),'changed compiled build command plan')
            require(planned['source_inputs']==expected_source,'compiler planned source differs')
            launch=command(proof['attempt'],compiler=True)
            require(launch['source']==expected_source,'compiler did not launch with declared actual source')
            root=pure(expected_target);builder=root/'build-toolchain';app=root/runtime['app_relative_path']
            expected_command=[runtime['node'],str(builder/'node_modules/@babel/cli/bin/babel.js'),str(root/'src'/'src'),'--out-dir',str(app/'dist'),'--config-file',str(builder/'babel.config.js'),'--no-babelrc']
            require(planned['command']==expected_command and pure(planned['cwd'])==builder,'undeclared actual Node compiler command')
            require(planned['node_sha256']==runtime['node_sha256'] and planned['babel_cli_sha256']==reconstructed['build-toolchain']['node_modules/@babel/cli/bin/babel.js'] and planned['build_config_sha256']==provenance['files']['babel.config.js'],'compiler executable/config hash differs')
            require(launch['base']['files'].get(str(pure(runtime['node']).relative_to(pure(owner['workspace']))).replace('\\','/'))==runtime['node_sha256'],'compiler actual Node executable unbound')
            compiled_payloads(proof,raw,names)
            require('Successfully compiled' in raw('cz-cli/'+proof['attempt']+'/console.log').decode('utf-8'),'compiler lacks positive complete output')
            return launch
        if not copied:check_build(build,project+'/retained-source/build.json',provenance['files'],initial=True)
    host_cases=get(project+'/host-contracts/scenarios.json')['cases']
    native_python=str(pure(runtime['node' if node else 'python']).relative_to(pure(owner['workspace']))).replace('\\','/')
    for case in canonical['cases']:
        native_base=get(project+'/host-contracts/'+case['spec'])
        reviewed=json.loads((DOC/project/case['spec']).read_text(encoding='utf-8'))
        reviewed['command'][0]=posixpath.relpath(native_python,'artifacts/'+NAME+'/'+project+'/host-contracts')
        if node:reviewed=host_contract(reviewed,runtime,host)
        if project=='jrnl' and host=='linux' and case['id']=='N06':
            position=next(i for i,s in enumerate(reviewed['steps']) if s.get('key')=='CtrlZ')
            require(reviewed['steps'][position+1]=={'key':'Enter'},'canonical EOF group changed')
            reviewed['steps']=reviewed['steps'][:position]+[{'key':'CtrlD'}]+reviewed['steps'][position+2:]
        if project=='commitizen-python' and host=='linux':
            reviewed['env']['PATH']='/usr/bin:/bin';reviewed['env']['GIT_CONFIG_GLOBAL']='/dev/null'
        require(native_base==reviewed,'native base silently changed canonical semantics/oracles')
        declared=next(c for c in host_cases if c['id']==case['id'])
        require(declared['canonical_sha256']==case['spec_sha256'] and declared['spec_sha256']==digest(project+'/host-contracts/'+case['spec']),'stale canonical/native base contract binding')
    model=dict(project=project,host=host,run=run,revision=revision,provider_job=jobs[0]['databaseId'],
        runner_sha256=expected['binary_sha256'],archive_sha256=expected['archive_sha256'],ordinary=[],faults=[],
        cleanup=dict(removed=True,source_restored=True,target_root=expected_target,process_confirmed=True),
        canonical_cases=[c['id'] for c in canonical['cases']],first_development_disposition_sha256=sha256(DOC/project/'first-development-disposition.json'))
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
    def states_match(actual,contract):
        if not node:return
        for observed,expected_step in zip(actual['steps'],contract['steps']):
            if 'state' not in expected_step:continue
            state=observed['state'];expected_state=expected_step['state']
            if observed['status']=='not_run':require(state is None,'unexecuted state has evidence');continue
            require(state is not None and state['path']==expected_state['path'] and state['kind']==expected_state['kind'],'state evidence differs from declared predicate')
            require(state['outcome']==('matched' if observed['status']=='passed' else 'rejected'),'state predicate evidence outcome differs')
    for batch in range(12):
        summary=get(f'{project}/final-series/{batch}/summary.json');prepared=get(f'{project}/final-series/{batch}/prepared.json')
        catalog=get(f'{project}/final-series/{batch}/runtime-catalog.json')
        require(catalog['files']==execution_files,'actual executed runtime dependency bytes differ')
        actual_executable=prepared['actual_executable' if node else 'actual_python']
        require(catalog['executable']==actual_executable and catalog['executable_sha256']==runtime['node_sha256' if node else 'python_sha256'],'wrong copied/normal interpreter')
        require(prepared['actual_runtime_catalog_sha256']==digest(f'{project}/final-series/{batch}/runtime-catalog.json'),'stale actual runtime catalog')
        runtime_relative=catalog['runtime_root'].split('/active/'+project+'/',1)[1]
        for name,value in catalog['files'].items():
            require(cleanup['files'][runtime_relative+'/'+name]['sha256']==value,'runtime changed between actual launch and cleanup')
        require(len(summary['observations'])==20 and summary['batch']==batch,'partial native batch summary')
        if node:require(prepared['declaration_sha256']==sha256(DOC/project/'final-series-declaration.json') and prepared['runtime_kind']=='node','Node series declaration/runtime kind changed')
        package=f'{project}/final-series/{batch}/'+('relocated café 雪' if batch==5 else 'contracts')
        for observation in summary['observations']:
            cid=observation['case'];case=next(c for c in canonical['cases'] if c['id']==cid)
            planned=get(f'{project}/final-series/{batch}/{cid}.planned.json')
            spec=get(package+'/'+case['spec'])
            report=get(f'{project}/final-series/{batch}/{cid}.report.json')
            require(digest(package+'/'+case['spec'])==planned['spec_sha256']==observation['spec_sha256'],'actual executed spec mismatch')
            require(digest(f'{project}/final-series/{batch}/{cid}.report.json')==observation['report_sha256'],'actual report reference changed')
            launch=command(observation['attempt'])
            require(launch['events']['started']['phase']=='final-archive','wrong-phase ordinary execution')
            require(launch['source']==provenance['files'],'ordinary run used mutated/wrong target source')
            require(launch['base']['files'].get(planned['spec'])==planned['spec_sha256'],'prelaunch actual contract identity missing')
            require(launch['base']['files'].get(actual_executable)==runtime['node_sha256' if node else 'python_sha256'],'actual target executable not bound at launch')
            require(launch['target']['files'].get('artifacts/'+NAME+'/active/'+project+'/launch-runtime-catalog.json')==prepared['actual_runtime_catalog_sha256'],'actual runtime catalog missing from prelaunch identity')
            actual=normalize(report)
            require(actual['invocation']==observation['invocation'],'observed report from another invocation')
            require(len(actual['steps'])==len(spec['steps']) and [s['action'] for s in actual['steps']]==[next(iter(s)) for s in spec['steps']],'actual positive step sequence differs')
            # Fixture and approved expectation data stay exact on every variant.
            native_base=get(project+'/host-contracts/'+case['spec'])
            expected_spec=copy.deepcopy(native_base)
            expected_spec['command'][0]=posixpath.relpath(actual_executable,posixpath.dirname(planned['spec']))
            if node:
                expected_runtime=('app-pair-'+str(batch//2)) if batch<4 else runtime['app_relative_path']
                require(runtime_relative==expected_runtime,'wrong declared cold/warm Node runtime copy')
                expected_spec['command'][2]=expected_spec['command'][2].replace('../'+runtime['app_relative_path']+'/'+runtime['entrypoint'],'../'+expected_runtime+'/'+runtime['entrypoint'])
                require(planned['schema_version']==2,'Node ordinary command plan missing')
                runner_plan(planned,package+'/'+case['spec'],f'{project}/final-series/{batch}/{cid}.report.json',f'{project}/final-series/{batch}/evidence',0)
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
            states_match(actual,spec)
            frozen=json.loads((DOC/project/'development-test-freeze.json').read_text())
            fixture_prefix='artifacts/'+NAME+'/'+package+'/'+case['initial_fixture']
            expected_files={'artifacts/'+NAME+'/'+package+'/'+name:value for name,value in frozen['inputs'].items() if name.startswith(case['initial_fixture']+'/')}
            observed_files={name:value for name,value in launch['base']['files'].items() if name.startswith(fixture_prefix+'/')}
            require(observed_files==expected_files,'actual prelaunch fixture has missing/extra/changed input files')
            expected_dirs={'artifacts/'+NAME+'/'+package+'/'+name for name in frozen['directories'] if name==case['initial_fixture'] or name.startswith(case['initial_fixture']+'/')}
            observed_dirs={name.replace('\\','/') for name in launch['base']['fixture_directories'] if name.replace('\\','/')==fixture_prefix or name.replace('\\','/').startswith(fixture_prefix+'/')}
            require(observed_dirs==expected_dirs,'actual prelaunch empty fixture directory proof differs')
            for name,value in frozen['inputs'].items():
                if name.startswith(case['initial_fixture']+'/') or name.startswith('snapshots/') and any(s.get('snapshot')==name.removeprefix('snapshots/') for s in spec['steps']):
                    if copied and host=='linux' and name=='snapshots/javascript-complete.txt':
                        canonical_screen=(DOC/project/name).read_bytes()
                        require(hashlib.sha256(canonical_screen).hexdigest()==value and canonical_screen.count(b'create output\\project.json')==1,'yo original reviewed screen changed')
                        value=hashlib.sha256(canonical_screen.replace(b'create output\\project.json',b'create output/project.json')).hexdigest()
                    require(digest(package+'/'+name)==value,'actual fixture/snapshot byte mismatch')
                    require(launch['base']['files'].get('artifacts/'+NAME+'/'+package+'/'+name)==value,'actual prelaunch fixture/snapshot not bound')
            actual.update(batch=batch,case=cid,spec_sha256=planned['spec_sha256'],runner_sha256=planned['runner_sha256'],
                archive_sha256=planned['archive_sha256'],phase=planned['phase'])
            model['ordinary'].append(actual)
    summaries=[(n,v) for n,v in payloads.items() if n.startswith(prefix+project+'/faults/') and n.endswith('/summary.json')]
    require(len(summaries)==1,'missing/ambiguous actual source fault matrix')
    name,summary=summaries[0]
    require(summary['phase']=='final-archive' and len(summary['faults'])==3,'wrong-phase/incomplete actual source faults')
    for fault in summary['faults']:
        require(fault['original_sha256']==fault['restored_sha256']==provenance['files'][fault['source']] and fault['restored_exact'],'missing exact actual fault restoration')
        declared_fault=next(f for f in json.loads((DOC/project/'fault-declaration.json').read_text())['faults'] if f['id']==fault['id'])
        reference=path(project+'/retained-source/source.tar.gz');source_row=index['files'][reference]
        with tarfile.open(retained/'packets.tar.gz','r:gz') as bundle:
            source_bytes=bundle.extractfile(source_row.get('member',reference)).read(8*1024**2+1)
        require(len(source_bytes)<=8*1024**2 and hashlib.sha256(source_bytes).hexdigest()==source_row['sha256'],'canonical source archive bound/hash mismatch')
        original=None;entries=expanded=0
        with tarfile.open(fileobj=io.BytesIO(source_bytes),mode='r:gz') as source_tar:
            for member in source_tar:
                entries+=1;expanded+=member.size
                require(entries<=10000 and expanded<=64*1024**2,'canonical source archive expansion bound')
                if member.isfile() and member.name.endswith('/'+fault['source']):
                    require(original is None and member.size<=4*1024**2,'ambiguous/oversized declared fault source')
                    original=source_tar.extractfile(member).read(4*1024**2+1)
        require(original is not None and hashlib.sha256(original).hexdigest()==provenance['files'][fault['source']],'actual declared mutation source not canonical')
        before=declared_fault['before'].encode();after=declared_fault['after'].encode()
        require(original.count(before)==1 and hashlib.sha256(original.replace(before,after)).hexdigest()==fault['mutated_sha256'],'actual source mutation differs from declared real fault')
        outcomes=[]
        for outcome in fault['outcomes']:
            relative=outcome['report'].removeprefix('artifacts/'+NAME+'/')
            report=get(relative);require(digest(relative)==outcome['report_sha256'],'source fault report changed')
            launch=command(outcome['attempt'])
            expected_source=dict(provenance['files'])
            if outcome['phase'] in {'mutated','terminal-only'}:expected_source[fault['source']]=fault['mutated_sha256']
            require(launch['source']==expected_source,'actual source mutation/restoration not bound to named invocation')
            if node and not copied:
                proof=outcome['compiled_build'];receipt=proof['compiled_receipt'].removeprefix('artifacts/'+NAME+'/')
                require(digest(receipt)==proof['compiled_receipt_sha256'],'compiled source fault receipt changed')
                compiled=get(receipt)
                require(compiled['source_inputs']==expected_source and compiled['compiled_files']==proof['compiled_files'] and compiled['compiled_payloads']==proof['compiled_payloads'],'compiled source fault proof differs')
                check_build(compiled,receipt,expected_source)
                if outcome['phase'] in {'baseline','restored'}:require(compiled['compiled_files']==build['compiled_files'],'source restoration failed to restore actual compiled bytes')
                catalog_relative=outcome['runtime_catalog'].removeprefix('artifacts/'+NAME+'/')
                catalog=get(catalog_relative)
                require(digest(catalog_relative)==outcome['actual_runtime_catalog_sha256']==proof['catalog_sha256'],'actual compiled calibration catalog changed')
                require(compiled['actual_runtime_catalog_sha256']==proof['catalog_sha256'] and compiled['runtime_catalog']==proof['catalog_path'],'compiler output/catalog receipt differs')
                require(catalog['files']=={**inventory['files'],**compiled['compiled_files']} and catalog['executable']==native_python and catalog['executable_sha256']==runtime['node_sha256'],'actual compiled calibration dependency/executable set differs')
                require(launch['target']['files'].get('artifacts/'+NAME+'/active/'+project+'/launch-runtime-catalog.json')==digest(catalog_relative),'actual compiled calibration catalog absent at launch')
                planned_relative=posixpath.dirname(relative)+'/'+fault['id']+'-'+outcome['phase']+'-planned.json'
                require(digest(planned_relative)==outcome['planned_sha256'] and get(planned_relative)['compiled_build']==proof,'compiled calibration command plan differs')
            if copied:
                from next20_verify_yo import assembly
                proof=outcome['source_assembly']
                expected_files=assembly(proof,get,raw,digest,expected_source,inventory['files'])
                catalog_relative=outcome['runtime_catalog'].removeprefix('artifacts/'+NAME+'/')
                catalog=get(catalog_relative)
                require(digest(catalog_relative)==outcome['actual_runtime_catalog_sha256']==proof['catalog_sha256'],'yo actual source-copy catalog changed')
                require(catalog['files']==expected_files and catalog['executable']==native_python and catalog['executable_sha256']==runtime['node_sha256'],'yo actual interpreted source/dependency/executable catalog differs')
                require(launch['target']['files'].get('artifacts/'+NAME+'/active/'+project+'/launch-runtime-catalog.json')==digest(catalog_relative),'yo source-copy catalog absent at actual launch')
                planned_relative=posixpath.dirname(relative)+'/'+fault['id']+'-'+outcome['phase']+'-planned.json'
                require(digest(planned_relative)==outcome['planned_sha256'] and get(planned_relative)['source_assembly']==proof,'yo calibration command plan differs')
            primary=json.loads((DOC/project/'fault-declaration.json').read_text()).get('primary_spec','normal-delete.json')
            selected=project+'/host-contracts/'+primary
            expected_contract=get(selected)
            if outcome['phase']=='terminal-only':
                require(project!='jrnl' and declared_fault.get('terminal_only_probe'),'undeclared terminal-only calibration')
                derived=posixpath.dirname(relative)+'/terminal-only';actual_spec=get(derived+'/spec.json')
                expected_spec=copy.deepcopy(get(project+'/host-contracts/'+json.loads((DOC/project/'fault-declaration.json').read_text())['primary_spec']))
                fixture=expected_spec['workspace']['fixture'];expected_spec['workspace']['fixture']='fixture'
                expected_spec['command'][0]=posixpath.relpath(native_python,'artifacts/'+NAME+'/'+derived)
                expected_spec['steps']=[s for s in expected_spec['steps'] if 'state' not in s]
                require(actual_spec==expected_spec and digest(derived+'/spec.json')==outcome['spec_sha256'],'terminal-only contract changed more than declared state omission/path rebinding')
                require(launch['base']['files'].get('artifacts/'+NAME+'/'+derived+'/spec.json')==outcome['spec_sha256'],'terminal-only contract not bound at launch')
                frozen=get(project+'/host-contracts/development-test-freeze.json')
                for name,value in frozen['inputs'].items():
                    if name.startswith(fixture+'/'):require(digest(derived+'/fixture/'+name.removeprefix(fixture+'/'))==value,'terminal-only fixture differs from approved real input')
                selected=derived+'/spec.json';expected_contract=actual_spec
            require(launch['base']['files'].get('artifacts/'+NAME+'/'+selected)==digest(selected),'actual calibration did not launch the unchanged declared contract')
            if node:
                runner_plan(get(planned_relative),selected,relative,relative.removesuffix('.json')+'-evidence',1 if outcome['phase']=='mutated' else 0)
            report_spec=pure(report['results'][0]['spec_path'])
            logical=str(report_spec.relative_to(pure(owner['workspace']))) if report_spec.is_absolute() else str(report_spec)
            require(logical.replace('\\','/')=='artifacts/'+NAME+'/'+selected,'calibration report belongs to another contract')
            actual=normalize(report);actual.update(phase=outcome['phase'],expected_category=next(f['category'] for f in json.loads((DOC/project/'fault-declaration.json').read_text())['faults'] if f['id']==fault['id']))
            require([s['action'] for s in actual['steps']]==[next(iter(s)) for s in expected_contract['steps']],'actual calibration step sequence differs')
            states_match(actual,expected_contract)
            outcomes.append(actual)
        model['faults'].append(dict(id=fault['id'],restored_exact=True,outcomes=outcomes))
    return model,index


def validate(model):
    project=model['project']
    require(project in {'jrnl','commitizen-python','cz-cli','yo'} and model['host'] in {'linux','windows'},'missing/canonical native project identity')
    require(model['cleanup']['removed'] and model['cleanup']['source_restored'] and model['cleanup']['process_confirmed'],'unsafe/unconfirmed target cleanup')
    pure=PureWindowsPath if model['host']=='windows' else PurePosixPath
    require(tuple(pure(model['cleanup']['target_root']).parts[-4:])==('artifacts',NAME,'active',project),'unsafe actual target removal root')
    require(len(model['ordinary'])==240 and {r['case'] for r in model['ordinary']}==set(model['canonical_cases']),'partial ordinary native series')
    require(len(model['canonical_cases'])==20,'missing canonical scenarios')
    require(model['first_development_disposition_sha256']==sha256(DOC/project/'first-development-disposition.json'),'missing original first-failure disposition')
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
        cases=json.loads((DOC/project/'scenarios.json').read_text())['cases']
        case=next(c for c in cases if c['id']==row['case']);steps=json.loads((DOC/project/case['spec']).read_text())['steps']
        if project=='jrnl' and model['host']=='linux' and row['case']=='N06':
            position=next(i for i,s in enumerate(steps) if s.get('key')=='CtrlZ')
            require(steps[position+1]=={'key':'Enter'},'canonical EOF group changed')
            steps=steps[:position]+[{'key':'CtrlD'}]+steps[position+2:]
        if row['batch']==7:
            expanded=[]
            for step in steps:
                count=(len(step['text'])+2)//3 if set(step)=={'text'} and len(step['text'])>1 and all(ord(c)>=32 and ord(c)!=127 for c in step['text']) else 1
                expanded.extend([step]*count)
            steps=expanded
        require([s['action'] for s in row['steps']]==[next(iter(s)) for s in steps],'missing/changed positive action sequence')
    require(len(model['faults'])==3 and {f['id'] for f in model['faults']}=={'F01','F02','F03'},'missing real source fault')
    for fault in model['faults']:
        phases={'baseline','mutated','restored'}
        if project in {'commitizen-python','cz-cli','yo'} and fault['id']=='F03':phases.add('terminal-only')
        require(fault['restored_exact'] and len(fault['outcomes'])==len(phases) and {o['phase'] for o in fault['outcomes']}==phases,'missing source restoration phase')
        for row in fault['outcomes']:
            outcome(row,'failed' if row['phase']=='mutated' else 'passed')
            if row['phase']=='mutated':
                require(row['category']==row['expected_category'],'wrong actual mutation rejection')
                if fault['id']=='F03':
                    index=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
                    require(all(s['status']=='passed' for s in row['steps'][:index]),'saved corruption failed before terminal/exit completion')
    return dict(ordinary=240,calibrations=10 if project in {'commitizen-python','cz-cli','yo'} else 9,cases=20,real_faults=3,native_cells=1)


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
