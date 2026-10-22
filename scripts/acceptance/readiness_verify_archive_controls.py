"""Audit actual exact-archive control reports, inputs and native launch events."""
import argparse
import hashlib
import re

from readiness_archive_controls import cases, definition_sha256
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import packet_file, read_json as load

DOC=ROOT/'docs/validation/runner-readiness-ten-project-pass'
PREFIX='artifacts/runner-readiness-ten-project-pass/'


def audit(base,host,control_id=None):
    declaration=load(DOC/'archive-control-declaration.json')
    frozen=load(DOC/'migration-candidate-freeze.json')
    cell=next(c for c in frozen['cells'] if c['host']==('darwin' if host=='macos' else host))
    roots=list((base/'product-controls').glob('*/results.json'))
    if control_id:roots=[p for p in roots if p.parent.name==control_id]
    require(len(roots)==1,'one complete actual public-control packet required')
    root=roots[0].parent;result=load(roots[0]);build=load(root/'build.json');intent=load(root/'intent.json')
    require(intent['declaration_sha256']==sha256(DOC/'archive-control-declaration.json')
        and intent['build_sha256']==sha256(root/'build.json'),'changed prelaunch public-control declaration/build')
    require(result['runner_sha256']==build['runner_sha256']==cell['binary_sha256']
        and result['archive_sha256']==build['archive_sha256']==cell['archive_sha256'],'wrong actual control archive')
    installed=load(base/('private-install/migration-v2/'+cell['host']+'-'+cell['architecture']+'/installation.json'))
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256'],
        'actual private installation differs')
    definitions=cases()
    require([(c['id'],definition_sha256(c)) for c in definitions]==[(c['id'],c['definition_sha256']) for c in declaration['cases']],
        'public-control definitions changed')
    expected=[c['id'] for c in definitions]+declaration['recorder_controls']
    require(intent['planned_cases']==expected and [r['case'] for r in result['controls']]==expected
        and result['observed']==len(expected)==35,'incomplete or duplicate public-control series')
    def key(path):return PREFIX+path.relative_to(base).as_posix()
    def actual_file(reference):
        require(reference.replace('\\','/').startswith(PREFIX),'control reference escapes campaign')
        return packet_file(base,reference.replace('\\','/').removeprefix(PREFIX),4*1024**2)
    commands=set();invocations=set();workspaces=set();rows=[]
    def command(identity,label,expected,fixture=True,unsupported=False):
        require(re.fullmatch('[a-f0-9]{32}',identity) and identity not in commands,'unsafe/duplicate control command')
        commands.add(identity)
        events={kind:load(packet_file(base,'events/'+identity+'-'+kind+'.json',2*1024**2))
            for kind in ['started','identified','launched','finished']}
        require(all(e['id']==identity and e['event']==kind and e['project']=='core' and e['phase']=='final-archive'
            and e['label']==label for kind,e in events.items()),'actual native command identity differs')
        end=events['finished']
        require(end['exit_code']==expected and end['category']=='passed' and end['harness_cleanup']=='harness_process_reaped'
            and not end['cleanup_errors'],'control exit or harness cleanup differs')
        console=packet_file(base,'core/'+identity+'/console.log',4*1024**2)
        require(sha256(console)==end['console_sha256'],'actual control console differs')
        reference=events['identified']['identity'];manifest=packet_file(base,reference['manifest'].replace('\\','/'),2*1024**2)
        require(sha256(manifest)==reference['sha256'],'actual prelaunch manifest changed')
        files=load(manifest)['files']
        if fixture:
            require(files.get(installed['binary'])==cell['binary_sha256']
                and (unsupported or files.get(build['fixture_relative_path'])==build['fixture_sha256']),
                'executed runner/fixture identity differs: '+label)
        return files,console
    build_files,_=command(build['build_attempt'],'archive-controls-fixture-build',0,fixture=False)
    require(build_files.get('cmd/fixture/main.go')==build['fixture_source_sha256']
        and build_files.get('go.mod')==build['go_mod_sha256'] and build_files.get('go.sum')==build['go_sum_sha256'],
        'actual fixture build source differs')
    for case,observed in zip(definitions,result['controls']):
        folder=root/case['id'];spec=folder/'spec.json';report=folder/'report.json';contract=load(spec);value=load(report)
        require(sha256(spec)==observed['spec_sha256'] and sha256(report)==observed['report_sha256'],
            'actual public-control contract/report hash differs')
        files,_=command(observed['attempt'],'archive-control-'+case['id'],int(case['category'] is not None),
            unsupported=case['id']=='unsupported-format')
        require(files.get(key(spec))==sha256(spec),'actual executed contract differs')
        require(contract['command'][0].replace('\\','/').endswith(build['fixture_relative_path'])
            and contract['command'][1]==case['mode'],'different actual synthetic fixture invocation')
        changes=case['changes']
        for name,want in changes.items():require(contract[name]==want,'declared control override changed')
        states=[s['state'] for s in contract['steps'] if 'state' in s]
        require(states==case['states'],'changed exact state expectations')
        actual={p.relative_to(folder/'fixture').as_posix():p for p in (folder/'fixture').rglob('*') if p.is_file()}
        require(set(actual)==set(case['files']),'missing/extra initial control fixture file')
        for name,data in case['files'].items():
            require(actual[name].read_bytes()==data and files.get(key(actual[name]))==hashlib.sha256(data).hexdigest(),
                'actual prelaunch fixture bytes differ')
        row=value['results'][0];failed=case['category'] is not None
        require(value['runner_version']==frozen['version'] and value['os']==('darwin' if host=='macos' else host)
            and value['arch']==('arm64' if host=='macos' else 'amd64')
            and value['summary']==dict(total=1,passed=int(not failed),failed=int(failed),cancelled=0,not_run=0)
            and row['status']==('failed' if failed else 'passed'),'actual public-control outcome differs')
        if failed:require(row['failure']['category']==case['category'],'wrong actual failure diagnosis')
        if case['category']=='invalid_spec':
            require(not row.get('invocation_id') and not row.get('workspace') and not row['cleanup']['attempted'],
                'invalid public contract launched a target')
        else:
            require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'incomplete target/workspace cleanup')
            require(row['invocation_id'] not in invocations and row['workspace']['id'] not in workspaces,'reused public invocation')
            invocations.add(row['invocation_id']);workspaces.add(row['workspace']['id'])
            if not failed:require(len(row['steps'])==len(contract['steps']) and all(s['status']=='passed' for s in row['steps']),
                'missing actual positive public step')
            for step in row['steps']:
                if 'state' in step:require(step['state']['invocation_id']==row['invocation_id']
                    and step['state']['workspace_id']==row['workspace']['id'],'cross-execution state proof')
            if case['id']=='dynamic-wrong-bytes':require(all(s['status']=='passed' for s in row['steps'][:4])
                and row['steps'][4]['state']['outcome']=='rejected','missing actual terminal-success/wrong-file refusal')
        if case['id']=='descendant-timeout-cleanup':require(observed['independent_child_termination'] in
            {'native PID absent','native process handle signaled'},'missing independent actual descendant termination')
        rows.append(dict(case=case['id'],attempt=observed['attempt'],report_sha256=sha256(report)))
    for observed in result['controls'][len(definitions):]:
        label=observed['case'];_,console=command(observed['attempt'],'archive-control-'+label,1)
        output=console.read_text(encoding='utf-8-sig')
        require(observed['export_absent'] and not (root/label/'recorded.json').exists(),'recorder exported false green')
        require(('unresolved control failures' if label=='recorder-rejected-capture' else 'completion') in output,
            'missing actual recorder refusal diagnosis')
        rows.append(dict(case=label,attempt=observed['attempt'],console_sha256=sha256(console)))
    removed=load(root/'removed.json')
    require(removed['fixture_binary_removed'] and removed['all_public_target_workspaces_checked']
        and removed['fixture_sha256']==build['fixture_sha256'] and not (base/build['fixture_relative_path'].removeprefix(PREFIX)).exists(),
        'synthetic fixture removal not confirmed')
    if host=='windows':command(removed['native_removal_attempt'],'archive-controls-fixture-checked-removal',0,fixture=False)
    return dict(host=host,controls=rows,observed=35,runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],
        actual_results_sha256=sha256(roots[0]),build_sha256=sha256(root/'build.json'),removed_sha256=sha256(root/'removed.json'),
        declaration_sha256=sha256(DOC/'archive-control-declaration.json'),new_unique_control_credit=0,new_project_credit=0,
        scope='Actual exact-archive public-control reexecutions, prelaunch fixture/contract/runner identities, native reports, recorder refusals and bounded cleanup. Source-only unit/race/harness controls remain separately qualified.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['linux','macos','windows'],required=True)
    parser.add_argument('--run');parser.add_argument('--local-control');args=parser.parse_args()
    if args.run:
        require(args.run.isascii() and args.run.isdecimal(),'unsafe native run')
        parent=RAW/'native'/args.run;meta=load(parent/'run-metadata.json')
        require(meta['status']=='completed' and meta['conclusion']=='success' and len(meta['jobs'])==3
            and all(j['status']=='completed' and j['conclusion']=='success' for j in meta['jobs']),
            'all three actual native jobs must complete successfully')
        suffix={'linux':'Linux','macos':'macOS','windows':'Windows'}[args.host]
        receipt=audit(parent/('archive-controls-'+suffix),args.host)
        receipt.update(run=args.run,native_metadata_sha256=sha256(parent/'run-metadata.json'))
        immutable_json(DOC/('archive-controls-verified-'+args.host+'.json'),receipt)
    else:
        require(args.host=='windows' and args.local_control and re.fullmatch('[a-f0-9]{32}',args.local_control),'explicit local Windows control required')
        receipt=audit(RAW,args.host,args.local_control)
        immutable_json(DOC/'archive-controls-verified-local-windows.json',receipt)
    print('Independently verified 35 actual public archive controls:',args.host)


if __name__=='__main__':main()
