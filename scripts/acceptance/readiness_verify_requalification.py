"""Verify earlier-project requalification from actual current-source native packets."""
import argparse
from pathlib import Path

from readiness_edit_verify_native import SOURCE,require
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_file,read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['plop','poetry','rubygems'],required=True)
    parser.add_argument('--run',required=True);parser.add_argument('--source-revision',default=SOURCE)
    args=parser.parse_args();project=args.project
    source_revision=args.source_revision
    require(len(source_revision)==40 and all(c in '0123456789abcdef' for c in source_revision),'invalid source revision')
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    run=RAW/'native'/args.run;metadata=load(run/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success','native requalification incomplete or failed')
    require(len(metadata['jobs'])==2 and all(j['status']=='completed' and j['conclusion']=='success' for j in metadata['jobs']),'missing successful native jobs')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'/project
    canonical={p.name:sha256(p) for p in docs.glob('*.json') if p.name.startswith(('normal-','edge-'))}
    require(len(canonical)==20,'twenty canonical contracts required')
    hosts=['playtestr-Linux','playtestr-Windows' if project=='rubygems' else 'playtestr-macOS'];cells=[]
    for host in hosts:
        base=run/host;packet=base/'runner-readiness-ten-project-pass'
        ledger=object.__new__(Campaign);ledger.raw=packet;attempts=ledger.attempts()
        runner=load(packet/(project+'-native-runner.json'))
        require(runner['source_revision']==source_revision and runner['candidate_sha256']==runner['copied_sha256'],'wrong requalification runner')
        suffix='.exe' if host.endswith('Windows') else ''
        runner_keys=['artifacts/runner-readiness-ten-project-pass/bin/playtestr'+suffix,'.playtestr-bin/playtestr'+suffix]
        def witness(identity,expected):
            events=attempts[identity];require('launched' in events,'missing actual launch')
            require(events['started']['expected_exit']==expected,'wrong expected command exit')
            finished=events['finished']
            require(finished['category']=='passed' and finished['exit_code']==expected and not finished['cleanup_errors'] and
                finished['harness_cleanup']=='harness_process_reaped','command outcome/cleanup mismatch')
            reference=events['identified']['identity'];path=packet_file(packet,reference['manifest'],1024**2)
            require(sha256(path)==reference['sha256'],'changed identity manifest')
            console=packet_file(packet,events['started']['project']+'/'+identity+'/console.log',4*1024**2)
            require(sha256(console)==finished['console_sha256'],'changed actual command output')
            return load(path)['files']
        def result_ok(result,status):
            require(result['status']==status and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'test result/cleanup mismatch')
            for step in result['steps']:
                if 'state' in step:
                    require(step['state']['invocation_id']==result['invocation_id'] and step['state']['workspace_id']==result['workspace']['id'],'cross-execution state')
        package=packet/project/'host-contracts';profile=load(packet/project/'host-profile.json')
        require(len(profile['contracts'])==20 and {r['spec'] for r in profile['contracts']}==set(canonical),'wrong profile selection')
        for row in profile['contracts']:
            require(row['source_sha256']==canonical[row['spec']] and row['authored_sha256']==sha256(package/row['spec']),'unreviewed native profile bytes')
        report=load(base/'playtestr/results.json')
        require(report['runner_version']=='source-'+source_revision and report['summary']==dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'incomplete exact-source ordinary suite')
        require({Path(r['spec_path'].replace('\\','/')).name for r in report['results']}==set(canonical),'wrong executed suite')
        for result in report['results']:result_ok(result,'passed')
        suites=[key for key,row in attempts.items() if row['started']['label']=='public-recorded-suite']
        require(len(suites)==1,'missing or ambiguous ordinary suite witness');files=witness(suites[0],0)
        require(any(files.get(key)==runner['copied_sha256'] for key in runner_keys),'ordinary runner binary not bound')
        for name in canonical:
            require(files['artifacts/runner-readiness-ten-project-pass/'+project+'/host-contracts/'+name]==sha256(package/name),'ordinary contract identity missing')
        summaries=list((packet/project/'faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous fault batch')
        summary_path=summaries[0];faults=load(summary_path)['faults']
        require(len(faults)==3 and {f['id'] for f in faults}=={'F01','F02','F03'},'missing real source faults')
        for fault in faults:
            require(not fault['held_out'],'replica mislabeled as another holdout')
            if project=='plop':
                source='artifacts/runner-readiness-ten-project-pass/active/plop/src/'+fault['source']
                original=fault['restored_source_sha256'];ids=[fault['baseline'],fault['mutated'],fault['restored']]
                spec_name={'F01':'normal-version.json','F02':'edge-continue-after-error.json','F03':'normal-artifact.json'}[fault['id']]
            else:
                prefix='src/poetry/' if project=='poetry' else 'lib/'
                source='artifacts/runner-readiness-ten-project-pass/active/'+project+'/src/'+prefix+fault['path']
                original=fault['original_source_sha256'];ids=[fault['baseline_attempt'],fault['mutation_attempt'],fault['restored_attempt']]
                spec_name=fault['spec']
                require(fault['restored_exact'],'missing exact source restoration')
            for phase,event,expected,digest in zip(['baseline','mutated','restored'],ids,[0,1,0],[original,fault['mutated_source_sha256'],original]):
                files=witness(event,expected)
                require(files[source]==digest and any(files.get(k)==runner['copied_sha256'] for k in runner_keys),'actual source or runner identity mismatch')
                require(files['artifacts/runner-readiness-ten-project-pass/'+project+'/host-contracts/'+spec_name]==sha256(package/spec_name),'fault contract changed between phases')
                outcome=load(summary_path.parent/(fault['id']+'-'+phase+'.json'))['results'][0]
                result_ok(outcome,'failed' if expected else 'passed')
                if fault['id']=='F03' and phase=='mutated':
                    require(outcome['failure']['category']=='state_assertion_failure','false-green fault missed by public state')
                    failed=next(i for i,s in enumerate(outcome['steps']) if s['status']=='failed');prior=outcome['steps'][:failed]
                    require(all(s['status']=='passed' for s in prior) and any(s['action'] in {'expect','snapshot'} for s in prior) and
                        any(s['action']=='exit' for s in prior),'state control lacks earlier passing screen/exit')
        journeys=list((packet/project).glob('maintenance*/journey.json'));require(len(journeys)==1,'ambiguous public maintenance')
        journey_path=journeys[0];journey=load(journey_path)
        require(len(journey['attempts'])>=11 and journey['maintained_spec_sha256']==journey['relocated_spec_sha256'],'incomplete maintenance or changed relocation')
        for row in journey['attempts']:witness(row['id'],1 if row['label'].startswith('intended-') else 0)
        file_spec,index={'plop':('normal-artifact.json',6),'poetry':('normal-version.json',2),'rubygems':('normal-set-path.json',2)}[project]
        maintained=journey_path.parent/('original route' if project=='plop' else 'package')/file_spec
        require(sha256(maintained)==journey['maintained_spec_sha256'],'maintained contract changed')
        current=load(maintained);original=load(package/file_spec);current['steps'][index]=original['steps'][index]
        require(current==original,'selected maintenance changed unrelated expectations')
        retained=packet/project/'retained-source';removed=load(retained/'removed.json');restore=load(retained/'verified-index.json')
        require(removed['removed'] and removed['owned_relative_path']=='active/'+project and removed['source_archive_sha256']==restore['archive_sha256'],'source cleanup/archive mismatch')
        canonical_archive=RAW/project/'retained-source/source.tar.gz'
        require(restore['archive_sha256']==load(RAW/project/'retained-source/acquisition.json')['archive_sha256']==sha256(canonical_archive),'native source differs from canonical acquired pin')
        candidate=next(r for r in load(docs.parent/'candidates.json')['rows'] if r['repository']=={'plop':'plopjs/plop','poetry':'python-poetry/poetry','rubygems':'ruby/rubygems'}[project])
        owner=load(retained/'task-owned.json');require(owner['pin']==candidate['pin'] and owner['project']==candidate['repository'],'wrong native source pin')
        if (retained/'source.tar.gz').exists():require(sha256(retained/'source.tar.gz')==restore['archive_sha256'],'native source archive changed')
        for name in restore['selected_restore']:require(sha256(retained/'selected-restore'/name)==restore['files'][name]['sha256'],'selected restore changed')
        cells.append(dict(host=host,scenarios=20,runner_sha256=runner['copied_sha256'],report_sha256=sha256(base/'playtestr/results.json'),
            source_fault_summary_sha256=sha256(summary_path),maintenance_sha256=sha256(journey_path),cleanup_receipt_sha256=sha256(retained/'removed.json')))
    output=RAW/project/('requalification-'+args.run+'.json')
    immutable_json(output,dict(schema_version=1,project=project,run=args.run,runner_source=source_revision,cells=cells,
        claim='Earlier-project development requalification only; no new project/cell or final archive credit.'))
    print('Verified earlier-project native requalification:',project,args.run)


if __name__=='__main__':main()
