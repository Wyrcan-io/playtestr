"""Independently count and bind the bounded fff incident observations."""
import argparse
from pathlib import Path

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native incident run')
    parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==1
            and metadata['jobs'][0]['name']=='linux-incident' and metadata['jobs'][0]['conclusion']=='success',
            'complete native investigation and cleanup job required')
    base=parent/'fff-r3-Linux';docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/fff'
    declaration=load(docs/'r3-batch-declaration.json');freeze=load(docs/'reviewed-contract-freeze.json')
    candidate=load(docs.parent/'migration-candidate-freeze.json');cell=next(c for c in candidate['cells'] if c['host']=='linux')
    installed=load(base/'private-install/migration-v2/linux-amd64/installation.json')
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256'],
            'different actual private archive')
    roots=list((base/'fff/r3-batches').glob('*/complete.json'));require(len(roots)==1,'missing or ambiguous complete investigation')
    root=roots[0].parent;intent=load(root/'intent.json')
    require(load(roots[0])==dict(completed_batches=3,observed=150,final_archive_credit=0)
            and intent['declaration_sha256']==sha256(docs/'r3-batch-declaration.json')
            and intent['canonical_package_inputs']==freeze['all_package_inputs']
            and intent['runner_sha256']==cell['binary_sha256'] and intent['archive_sha256']==cell['archive_sha256'],
            'incident declaration or candidate identity differs')
    retained=base/'fff/retained-source';source_review=load(docs/'source-review.json')
    require(sha256(retained/'source.tar.gz')==source_review['archive_sha256']
            and load(retained/'task-owned.json')['pin']==declaration['target_pin']
            and load(retained/'removed.json')['removed']
            and load(retained/'removal-prepared.json')['runtime_processes_verified'],
            'pinned source retention or actual removal differs')
    def key(path):return 'artifacts/runner-readiness-ten-project-pass/'+path.relative_to(base).as_posix()
    def reference(value):
        prefix='artifacts/runner-readiness-ten-project-pass/'
        require(value.startswith(prefix),'incident report reference escapes campaign')
        return packet_file(base,value.removeprefix(prefix),4*1024**2)
    observations=[];invocations=set();workspaces=set();commands=set()
    for batch in declaration['batches']:
        folder=root/('batch-'+str(batch['number']));summary=load(folder/'complete.json')
        package=folder/('relocated caf\u00e9 \u96ea' if batch['number']==3 else 'contracts')
        require({p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
                ==freeze['all_package_inputs'],'relocation changed approved contract or fixture bytes')
        actual=[];planned=list(folder.glob('*-planned.json'));require(len(planned)==50,'batch planned denominator differs')
        for path in planned:
            identity=path.name.removesuffix('-planned.json');plan=load(path);row=load(folder/(identity+'-observed.json'))
            number=plan['number'];loaded=batch['number']==2 and number%10==0
            require(plan==dict(batch=batch['number'],number=number,seed=batch['seed'],
                controlled_two_second_worker=loaded,contract_sha256=sha256(package/'E03.json'))
                and row['number']==number,'declared attempt schedule differs')
            command=row['command_attempt'];require(command not in commands,'duplicate incident command');commands.add(command)
            events={kind:load(base/'events'/(command+'-'+kind+'.json')) for kind in ['started','identified','launched','finished']}
            require(all(r['event']==kind and r['id']==command and r['project']=='fff'
                        and r['label']=='r3-E03-batch-'+str(batch['number'])+'-attempt-'+str(number)
                        for kind,r in events.items()),'actual incident command identity differs')
            finished=events['finished'];report=reference(row['report']);value=load(report);result=value['results'][0]
            status=result['status'];expected=0 if status=='passed' else 1
            require(status in {'passed','failed'} and finished['exit_code']==expected
                    and finished['category']==('passed' if expected==0 else 'exit_mismatch')
                    and finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'],
                    'actual outcome or controlled worker cleanup differs')
            require(events['started']['variation']==('owned 2-second 8-MiB SHA256 CPU worker' if loaded else 'ordinary'),
                    'actual contention schedule differs')
            manifest_reference=events['identified']['identity'];manifest=packet_file(base,manifest_reference['manifest'].replace('\\','/'),2*1024**2)
            require(sha256(manifest)==manifest_reference['sha256'],'changed prelaunch manifest')
            files=load(manifest)['files']
            require(files[installed['binary']]==cell['binary_sha256']
                    and files[key(package/'E03.json')]==freeze['contracts']['E03.json']
                    and files['artifacts/runner-readiness-ten-project-pass/active/fff/src/fff']==source_review['reviewed_inputs']['fff'],
                    'actual executed runner, contract or source differs')
            contract=load(package/'E03.json')
            for path in (package/contract['workspace']['fixture']).rglob('*'):
                if path.is_file():require(files[key(path)]==sha256(path),'actual initial fixture input differs')
            for step in contract['steps']:
                if 'snapshot' in step:
                    path=package/'snapshots'/step['snapshot']
                    require(files[key(path)]==sha256(path),'actual selected snapshot differs')
            require(sha256(report)==row['report_sha256'] and value['runner_version']==candidate['version']
                    and value['summary']==dict(total=1,passed=int(expected==0),failed=int(expected==1),cancelled=0,not_run=0)
                    and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned']
                    and row['status']==status and row['failure']==result.get('failure'),
                    'actual report or managed cleanup differs')
            require(sha256(base/'fff'/command/'console.log')==finished['console_sha256'],'incident console changed')
            if not expected:require(len(result['steps'])==len(load(package/'E03.json')['steps']) and all(s['status']=='passed' for s in result['steps']),
                'incident pass lacks complete positive step evidence')
            require(result['invocation_id'] not in invocations and result['workspace']['id'] not in workspaces,
                    'fresh incident invocation/workspace reused')
            invocations.add(result['invocation_id']);workspaces.add(result['workspace']['id'])
            for step in result['steps']:
                if 'state' in step:require(step['state']['invocation_id']==result['invocation_id']
                    and step['state']['workspace_id']==result['workspace']['id'],'cross-execution incident state')
            if not expected:
                for declared,observed in zip(contract['steps'],result['steps']):
                    if 'state' in declared:
                        require(observed['state']['kind']==declared['state']['kind']
                                and observed['state']['path']==declared['state']['path']
                                and observed['state']['outcome']=='matched','positive saved-state checkpoint differs')
            actual.append(row)
        require({r['number'] for r in actual}==set(range(50)) and sorted(actual,key=lambda r:r['number'])==summary['attempts']
                and summary['observed']==50 and summary['passed']==sum(r['status']=='passed' for r in actual)
                and summary['failed']==sum(r['status']=='failed' for r in actual),'batch summary differs from actual attempts')
        observations.append(dict(batch=batch['number'],passed=summary['passed'],failed=summary['failed'],summary_sha256=sha256(folder/'complete.json')))
    require(len(commands)==len(invocations)==len(workspaces)==150,'actual incident denominator differs')
    immutable_json(docs/'r3-batch-observations.json',dict(schema_version=1,run=args.run,
        native_metadata_sha256=sha256(parent/'run-metadata.json'),batches=observations,observed=150,
        passed=sum(r['passed'] for r in observations),failed=sum(r['failed'] for r in observations),
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],
        disposition='Bounded current Linux E03 observations only; the original failed run and unexplained cause remain preserved. No zero-flake or universal compatibility claim.',
        cleanup_sha256=sha256(retained/'removed.json'),new_project_credit=0,final_archive_credit=0))
    print('Independently audited 150 actual incident outcomes:',observations)


if __name__=='__main__':main()
