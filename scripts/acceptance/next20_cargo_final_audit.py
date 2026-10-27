"""Independent readback of actual native Cargo final reports and launch identities.

This cell audit is deliberately separate from campaign admission/retention gates.
"""
import argparse
import copy
import hashlib
import json
import posixpath
from pathlib import Path
import subprocess
import uuid

from next20_check import RAW,ROOT,DOC,NAME
from readiness_evidence import immutable_json,sha256


def audit(root,host,revision,run=None):
    prefix='artifacts/'+NAME+'/';package=DOC/'cargo-generate';project=root/'cargo-generate'
    retained=None
    def local_records():
        nonlocal retained
        if retained is None:
            from next20_local_records import read_packet
            _,retained=read_packet('cargo-generate')
        return retained
    def read(path):
        if path.is_file():return path.read_bytes()
        if root!=RAW:raise FileNotFoundError(path)
        name=path.relative_to(RAW).as_posix()
        records=local_records()
        if name not in records:raise FileNotFoundError('required actual logical evidence missing: '+name)
        return records[name]
    def sha256(path):return hashlib.sha256(read(path)).hexdigest()
    def document(path):return json.loads(read(path).decode('utf-8-sig'))
    def available(path):
        if path.is_file():return True
        return root==RAW and path.relative_to(RAW).as_posix() in local_records()
    def files_under(directory):
        paths={p for p in directory.rglob('*') if p.is_file()}
        if root==RAW and (project/'retained-local-v1/index.json').is_file():
            selected=directory.relative_to(RAW).as_posix()+'/'
            paths.update(RAW/name for name in local_records() if name.startswith(selected))
        return sorted(paths)
    def located(name):
        name=name.replace('\\','/')
        if name.startswith(prefix):name=name[len(prefix):]
        path=root/name;path.resolve().relative_to(root.resolve())
        return path
    def manifest(reference):
        path=located(reference['manifest'])
        if sha256(path)!=reference['sha256']:raise ValueError('actual identity manifest changed')
        return document(path)
    candidates=document(DOC/'replacement-candidate-freeze-native-exit-v1.json')
    candidate=next(c for c in candidates['cells'] if c['host']==host)
    declaration_path=package/'final-series-declaration-native-exit-v1.json';declaration=document(declaration_path)
    freeze=document(package/'development-test-freeze.json');faults=document(package/'fault-declaration.json')
    for name,digest in freeze['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('canonical frozen contract changed')
    target=root/'active/cargo-generate'
    if not target.exists():target=project/'retained-source'
    build=document(target/'build.json');runtime=document(target/'runtime.json')
    if build['binary_sha256']!=runtime['native_sha256'] or runtime['kind']!='native' or build['runtime_kind']!='native' or build['features']!='default':raise ValueError('native actual build/runtime differs')
    profile=document(project/'host-contracts/scenarios.json');case_map={c['id']:c for c in profile['cases']}
    canonical=document(package/'scenarios.json');canonical_cases={c['id']:c for c in canonical['cases']}
    if len(case_map)!=20 or set(case_map)!=set(canonical_cases):raise ValueError('missing/duplicate canonical cases')
    if profile['native_binary_sha256']!=build['binary_sha256'] or profile['development_freeze_sha256']!=sha256(package/'development-test-freeze.json'):raise ValueError('native profile build/freeze changed')
    native_review=document(package/'native-linux-profile-review-v2.json') if host=='linux' else None
    spec_names={c['spec'] for c in case_map.values()}
    for case in case_map.values():
        original=canonical_cases[case['id']];expected=copy.deepcopy(document(package/original['spec']))
        actual=document(project/'host-contracts'/case['spec']);expected['command'][0]=actual['command'][0]
        if host=='linux':expected['env'].update(GIT_CONFIG_GLOBAL='/dev/null',**native_review['native_environment'])
        if 'native_exit_profile' in original:
            for step in expected['steps']:
                if 'exit' in step:step['exit']=original['native_exit_profile'][host]
        if actual!=expected or case['canonical_sha256']!=sha256(package/original['spec']):raise ValueError('native profile changes a canonical oracle/action')
    for name,digest in freeze['inputs'].items():
        if name in spec_names:continue
        if host=='linux' and name=='snapshots/normal-project.rows.json':digest=native_review['native_snapshot_sha256']
        if sha256(project/'host-contracts'/name)!=digest:raise ValueError('native profile fixture/snapshot changed')
    source_cache={}
    def source_hashes(name):
        if name not in source_cache:
            blob=subprocess.check_output(['git','show',revision+':'+name]);source_cache[name]={hashlib.sha256(blob).hexdigest(),hashlib.sha256(blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()}
        return source_cache[name]
    invocations=set();attempts=set()
    def command(eid,expected):
        if eid in attempts:raise ValueError('duplicate fresh execution identity')
        attempts.add(eid);events={}
        for event in ['started','identified','launched','finished']:
            row=document(root/'events'/(eid+'-'+event+'.json'))
            if row['event']!=event or row['id']!=eid or row['campaign']!=NAME or row['phase']!='final-archive' or row['project']!='cargo-generate':raise ValueError('wrong/missing original event phase/project')
            events[event]=row
        start=events['started'];finish=events['finished']
        if start['ci_run_id']!=run or finish['exit_code']!=expected or finish['cleanup_errors'] or finish['harness_cleanup']!='harness_process_reaped':raise ValueError('actual command outcome/provider/cleanup differs')
        if sha256(project/eid/'console.log')!=finish['console_sha256']:raise ValueError('actual console changed')
        wrapper=manifest(events['identified']['identity']);base=wrapper
        while 'base' in base:base=manifest(base['base'])
        runner=prefix+'candidate-native-exit-v1/'+host+'/playtestr'+('.exe' if host=='windows' else '')
        if base['files'].get(runner)!=candidate['binary_sha256']:raise ValueError('actually launched Playtestr executable differs from frozen archive')
        for helper in ['next20_cargo_final_ordinary.py','next20_jrnl_final.py','next20_cargo_faults.py','next20_check.py','adversarial_process.py','readiness_evidence.py']:
            name='scripts/acceptance/'+helper
            if base['files'].get(name) not in source_hashes(name):raise ValueError('actual final helper source differs: '+helper)
        return wrapper,base
    def report(path,expected,category=None):
        data=document(path)
        if data['runner_version']!='v0.4.0-rc.6' or data['os']!=host or data['arch']!='amd64' or len(data['results'])!=1:raise ValueError('wrong actual runner/native report')
        row=data['results'][0];invocation=row['invocation_id']
        if invocation in invocations:raise ValueError('reused invocation across fresh executions')
        invocations.add(invocation)
        if row['status']!=expected or row.get('failure',{}).get('category')!=category or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('native outcome/target/workspace cleanup differs')
        if expected=='passed' and not all(s['status']=='passed' for s in row['steps']):raise ValueError('missing positive evidence')
        for step in row['steps']:
            state=step.get('state')
            if state and (state['invocation_id']!=invocation or state['workspace_id']!=row['workspace']['id']):raise ValueError('state borrowed from another invocation/workspace')
        for name in row.get('evidence',{}).values():
            if isinstance(name,str) and not available(located(name)):raise ValueError('missing captured failure evidence')
        return row
    ordinary=[]
    for batch in range(12):
        folder=project/'final-series-native-exit-v1'/str(batch);summary=document(folder/'summary.json');prepared=document(folder/'prepared.json')
        if summary['phase']!='final-archive' or summary['batch']!=batch or summary['host']!=host or summary['ordinary_executions']!=20 or len(summary['observations'])!=20:raise ValueError('partial/wrong final series')
        if prepared['archive_sha256']!=candidate['archive_sha256'] or prepared['runner_sha256']!=candidate['binary_sha256'] or prepared['actual_executable_sha256']!=build['binary_sha256'] or prepared['declaration_sha256']!=sha256(declaration_path):raise ValueError('mixed candidate or native executable')
        changes={c['case']:c for c in prepared['changes']}
        seen=set()
        for observation in summary['observations']:
            case=observation['case']
            if case in seen or case not in case_map:raise ValueError('duplicate/missing case')
            seen.add(case);plan=document(folder/(case+'.planned.json'));spec=located(plan['spec']);row=report(folder/(case+'.report.json'),'passed')
            if sha256(folder/(case+'.report.json'))!=observation['report_sha256'] or sha256(spec)!=observation['spec_sha256'] or sha256(spec)!=plan['spec_sha256'] or row['invocation_id']!=observation['invocation']:raise ValueError('changed original report/contract')
            if plan['archive_sha256']!=candidate['archive_sha256'] or plan['runner_sha256']!=candidate['binary_sha256'] or plan['phase']!='final-archive':raise ValueError('planned archive/phase differs')
            base_path=project/'host-contracts'/case_map[case]['spec'];value=document(spec);expected=copy.deepcopy(document(base_path));expected['command'][0]=value['command'][0]
            if sha256(base_path)!=case_map[case]['spec_sha256'] or changes[case]['native_base_sha256']!=sha256(base_path) or changes[case]['executed_spec_sha256']!=sha256(spec):raise ValueError('changed native contract baseline')
            if batch==4:expected.update(width=expected['width']+10,height=expected['height']+2)
            if batch==7:
                steps=[]
                for step in expected['steps']:
                    if set(step)=={'text'} and len(step['text'])>1 and all(ord(c)>=32 and ord(c)!=127 for c in step['text']):steps.extend({'text':step['text'][o:o+3]} for o in range(0,len(step['text']),3))
                    else:steps.append(step)
                expected['steps']=steps
            if batch==10 and case=='N01':expected['height']=12
            if batch==11:expected['startup_timeout_ms']=declaration.get('startup_timeout_ms_by_host',{}).get(host,2000)
            if value!=expected:raise ValueError('undeclared final contract/oracle variation')
            wrapper,base=command(observation['attempt'],0)
            initial=value.get('workspace',{}).get('fixture')
            if initial:
                fixture=spec.parent/initial
                for initial_file in files_under(fixture):
                    name=initial_file.relative_to(spec.parent).as_posix();canonical_initial=project/'host-contracts'/name
                    key=prefix+initial_file.relative_to(root).as_posix()
                    if sha256(initial_file)!=sha256(canonical_initial) or base['files'].get(key)!=sha256(initial_file):raise ValueError('actual initial fixture differs from reviewed native fixture')
            for step in value['steps']:
                if isinstance(step.get('snapshot'),str):
                    snapshot=spec.parent/'snapshots'/step['snapshot'];key=prefix+snapshot.relative_to(root).as_posix()
                    if sha256(snapshot)!=sha256(project/'host-contracts/snapshots'/step['snapshot']) or base['files'].get(key)!=sha256(snapshot):raise ValueError('actually executed approved snapshot differs')
            catalog=manifest(wrapper['target_catalog'])
            runtime_catalog_path=folder/'runtime-catalog.json';runtime_catalog=document(runtime_catalog_path)
            if (sha256(runtime_catalog_path)!=prepared['actual_runtime_catalog_sha256'] or
                catalog['files'].get(prefix+'active/cargo-generate/launch-runtime-catalog.json')!=sha256(runtime_catalog_path) or
                runtime_catalog['executable']!=prepared['actual_executable'] or runtime_catalog['executable_sha256']!=build['binary_sha256']):raise ValueError('actually selected native runtime catalog differs')
            routed=posixpath.normpath(posixpath.join(posixpath.dirname(plan['spec'].replace('\\','/')),value['command'][0]))
            actual={posixpath.normpath(name.replace('\\','/')):digest for name,digest in base['files'].items()}
            if routed!=prepared['actual_executable'] or actual.get(routed)!=build['binary_sha256']:raise ValueError('actually executed native executable differs from retained compiled baseline')
            if base['files'].get(prefix+plan['spec'].replace('\\','/').removeprefix(prefix))!=sha256(spec):raise ValueError('executed contract missing from prelaunch identity')
            ordinary.append(observation['attempt'])
        if seen!=set(case_map):raise ValueError('incomplete batch')
    calibration=project/'source-fault-final-native-exit-v1/v1';summary=document(calibration/'summary.json');triples=[]
    if summary['phase']!='final-archive' or summary['final_native_calibration_executions']!=9 or len(summary['observations'])!=3:raise ValueError('partial/stale calibration window')
    for fault,observed in zip(faults['faults'],summary['observations']):
        if fault['id']!=observed['fault']:raise ValueError('fault selection changed')
        receipt_path=located(observed['compiled_receipt']);compiled=document(receipt_path)
        if sha256(receipt_path)!=observed['compiled_receipt_sha256'] or compiled['pristine_build_sha256']!=sha256(target/'build.json') or compiled['fault_declaration_sha256']!=sha256(package/'fault-declaration.json'):raise ValueError('source mutation compile provenance changed')
        source_review=document(package/'source-review.json');sources=dict(source_review['reviewed_inputs']);sources[fault['path']]=fault['mutated_source_sha256']
        expected_sources={prefix+'active/cargo-generate/src/'+name:digest for name,digest in sources.items()}
        if compiled['source_inputs']!=expected_sources or compiled['compiler_sha256']!=build['compiler_sha256'] or compiled['cargo_sha256']!=build['cargo_sha256']:raise ValueError('compiled mutation source/toolchain differs from one declared native fault')
        for phase in ['baseline','mutated','restored']:
            item=observed[phase];path=located(item['report']);row=report(path,'failed' if phase=='mutated' else 'passed',fault['category'] if phase=='mutated' else None)
            if sha256(path)!=item['report_sha256'] or item['runner_sha256']!=candidate['binary_sha256']:raise ValueError('calibration report/archive differs')
            wrapper,base=command(item['attempt'],1 if phase=='mutated' else 0)
            if phase=='mutated':
                mutation=wrapper.get('native_source_fault')
                if not mutation or mutation['actual_executable_sha256']!=compiled['binary_sha256'] or mutation['source_inputs']!=compiled['source_inputs']:raise ValueError('missing actually executed compiled mutation')
                if fault['id']=='F03':
                    first=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
                    if not all(s['status']=='passed' for s in row['steps'][:first]):raise ValueError('saved corruption hidden behind an earlier failure')
            triples.append(item['attempt'])
    return dict(schema_version=1,host=host,revision=revision,run=run,ordinary_attempts=ordinary,calibration_attempts=triples,
        candidate_archive_sha256=candidate['archive_sha256'],target_binary_sha256=build['binary_sha256'],
        ordinary_readbacks=len(ordinary),calibration_readbacks=len(triples),project_admissions=0,
        scope='Actual reports/launch/source/variation readback only; complete source/executable retention, canonical native profile, provider, corruption controls and admission closure remain separate required gates.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['windows','linux'],required=True);parser.add_argument('--root',type=Path,default=RAW)
    parser.add_argument('--revision',required=True);parser.add_argument('--run');args=parser.parse_args()
    args.root.resolve(strict=True).relative_to(RAW.resolve(strict=True))
    value=audit(args.root,args.host,args.revision,args.run)
    immutable_json(RAW/'cargo-generate'/('final-cell-readback-'+args.host+'-'+uuid.uuid4().hex+'.json'),value)
    print('Actual native final cell readback:',args.host,value['ordinary_readbacks'],'ordinary /',value['calibration_readbacks'],'calibrations; admission closure remains separate')


if __name__=='__main__':main()
