"""Audit real compiled faults, restoration and public Rclone maintenance."""
import argparse

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_rclone_verify_first_use import require,verify_native


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'],required=True)
    parser.add_argument('--original',action='store_true')
    parser.add_argument('--both-host-jobs',action='store_true')
    parser.add_argument('--audit-only',action='store_true');args=parser.parse_args()
    require(not args.original or args.host=='linux','original heldout is Linux only')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'
    selection=load(docs/'fault-selection.json');review=load(docs/'source-review.json')
    first=verify_native(args.run,publish=False,phase_only=True,hosts=[args.host],
        job_hosts=['linux','windows'] if args.both_host_jobs else [args.host])
    cell=first['cells'][0];run=RAW/'native'/args.run;metadata=load(run/'run-metadata.json')
    packet=run/('playtestr-'+('Linux' if args.host=='linux' else 'Windows'));target=packet/'rclone'
    profile=docs if args.host=='linux' else docs/'native-profiles/windows'
    frozen=load(profile/'reviewed-contract-freeze.json');package=target/'host-contracts'
    require(load(target/'native-profile.json')['freeze_sha256']==sha256(profile/'reviewed-contract-freeze.json'),
            'actual native profile differs')
    for name,digest in frozen['all_package_inputs'].items():
        require(sha256(packet_file(package,name,1024**2))==digest,'actual frozen native input changed')
    ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts()
    build=load(target/'retained-source/build.json');prefix='artifacts/runner-readiness-ten-project-pass/active/rclone/'
    installed=load(packet/('private-install/provisional-v1/'+args.host+'-amd64/installation.json'))
    required_steps={'Execute exact committed native twenty-case profile','Rebuild actual source faults and restore exact source and executable'}
    job_name='terminal (ubuntu-24.04)' if args.host=='linux' else 'terminal (windows-2025)'
    actual_job=next(j for j in metadata['jobs'] if j['name']==job_name)
    require(all(any(s['name']==name and s['status']=='completed' and s['conclusion']=='success'
                    for s in actual_job['steps']) for name in required_steps),'actual qualification stages incomplete')
    require(build['binary_sha256']==cell['target_binary_sha256'],'first route and retained compiled target differ')
    def witness(identity,fault=None,compiled=None):
        event=events[identity];finished=event['finished']
        require('launched' in event and finished['category']=='passed' and not finished['cleanup_errors']
                and finished['harness_cleanup']=='harness_process_reaped','actual command outcome/cleanup differs')
        reference=event['identified']['identity'];manifest=packet_file(packet,reference['manifest'],2*1024**2)
        require(sha256(manifest)==reference['sha256'],'actual prelaunch identity changed')
        actual=load(manifest,maximum=2*1024**2);files=actual['files'];expected=dict(review['reviewed_inputs'])
        if fault:expected[fault['path']]=fault['mutated_source_sha256']
        require({n[len(prefix+'src/'):]:d for n,d in files.items() if n.startswith(prefix+'src/')}==expected,
                'actual original/mutated source catalog differs')
        require(actual['runtime_executables']['go']==build['compiler_sha256'],'actual compiler differs')
        if compiled:
            require(files[prefix+build['binary_relative_path']]==compiled,'actual launched compiled target differs')
        console=packet/event['started']['project']/identity/'console.log'
        require(sha256(console)==finished['console_sha256'],'actual command output changed')
        return event,files,console.read_text(encoding='utf-8-sig')
    summaries=list((target/'faults').glob('*/summary.json'));require(len(summaries)==1,'missing or ambiguous complete fault summary')
    summary=load(summaries[0]);root=summaries[0].parent
    require(summary['runner_sha256']==cell['runner_sha256'] and summary['original_binary_sha256']==build['binary_sha256']
            and summary['compiler_sha256']==build['compiler_sha256'],'fault summary compiled provenance differs')
    require(len(summary['faults'])==3 and {r['id'] for r in summary['faults']}=={'F01','F02','F03'},'incomplete real fault set')
    faults=[]
    for declared in selection['faults']:
        matches=[r for r in summary['faults'] if r['id']==declared['id']];require(len(matches)==1,'duplicate fault')
        receipt=matches[0]
        require(all(receipt[k]==v for k,v in declared.items()) and receipt['restored_exact'],'reviewed fault or restoration differs')
        require(receipt['original_heldout']==bool(args.original and declared['id']=='F03'),'original heldout accounting differs')
        mutated=receipt['mutation_validation'];restored=receipt['restored_validation']
        require(mutated['binary_sha256']!=build['binary_sha256'] and restored['binary_sha256']==build['binary_sha256']
                and mutated['compiler_sha256']==restored['compiler_sha256']==build['compiler_sha256'],'compiled mutation/restoration differs')
        for validation,fault in [(mutated,declared),(restored,None)]:
            witness(validation['attempt'],fault)
            witness(validation['version_attempt'],fault,validation['binary_sha256'])
        for phase,expected_exit,compiled,fault in [('baseline',0,build['binary_sha256'],None),
                ('mutated',1,mutated['binary_sha256'],declared),('restored',0,build['binary_sha256'],None)]:
            identity=receipt[{'baseline':'baseline_attempt','mutated':'mutation_attempt','restored':'restored_attempt'}[phase]]
            event,files,_=witness(identity,fault,compiled)
            require(files[installed['binary']]==cell['runner_sha256'],'actual public fault runner differs')
            require(event['started']['expected_exit']==expected_exit and event['finished']['exit_code']==expected_exit,'actual public runner exit differs')
            spec_key='artifacts/runner-readiness-ten-project-pass/rclone/host-contracts/'+declared['spec']
            require(files[spec_key]==frozen['contracts'][declared['spec']],'actual fault spec differs from committed freeze')
            for name,digest in frozen['all_package_inputs'].items():
                key='artifacts/runner-readiness-ten-project-pass/rclone/host-contracts/'+name
                if key in files:require(files[key]==digest,'actual selected input changed')
            report=load(root/(declared['id']+'-'+phase+'.json'));outcome=report['results'][0]
            require(report['runner_version']=='v0.4.0-rc.4' and outcome['cleanup']['confirmed_exited'] and outcome['workspace']['cleaned'],
                    'fault report version/cleanup differs')
            if phase=='mutated':
                require(outcome['failure']['category']==declared['category'],'wrong fault detection category')
                if declared['id']=='F02':require(outcome['target']['exited'] and outcome['target']['exit_code']==0,'wrong actual config-failure exit')
                else:
                    failed=next(i for i,s in enumerate(outcome['steps']) if s['status']=='failed');prior=outcome['steps'][:failed]
                    state=outcome['steps'][failed]['state']
                    require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
                            and outcome['target']['exited'] and outcome['target']['exit_code']==0
                            and state['kind']==declared['state_kind'] and state['path']==declared['state_path']
                            and state['invocation_id']==outcome['invocation_id'] and state['workspace_id']==outcome['workspace']['id'],
                            'file fault lacks unchanged passing screen, exact exit or same-execution rejection')
                    if declared['id']=='F03':require(sum(s.get('state',{}).get('kind')=='file' for s in prior)==2,'extra entry lacks prior exact files')
            else:require(outcome['status']=='passed','fault baseline/restoration failed')
        faults.append(dict(id=declared['id'],receipt_sha256=sha256(root/(declared['id']+'-receipt.json')),
            mutation_attempt=receipt['mutation_attempt'],restored_attempt=receipt['restored_attempt'],
            original_heldout=receipt['original_heldout'],mutated_binary_sha256=mutated['binary_sha256']))
    # Preserve original consumption even if a later maintenance step failed.
    receipt=dict(run=args.run,host=args.host,workflow_conclusion=metadata['conclusion'],faults=faults,
        native_freeze_sha256=sha256(profile/'reviewed-contract-freeze.json'),runner_sha256=cell['runner_sha256'],
        provisional_archive_sha256=cell['archive_sha256'],summary_sha256=sha256(summaries[0]),
        source_cleanup_sha256=sha256(target/'retained-source/removed.json'),development_admission=False,final_archive_credit=0)
    if args.audit_only:
        print('Reverified actual fault runner, compiler, source, outcomes and restoration without publishing another receipt.')
        return
    if args.original:
        immutable_json(docs/'original-source-faults.json',receipt)
    else:
        immutable_json(docs/('replica-source-faults-'+args.host+'-'+args.run+'.json'),receipt)
    print('Independently verified three real compiled faults and exact source/binary restoration; maintenance is a separate gate.')


if __name__=='__main__':main()
