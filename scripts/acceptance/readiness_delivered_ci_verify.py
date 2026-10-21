"""Audit a real delivered-CI success, source corruption or recovery run."""
import argparse
from pathlib import Path

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import packet_file, read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--mode',choices=['success','corruption','recovery'],required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid CI run')
    parent=RAW/'delivered-ci-generation';packet=parent/(args.mode+'-'+args.run)
    metadata=load(parent/('run-metadata-'+args.run+'.json'));red=args.mode=='corruption'
    require(metadata['status']=='completed' and metadata['conclusion']==('failure' if red else 'success')
        and len(metadata['jobs'])==1 and metadata['jobs'][0]['status']=='completed','wrong actual CI outcome')
    steps=metadata['jobs'][0]['steps'];public='Test recorded interactions'
    failures={s['name'] for s in steps if s['conclusion']=='failure'}
    require(failures==({public} if red else set()),'CI failed outside the intentional public test')
    for name in ['Build exact candidate runner','Explicit target build','Select committed suite and capture exact context',public,
        'Render offline evidence','Verify real target restoration, preserve provenance and remove owned source/runtime',
        'Accessible outcome summary','Run actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f']:
        matches=[s for s in steps if s['name']==name]
        require(len(matches)==1 and matches[0]['status']=='completed'
            and matches[0]['conclusion']==('failure' if red and name==public else 'success'),'missing actual delivered CI stage')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass';project=docs/'rclone'
    candidate=load(docs/'migration-candidate-freeze.json');review=load(project/'source-review.json')
    frozen=load(project/'reviewed-contract-freeze.json');fault=next(f for f in load(project/'fault-selection.json')['faults'] if f['id']=='F03')
    context=load(packet/'context.json');build=load(packet/'target-build.json');final=load(packet/'target-finalized.json')
    report=load(packet/'results.json');row=report['results'][0]
    require(context['event']=='workflow_dispatch' and context['run_id']==args.run and context['tested_sha']==metadata['headSha']
        and context['pr_number'] is None and context['head_sha'] is None,'actual event/context differs')
    spec='artifacts/runner-readiness-ten-project-pass/rclone/host-contracts/N02.json'
    selected={spec:frozen['all_package_inputs']['N02.json']}
    for name in ['fixtures/N02/rclone.conf','fixtures/N02/sentinel.bin','snapshots/N02-final.txt']:
        selected['artifacts/runner-readiness-ten-project-pass/rclone/host-contracts/'+name]=frozen['all_package_inputs'][name]
    require(context['selected_specs']==[spec] and context['contract_files']==selected and build['suite']==spec
        and build['suite_sha256']==selected[spec] and build['freeze_sha256']==sha256(project/'reviewed-contract-freeze.json'),
        'actual delivered suite/fixtures/oracles changed')
    require(build['mode']==final['mode']==args.mode and build['target_pin']==review['pin']
        and build['source_path']==fault['path'] and build['pristine_source_sha256']==fault['original_source_sha256']
        and build['executed_source_sha256']==fault['mutated_source_sha256' if red else 'original_source_sha256']
        and (build['executed_binary_sha256']!=build['pristine_binary_sha256'])==red
        and bool(build['actual_mutation_build'])==red,'wrong actual compiled source fault')
    target_key='artifacts/runner-readiness-ten-project-pass/active/rclone/bin/rclone'
    require(context['target_binaries']=={target_key:build['executed_binary_sha256']},'public context selected another target executable')
    require(report['runner_version']=='source-'+candidate['source_revision']
        and report['summary']==dict(total=1,passed=int(not red),failed=int(red),cancelled=0,not_run=0)
        and row['status']==('failed' if red else 'passed') and row['spec_version']==3
        and Path(row['spec_path'].replace('\\','/')).name=='N02.json'
        and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'] and row['workspace']['id']==row['invocation_id'],
        'actual public report/cleanup differs')
    contract=load(project/'contracts/N02.json')
    for step in row['steps']:
        if 'state' in step:require(step['state']['invocation_id']==row['invocation_id']
            and step['state']['workspace_id']==row['workspace']['id'],'cross-execution state evidence')
    if red:
        require(row['failure']['category']=='state_assertion_failure' and row['target']['exited'] and row['target']['exit_code']==0,
            'wrong actual source fault diagnosis')
        failed=next(i for i,s in enumerate(row['steps']) if s['status']=='failed');prior=row['steps'][:failed]
        require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
            and sum(s.get('state',{}).get('kind')=='file' for s in prior)==2
            and row['steps'][failed]['state']['kind']=='entries' and row['steps'][failed]['state']['path']=='.',
            'missing actual success-screen/exact-file/exit false-green calibration')
    else:require(len(row['steps'])==len(contract['steps']) and all(s['status']=='passed' for s in row['steps']),'incomplete positive public evidence')
    require(final['report_sha256']==sha256(packet/'results.json') and final['context_sha256']==sha256(packet/'context.json')
        and final['target_build_sha256']==sha256(packet/'target-build.json') and final['actual_expected_public_outcome']
        and final['restored_binary_sha256']==build['pristine_binary_sha256'] and final['source_and_runtime_removed'],
        'unconfirmed actual target restoration/cleanup')
    evidence=packet/'build-evidence';total=0
    for name,digest in final['evidence_files'].items():
        path=packet_file(evidence,name,4*1024**2);require(sha256(path)==digest,'changed retained build evidence');total+=path.stat().st_size
    require(total==final['evidence_bytes'] and total<=32*1024**2,'CI evidence byte denominator differs')
    retained=evidence/'rclone/retained-source';original=load(retained/'build.json');runtime=load(retained/'runtime.json')
    require(sha256(retained/'build.json')==build['target_build_sha256'] and sha256(retained/'runtime.json')==build['target_runtime_sha256']
        and original['pin']==review['pin'] and original['binary_sha256']==build['pristine_binary_sha256'],'original target build differs')
    removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/rclone' and removed['source_archive_sha256']==review['archive_sha256']
        and prepared['runtime_processes_verified'] and prepared['managed_cleanup_verified'],'source/runtime removal proof differs')
    ledger=object.__new__(Campaign);ledger.raw=evidence;events=ledger.attempts()
    prefix='artifacts/runner-readiness-ten-project-pass/active/rclone/'
    def witness(identity,mutated=False,compiled=None):
        event=events[identity];end=event['finished']
        require('launched' in event and end['category']=='passed' and end['exit_code']==0
            and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'actual prerequisite build/cleanup failed')
        manifest=load_manifest(evidence,event['identified']['identity']);files=manifest['files'];source=dict(review['reviewed_inputs'])
        if mutated:source[fault['path']]=fault['mutated_source_sha256']
        require({n[len(prefix+'src/'):]:h for n,h in files.items() if n.startswith(prefix+'src/')}==source,'actual build source catalog differs')
        require(files[prefix+'toolchain/go/bin/go']==runtime['compiler_sha256'],'actual build compiler differs')
        if compiled:require(files[target_key]==compiled,'actual restored executable differs')
        require(sha256(evidence/'rclone'/identity/'console.log')==end['console_sha256'],'actual prerequisite output differs')
    witness(original['build_attempt'])
    if red:
        witness(build['actual_mutation_build'],True)
        restored=[identity for identity,event in events.items() if event['started']['label']=='delivered-ci-exact-original-writer-restore']
        require(len(restored)==1,'ambiguous actual restoration compile');witness(restored[0])
    cleanup=[identity for identity,event in events.items() if event['started']['label']=='delivered-ci-owned-target-cleanup']
    require(len(cleanup)==1,'ambiguous actual target removal');witness(cleanup[0],compiled=build['pristine_binary_sha256'])
    require((packet/'report.html').is_file() and (packet/'report.html').stat().st_size<=8*1024**2,'missing/bounded actual offline HTML')
    immutable_json(docs/'archive-experience'/('delivered-ci-'+args.mode+'.json'),dict(run=args.run,mode=args.mode,
        workflow_commit=metadata['headSha'],source_revision=candidate['source_revision'],runner_sha256=context['runner_sha256'],
        invocation_id=row['invocation_id'],report_sha256=sha256(packet/'results.json'),context_sha256=sha256(packet/'context.json'),
        html_sha256=sha256(packet/'report.html'),build_sha256=sha256(packet/'target-build.json'),finalized_sha256=sha256(packet/'target-finalized.json'),
        evidence_bytes=total,final_archive_credit=0,real_pr_event_proven=False,
        scope='Actual delivered source-build/list/context/test/report/summary/artifact job, reviewed owned-SDK/event/cleanup adapters, real compiled Rclone writer, unchanged public same-execution state oracle and checked exact restoration/removal. Source-built runner; no exact-archive repetition or real-PR event credit.'))
    print('Independently verified actual delivered CI control:',args.mode)


if __name__=='__main__':main()
