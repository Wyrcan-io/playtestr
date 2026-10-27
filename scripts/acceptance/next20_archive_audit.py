"""Independently inspect complete actual public archive-control reexecutions."""
import argparse
import asyncio
import hashlib
import json
import re
import uuid

from next20_check import RAW, ROOT, NAME, NextCampaign, owned_environment
from adversarial_process import execute
from readiness_compact_native import compact
from readiness_archive_controls import cases, definition_sha256
from readiness_evidence import immutable_json, sha256
from next20_verify_jrnl import require, source_hashes
from next20_candidate import contract,SERIES


def audit(base,host,control_id=None,run=None,revision=None,candidate_series='rc5'):
    def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
    inherited=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    freeze,cell,candidate_directory=contract(candidate_series,host)
    candidate_relative=candidate_directory.relative_to(RAW).as_posix()
    declaration=load(inherited/'archive-control-declaration.json')
    require([(c['id'],definition_sha256(c)) for c in cases()]==[(c['id'],c['definition_sha256']) for c in declaration['cases']],'changed inherited definitions')
    paths=list((base/'product-controls').glob('*/results.json'))
    if control_id:paths=[p for p in paths if p.parent.name==control_id]
    require(len(paths)==1,'missing/ambiguous complete control run')
    root=paths[0].parent;result=load(paths[0]);intent=load(root/'intent.json');build=load(root/'build.json')
    require(result['observed']==35 and result['runner_sha256']==build['runner_sha256']==cell['binary_sha256'] and result['archive_sha256']==build['archive_sha256']==cell['archive_sha256'],'wrong/partial actual archive series')
    definition='scripts/acceptance/readiness_archive_controls.py'
    definition_hashes=source_hashes(revision,definition) if revision else {sha256(ROOT/definition)}
    require(intent['declaration_sha256']==sha256(inherited/'archive-control-declaration.json') and intent['build_sha256']==sha256(root/'build.json') and intent['definition_source_sha256'] in definition_hashes,'changed actual declaration/source/build')
    installed=load(base/candidate_relative/'installed.json')
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256'],'wrong actual archive install')
    planned=[c['id'] for c in cases()]+declaration['recorder_controls']
    require(intent['planned_cases']==planned==[c['case'] for c in result['controls']],'missing/duplicate control cases')
    invocations=set();commands=set()
    def command(eid,label,code,fixture=True):
        require(re.fullmatch('[0-9a-f]{32}',eid) and eid not in commands,'invalid/duplicate actual control command');commands.add(eid)
        events={k:load(base/'events'/(eid+'-'+k+'.json')) for k in ['started','identified','launched','finished']}
        require(all(e['id']==eid and e['label']==label and e['campaign']==NAME and e['phase']=='final-archive' for e in events.values()),'wrong control event phase/identity')
        finish=events['finished'];require(finish['category']=='passed' and finish['exit_code']==code and finish['harness_cleanup']=='harness_process_reaped' and not finish['cleanup_errors'],'failed/unclean actual control command')
        console=base/'core'/eid/'console.log';require(sha256(console)==finish['console_sha256'],'changed actual control console')
        reference=events['identified']['identity'];require('..' not in reference['manifest'].replace('\\','/').split('/'),'unsafe manifest reference')
        manifest=base/reference['manifest'];require(sha256(manifest)==reference['sha256'],'changed actual prelaunch identity')
        identity=load(manifest);files=identity['files']
        if run:
            require(events['started']['ci_run_id']==run and str(events['started']['ci_run_attempt'])=='1','wrong actual native run/attempt')
            helper_names=['next20_archive_controls.py','readiness_archive_controls.py','readiness_bootstrap_go.py','next20_check.py','adversarial_process.py','readiness_evidence.py']
            if candidate_series!='rc5':helper_names.append('next20_candidate.py')
            for name in helper_names:
                key='scripts/acceptance/'+name
                require(files.get(key) in source_hashes(revision,key),'stale native public-control source: '+name)
        if not fixture:require(identity.get('runtime_executables',{}).get('go')==build['compiler_sha256'],'actual prelaunch compiler identity missing/changed')
        if fixture:
            require(files.get('artifacts/'+NAME+'/'+candidate_relative+'/playtestr'+('.exe' if host=='windows' else ''))==cell['binary_sha256'],'actual launched runner differs')
        return files,console.read_text(encoding='utf-8-sig')
    build_files,_=command(build['build_attempt'],'archive-controls-fixture-build',0,False)
    fixture_source_hashes=source_hashes(revision,'cmd/fixture/main.go') if revision else {sha256(ROOT/'cmd/fixture/main.go')}
    require(build_files['cmd/fixture/main.go']==build['fixture_source_sha256'] and build['fixture_source_sha256'] in fixture_source_hashes,'actual compiled fixture source differs')
    for name in ['go.mod','go.sum']:
        expected_hashes=source_hashes(revision,name) if revision else {sha256(ROOT/name)}
        require(build_files[name] in expected_hashes,'actual compiled fixture module inputs differ')
        if revision:require(build[name.replace('.','_')+'_sha256']==build_files[name],'native build module receipt mismatch')
    for case,observed in zip(cases(),result['controls']):
        folder=root/case['id'];spec=load(folder/'spec.json');report=load(folder/'report.json')
        require(sha256(folder/'spec.json')==observed['spec_sha256'] and sha256(folder/'report.json')==observed['report_sha256'],'changed actual spec/report')
        expected=int(case['category'] is not None);files,_=command(observed['attempt'],'archive-control-'+case['id'],expected)
        key='artifacts/'+NAME+'/'+(folder/'spec.json').relative_to(base).as_posix()
        require(files.get(key)==observed['spec_sha256'],'prelaunch contract not actual report contract')
        require(spec['command'][0].replace('\\','/').endswith(build['fixture_relative_path']) and spec['command'][1]==case['mode'],'wrong fixture invocation')
        if case['id']!='unsupported-format':require(files.get(build['fixture_relative_path'])==build['fixture_sha256'],'actual fixture executable differs')
        require([s['state'] for s in spec['steps'] if 'state' in s]==case['states'],'changed reviewed exact-state expectations')
        for name,value in case['changes'].items():require(spec[name]==value,'changed declared boundary override')
        actual={p.relative_to(folder/'fixture').as_posix():p for p in (folder/'fixture').rglob('*') if p.is_file()}
        require(set(actual)==set(case['files']),'extra/missing initial fixture')
        for name,data in case['files'].items():
            digest=hashlib.sha256(data).hexdigest();key='artifacts/'+NAME+'/'+actual[name].relative_to(base).as_posix()
            require(actual[name].read_bytes()==data and files.get(key)==digest,'changed exact prelaunch fixture bytes')
        require(report['runner_version']==freeze['version'] and report['os']==host and report['arch']==cell['architecture'] and len(report['results'])==1,'wrong actual archive/platform/report')
        row=report['results'][0];require(row['status']==('failed' if expected else 'passed'),'wrong actual control result')
        if expected:require(row['failure']['category']==case['category'],'wrong actual rejection diagnosis')
        if case['category']=='invalid_spec':require(not row.get('invocation_id') and not row.get('workspace') and not row['cleanup']['attempted'],'invalid spec launched target')
        else:
            require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'] and row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'missing/duplicated cleanup/invocation proof')
            invocations.add(row['invocation_id'])
            if not expected:require(len(row['steps'])==len(spec['steps']) and all(s['status']=='passed' for s in row['steps']),'missing actual positive control steps')
            for step in row['steps']:
                if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-execution control state')
        if case['id']=='descendant-timeout-cleanup':require(observed['independent_child_termination'] in {'native PID absent','native process handle signaled'},'missing independently observed owned descendant termination')
    for observed in result['controls'][-2:]:
        _,console=command(observed['attempt'],'archive-control-'+observed['case'],1)
        anchor='unresolved control failures' if observed['case']=='recorder-rejected-capture' else 'completion'
        require(observed['export_absent'] and not (root/observed['case']/'recorded.json').exists() and anchor in console,'recorder false green/refusal proof missing')
    removed=load(root/'removed.json');require(removed['fixture_binary_removed'] and removed['fixture_sha256']==build['fixture_sha256'] and removed['all_public_target_workspaces_checked'] and not (root/'bin').exists(),'fixture cleanup missing or false')
    if run:
        prerequisite=load(root/'compiler-prerequisite.json')
        require(prerequisite['selected_compiler_sha256']==build['compiler_sha256'],'selected native compiler changed')
        if prerequisite['owned_sdk_used']:
            require(('artifacts/'+NAME+'/toolchain/go/bin/go') in prerequisite['selected_compiler'].replace('\\','/'),'SDK not confined to new campaign')
            sdk=load(base/'toolchain/sdk.json');require(sdk['version']=='go1.25.0' and sdk['host']==host and sdk['architecture']==cell['architecture'],'wrong owned SDK profile')
    return dict(schema_version=1,host=host,public_reexecutions=35,result_sha256=sha256(paths[0]),
        definition_source_sha256=intent['definition_source_sha256'],actual_invocations=len(invocations),
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],new_project_credit=0,new_whole_control_credit=0)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['linux','darwin','windows'],required=True)
    parser.add_argument('--packet');parser.add_argument('--control-id');parser.add_argument('--run')
    parser.add_argument('--generation',type=int);parser.add_argument('--candidate-series',choices=SERIES,default='rc5');args=parser.parse_args()
    metadata=None
    if args.run:
        require(args.run.isascii() and args.run.isdecimal() and args.generation is not None,'explicit safe native run/generation required')
        label={'linux':'Linux','darwin':'macOS','windows':'Windows'}[args.host]
        args.packet='native/'+args.run+'/next20-archive-controls-'+label
        metadata_path=RAW/'provider'/(args.run+'.json')
        if not metadata_path.exists():
            actual=asyncio.run(execute(['gh','run','view',args.run,'--json','databaseId,status,conclusion,headSha,jobs,url'],
                'core','inspect-public-control-provider',cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign()))
            metadata=json.loads(actual['output']);require(metadata['status']=='completed','native control run still pending')
            immutable_json(metadata_path,metadata)
        metadata=json.loads(metadata_path.read_text())
        require(str(metadata['databaseId'])==args.run and metadata['conclusion']=='success','actual native control provider run failed')
        os_label={'linux':'ubuntu-24.04','darwin':'macos-15','windows':'windows-2025'}[args.host]
        jobs=[j for j in metadata['jobs'] if os_label in j['name']]
        require(len(jobs)==1 and jobs[0]['conclusion']=='success','missing successful actual native control host')
        steps={s['name']:s['conclusion'] for s in jobs[0]['steps']}
        require(steps.get('Reexecute inherited public controls through exact native archive')=='success' and
            any(s['conclusion']=='success' and s['name'].startswith('Run actions/upload-artifact@') for s in jobs[0]['steps']),'missing actual complete control/upload steps')
        packet_metadata=RAW/'native'/args.run/'run-metadata.json'
        if packet_metadata.exists():require(json.loads(packet_metadata.read_text())==metadata,'existing actual provider metadata changed')
        else:immutable_json(packet_metadata,metadata)
    base=RAW/args.packet if args.packet else RAW
    base.resolve(strict=True).relative_to(RAW.resolve())
    result=audit(base,args.host,args.control_id,args.run,metadata['headSha'] if metadata else None,args.candidate_series);destination=RAW/'product-control-audits'/uuid.uuid4().hex
    if args.candidate_series!='rc5':result['candidate_series']=args.candidate_series
    if args.run:
        retained=compact(RAW,'product-controls',[args.run],generation=args.generation)
        result.update(run=args.run,revision=metadata['headSha'],generation=args.generation,
            archive_sha256=sha256(retained/'packets.tar.gz'),index_sha256=sha256(retained/'index.json'),provider_metadata_sha256=sha256(RAW/'provider'/(args.run+'.json')))
        immutable_json(retained/'public-control-audit.json',result)
    immutable_json(destination/'verified.json',result)
    print('Independently audited 35 actual exact-archive public controls:',args.host)


if __name__=='__main__':main()
