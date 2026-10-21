"""Independently audit final compiled Rclone batches and real source mutations."""
import argparse
from pathlib import Path

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'],required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid run')
    parent=RAW/'native'/args.run;meta=load(parent/'run-metadata.json');host=args.host
    require(meta['status']=='completed' and meta['conclusion']=='success' and len(meta['jobs'])==2
        and all(j['status']=='completed' and j['conclusion']=='success' for j in meta['jobs']),'incomplete native jobs')
    expected_jobs={'native-final (ubuntu-24.04, linux-amd64, linux_amd64, tar.gz)',
        'native-final (windows-2025, windows-amd64, windows_amd64, zip)'}
    require({j['name'] for j in meta['jobs']}==expected_jobs,'different native host matrix')
    packet=parent/('final-rclone-'+('Linux' if host=='linux' else 'Windows'));target=packet/'rclone'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'
    profile=docs if host=='linux' else docs/'native-profiles/windows'
    candidate=load(docs.parent/'migration-candidate-freeze.json');cell=next(c for c in candidate['cells'] if c['host']==host)
    installed=load(packet/'private-install/migration-v2'/(host+'-amd64')/'installation.json')
    require(installed['archive_sha256']==cell['archive_sha256'] and installed['binary_sha256']==cell['binary_sha256']
        and installed['source_revision']==candidate['source_revision'] and installed['version']==candidate['version'],'different exact candidate')
    retained=target/'retained-source';build=load(retained/'build.json');runtime=load(retained/'runtime.json')
    sdk=load(retained/'sdk.json');review=load(docs/'source-review.json');index=load(retained/'verified-index.json')
    require(build['pin']==review['pin'] and build['source_review_sha256']==sha256(docs/'source-review.json')
        and build['version']=='v1.76.0-DEV' and not build['cgo_enabled'] and not build['target_hooks_executed']
        and sdk['host']==host and sdk['architecture']=='amd64' and sdk['version']=='go1.27.0'
        and build['sdk_sha256']==sha256(retained/'sdk.json')==runtime['sdk_sha256']
        and build['compiler_sha256']==runtime['compiler_sha256'],'wrong target/compiler provenance')
    require(build['native_settings']==dict(CGO_ENABLED='0',GOAMD64='v1',GOARCH='amd64',GOOS=host,GOVERSION='go1.27.0'),
        'different native build settings')
    require(index['archive_sha256']==review['archive_sha256']
        and {n:r['sha256'] for n,r in index['files'].items()}==review['reviewed_inputs'],'different retained source catalog')
    prefix='artifacts/runner-readiness-ten-project-pass/active/rclone/'
    ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts()
    def witness(identity,expected=0,fault=None,compiled=None,public=False,compiler_required=True):
        event=events[identity];end=event['finished']
        require(all(e['phase']=='final-archive' for e in event.values()),'actual final phase differs')
        require('launched' in event and event['started']['expected_exit']==expected and end['category']=='passed'
            and end['exit_code']==expected and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],
            'actual command outcome/cleanup differs')
        require(sha256(packet/event['started']['project']/identity/'console.log')==end['console_sha256'],'changed actual output')
        manifest=load_manifest(packet,event['identified']['identity']);files=manifest['files'];expected_source=dict(review['reviewed_inputs'])
        if fault:expected_source[fault['path']]=fault['mutated_source_sha256']
        require({n[len(prefix+'src/'):]:d for n,d in files.items() if n.startswith(prefix+'src/')}==expected_source,
            'actual source catalog differs')
        compiler_key=prefix+'toolchain/go/bin/'+('go.exe' if host=='windows' else 'go')
        if compiler_required:require(files[compiler_key]==build['compiler_sha256'],'actual compiler differs')
        if 'runtime_executables' in manifest:
            require(manifest['runtime_executables']['go']==build['compiler_sha256'],'actual runtime compiler differs')
        if compiled:require(files[prefix+build['binary_relative_path']]==compiled,'actual target executable differs')
        if public:require(files[installed['binary']]==cell['binary_sha256'],'actual archive runner differs')
        return files
    for key in ['build_attempt','settings_attempt']:witness(build[key])
    witness(build['version_attempt'],compiled=build['binary_sha256'],compiler_required=False)
    frozen=load(profile/'reviewed-contract-freeze.json');package=target/'host-contracts'
    for name,digest in frozen['all_package_inputs'].items():require(sha256(package/name)==digest,'native canonical input changed')
    declaration=load(docs/'final-series-declaration.json');final=target/'final-series';intent=load(final/'intent.json')
    require(intent['host']==host and intent['declaration_file']=='final-series-declaration.json'
        and intent['declaration_sha256']==sha256(docs/'final-series-declaration.json')
        and declaration['candidate_freeze_sha256']==sha256(docs.parent/'migration-candidate-freeze.json')
        and intent['runner_sha256']==cell['binary_sha256'] and intent['archive_sha256']==cell['archive_sha256']
        and intent['target_build_sha256']==sha256(retained/'build.json') and intent['target_pin']==review['pin']
        and intent['canonical_package_inputs']==frozen['all_package_inputs'],'different final intent')
    require(len(declaration['batches'])==12 and [b['number'] for b in declaration['batches']]==list(range(12)),'invalid twelve-batch declaration')
    invocations=set();commands=set();rows=[]
    def result_ok(row,status):
        require(row['status']==status and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'actual result/cleanup differs')
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'reused invocation/workspace')
        invocations.add(row['invocation_id'])
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id']
                and step['state']['workspace_id']==row['workspace']['id'],'cross-execution state')
    def bind_inputs(files,current,contract,name,inputs):
        for relative,digest in inputs.items():
            selected=(relative==name or relative.startswith(contract['workspace']['fixture'].rstrip('/')+'/')
                or any(s.get('snapshot')==relative.removeprefix('snapshots/') for s in contract['steps']))
            if selected:require(files['artifacts/runner-readiness-ten-project-pass/'+(current/relative).relative_to(packet).as_posix()]==digest,
                'actual selected input not bound')
    for batch in declaration['batches']:
        folder=final/str(batch['number']);prepared=load(folder/'prepared.json');current=folder/batch['package_directory']
        require(prepared['batch']==batch and set(prepared['package_inputs'])==set(frozen['all_package_inputs']),'batch coverage differs')
        for name,digest in prepared['package_inputs'].items():
            require(sha256(current/name)==digest,'changed prepared bytes')
            if name not in frozen['contracts']:require(digest==frozen['all_package_inputs'][name],'changed fixture/snapshot')
        for number,name in enumerate(sorted(frozen['contracts'])):
            before=load(profile/'contracts'/name);expected=dict(before);contract=load(current/name)
            if batch['input_chunks']:
                size=batch['input_chunks'];steps=[]
                for step in before['steps']:
                    if set(step)=={'text'} and len(step['text'])>size:
                        steps.extend({'text':step['text'][i:i+size]} for i in range(0,len(step['text']),size))
                    else:steps.append(step)
                expected['steps']=steps
            require(contract==expected,'executed contract exceeds declared variation')
            require(load(folder/(name+'.planned.json'))==dict(batch=batch['number'],number=number,spec=name,
                runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],spec_sha256=sha256(current/name),
                prepared_sha256=sha256(folder/'prepared.json'),owned_two_second_worker=batch['contention']),'changed prelaunch plan')
            observed=load(folder/(name+'.observed.json'));identity=observed['attempt'];report_path=folder/(name+'.report.json')
            require(identity not in commands,'reused command');commands.add(identity)
            report=load(report_path);row=report['results'][0]
            require(report['runner_version']==candidate['version'] and report['summary']==dict(total=1,passed=1,failed=0,cancelled=0,not_run=0)
                and observed['report_sha256']==sha256(report_path) and observed['invocation_id']==row['invocation_id'],'actual report differs')
            result_ok(row,'passed')
            require(len(row['steps'])==len(contract['steps']) and all(s['status']=='passed' for s in row['steps']),'incomplete positive evidence')
            event=events[identity]['started']
            require(event['label']=='final-batch-'+str(batch['number'])+'-'+name
                and event['variation']==('owned 2-second 8-MiB SHA256 CPU worker' if batch['contention'] else 'ordinary'),'schedule differs')
            files=witness(identity,compiled=build['binary_sha256'],public=True)
            bind_inputs(files,current,contract,name,prepared['package_inputs']);rows.append(observed)
        complete=load(folder/'complete.json')
        require(complete['observed']==20 and complete['records']==rows[-20:],'incomplete actual batch')
    require(len(rows)==240 and len(invocations)==240,'incorrect ordinary denominator')
    summaries=list((target/'faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous fault batch')
    summary=load(summaries[0]);selection=load(docs/'fault-selection.json');calibration=[]
    require(summary['runner_sha256']==cell['binary_sha256'] and summary['original_binary_sha256']==build['binary_sha256']
        and summary['compiler_sha256']==build['compiler_sha256'] and {f['id'] for f in summary['faults']}=={'F01','F02','F03'}
        and len(summary['faults'])==3,'fault coverage/provenance differs')
    for declared in selection['faults']:
        receipt=next(f for f in summary['faults'] if f['id']==declared['id'])
        require(all(receipt[k]==v for k,v in declared.items()) and receipt['restored_exact'] and not receipt['original_heldout'],'reviewed fault differs')
        mutated=receipt['mutation_validation'];restored=receipt['restored_validation']
        require(mutated['binary_sha256']!=build['binary_sha256'] and restored['binary_sha256']==build['binary_sha256']
            and mutated['compiler_sha256']==restored['compiler_sha256']==build['compiler_sha256'],'actual recompile/restoration differs')
        for validation,fault in [(mutated,declared),(restored,None)]:
            witness(validation['attempt'],fault=fault)
            witness(validation['version_attempt'],fault=fault,compiled=validation['binary_sha256'])
        for phase,code,compiled,fault in [('baseline',0,build['binary_sha256'],None),('mutated',1,mutated['binary_sha256'],declared),
            ('restored',0,build['binary_sha256'],None)]:
            identity=receipt[{'baseline':'baseline_attempt','mutated':'mutation_attempt','restored':'restored_attempt'}[phase]]
            require(identity not in commands,'reused calibration command');commands.add(identity)
            files=witness(identity,code,fault,compiled,True);contract=load(package/declared['spec'])
            bind_inputs(files,package,contract,declared['spec'],frozen['all_package_inputs'])
            path=summaries[0].parent/(declared['id']+'-'+phase+'.json');report=load(path);row=report['results'][0]
            require(report['runner_version']==candidate['version'] and row['spec_version']==3
                and Path(row['spec_path'].replace('\\','/')).name==declared['spec'],'actual calibration version/spec differs')
            result_ok(row,'failed' if code else 'passed')
            if code:
                require(row['failure']['category']==declared['category'],'wrong mutant diagnosis')
                require(row['target']['exited'] and row['target']['exit_code']==0,'mutant target exit differs')
                if declared['id']!='F02':
                    failed=next(i for i,s in enumerate(row['steps']) if s['status']=='failed');prior=row['steps'][:failed];state=row['steps'][failed]['state']
                    require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
                        and state['kind']==declared['state_kind'] and state['path']==declared['state_path'],'missing actual false-green/state rejection')
                    if declared['id']=='F03':require(sum(s.get('state',{}).get('kind')=='file' for s in prior)==2,'missing prior exact file passes')
            calibration.append(dict(fault=declared['id'],phase=phase,command=identity,invocation_id=row['invocation_id'],report_sha256=sha256(path)))
    removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/rclone' and removed['source_archive_sha256']==review['archive_sha256']
        and prepared['runtime_processes_verified'] and prepared['managed_cleanup_verified'],'unconfirmed source/runtime cleanup')
    for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'selected source restore differs')
    immutable_json(docs/('final-verified-'+host+'.json'),dict(run=args.run,host=host,ordinary_executions=240,calibration_executions=9,
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],target_pin=build['pin'],
        source_fault_summary_sha256=sha256(summaries[0]),cleanup_receipt_sha256=sha256(retained/'removed.json'),observations=rows,
        calibration_observations=calibration,final_archive_credit=0,
        scope='Exact native final archive and phase, twelve fresh executions per case, independently reconstructed variants and unchanged oracles, full prelaunch source/compiler catalogs, real compiled faults, exact restoration and checked cleanup. Overall final matrix gates remain separate.'))
    print('Verified final Rclone 240 ordinary executions and nine actual compiled-fault controls:',host)


if __name__=='__main__':main()
