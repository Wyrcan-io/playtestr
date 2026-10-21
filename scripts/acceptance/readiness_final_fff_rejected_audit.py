"""Audit rejected final fff series directly from verified retained archives."""
import hashlib
import json
import tarfile

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def require(value,message):
    if not value:
        raise RuntimeError(message)


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    declaration=load(docs/'fff/final-series-declaration.json')
    candidate=load(docs/'migration-candidate-freeze.json')
    source_review=load(docs/'fff/source-review.json')
    run='39562308064';cells=[]
    for host,generation,denominator in [('linux',5,91),('macos',6,123)]:
        retained=RAW/'fff'/('retained-native-v'+str(generation))
        index=load(retained/'index.json',maximum=4*1024**2)
        require(load(retained/'expanded-removed.json')['all_expanded_removed'], 'expanded packet removal incomplete')
        require(sha256(retained/'packets.tar.gz')==index['archive_sha256'], 'retained archive changed')
        with tarfile.open(retained/'packets.tar.gz') as archive:
            def payload(name):
                record=index['files'][name]
                data=archive.extractfile(record.get('member',name)).read(4*1024**2+1)
                require(len(data)<=4*1024**2 and hashlib.sha256(data).hexdigest()==record['sha256'],'retained payload changed')
                return data
            def read(name):return json.loads(payload(name).decode('utf-8-sig'))
            prefix='native/'+run+'/final-fff-'+('Linux' if host=='linux' else 'macOS')+'/'
            def get(name):return read(prefix+name)
            def digest(name):
                payload(prefix+name)
                return index['files'][prefix+name]['sha256']
            metadata=read('native/'+run+'/run-metadata.json')
            require(metadata['status']=='completed' and metadata['conclusion']=='failure' and len(metadata['jobs'])==2
                    and all(j['status']=='completed' and j['conclusion']=='failure' for j in metadata['jobs']),
                    'actual rejected native jobs differ')
            require(all(any(s['name']=='Verify target termination and remove only owned source/runtime'
                    and s['conclusion']=='success' for s in j['steps']) for j in metadata['jobs']), 'native cleanup step not successful')
            cell=next(c for c in candidate['cells'] if c['host']==('darwin' if host=='macos' else host))
            installation=get('private-install/migration-v2/'+('darwin-arm64' if host=='macos' else 'linux-amd64')+'/installation.json')
            require(installation['binary_sha256']==cell['binary_sha256'] and installation['archive_sha256']==cell['archive_sha256'], 'different actual archive')
            native_docs=docs/'fff'/('native-profiles/macos' if host=='macos' else '.')
            frozen=load(native_docs/'reviewed-contract-freeze.json')
            intent=get('fff/final-series/intent.json');build=get('fff/retained-source/build.json')
            require(intent['declaration_sha256']==sha256(docs/'fff/final-series-declaration.json')
                    and intent['canonical_package_inputs']==frozen['all_package_inputs']
                    and intent['runner_sha256']==cell['binary_sha256'] and intent['archive_sha256']==cell['archive_sha256']
                    and intent['target_build_sha256']==digest('fff/retained-source/build.json')
                    and intent['target_pin']==build['pin']==get('fff/retained-source/task-owned.json')['pin'], 'series intent differs')
            require(build['binary_sha256']==source_review['reviewed_inputs']['fff']
                    and get('fff/retained-source/removed.json')['removed']
                    and get('fff/retained-source/removal-prepared.json')['runtime_processes_verified'], 'source identity or cleanup differs')
            invocations=set();commands=set();observed=[];failed=[]
            for batch in declaration['batches']:
                folder='fff/final-series/'+str(batch['number'])+'/'
                prepared=get(folder+'prepared.json')
                require(prepared['batch']==batch, 'batch declaration differs')
                package=folder+batch['package_directory']+'/'
                require(set(prepared['package_inputs'])==set(frozen['all_package_inputs']), 'native package coverage changed')
                for name,h in prepared['package_inputs'].items():
                    require(digest(package+name)==h, 'prepared package bytes changed')
                    if name not in frozen['contracts']:
                        require(h==frozen['all_package_inputs'][name], 'fixture or snapshot weakened')
                for number,name in enumerate(sorted(frozen['contracts'])):
                    canonical=load(native_docs/'contracts'/name)
                    require(sha256(native_docs/'contracts'/name)==frozen['contracts'][name], 'canonical contract changed')
                    expected=dict(canonical)
                    if batch['input_chunks']:
                        steps=[];size=batch['input_chunks']
                        for step in canonical['steps']:
                            if set(step)=={'text'} and len(step['text'])>size:
                                steps.extend({'text':step['text'][i:i+size]} for i in range(0,len(step['text']),size))
                            else:steps.append(step)
                        expected['steps']=steps
                    contract=get(package+name)
                    require(contract==expected, 'executed contract exceeds declared text segmentation')
                    report_name=folder+name+'.report.json'
                    if prefix+report_name not in index['files']:continue
                    require(not failed, 'attempts continued after the rejected batch')
                    plan=get(folder+name+'.planned.json')
                    require(plan==dict(batch=batch['number'],number=number,spec=name,runner_sha256=cell['binary_sha256'],
                        archive_sha256=cell['archive_sha256'],spec_sha256=digest(package+name),
                        prepared_sha256=digest(folder+'prepared.json'),owned_two_second_worker=batch['contention']), 'case launch declaration differs')
                    report=get(report_name);row=report['results'][0];status=row['status'];expected_exit=0 if status=='passed' else 1
                    require(report['runner_version']==candidate['version'] and report['summary']==dict(total=1,passed=int(not expected_exit),
                        failed=expected_exit,cancelled=0,not_run=0) and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'], 'actual outcome/cleanup differs')
                    require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations, 'fresh workspace/invocation reused')
                    invocations.add(row['invocation_id'])
                    if not expected_exit:
                        outcome=get(folder+name+'.observed.json');command=outcome['attempt']
                        require(outcome['report_sha256']==digest(report_name) and outcome['invocation_id']==row['invocation_id'], 'observed report identity differs')
                        require(len(row['steps'])==len(contract['steps']) and all(s['status']=='passed' for s in row['steps']), 'passing step evidence incomplete')
                    else:
                        matches=[]
                        for n in index['files']:
                            if n.startswith(prefix+'events/') and n.endswith('-started.json'):
                                event=read(n)
                                if event['project']=='fff' and event['label']=='final-batch-'+str(batch['number'])+'-'+name:matches.append(event['id'])
                        require(len(matches)==1, 'failed actual command witness ambiguous')
                        command=matches[0];failed.append(dict(batch=batch['number'],spec=name,invocation_id=row['invocation_id'],
                            failure=row['failure'],report_sha256=digest(report_name)))
                    require(command not in commands,'duplicate actual command');commands.add(command)
                    events={k:get('events/'+command+'-'+k+'.json') for k in ['started','identified','launched','finished']}
                    require(all(e['id']==command and e['event']==k and e['project']=='fff' for k,e in events.items()), 'launch identity differs')
                    finished=events['finished'];require(finished['exit_code']==expected_exit
                        and finished['category']==('exit_mismatch' if expected_exit else 'passed')
                        and finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'], 'command or worker cleanup differs')
                    reference=events['identified']['identity'];manifest=reference['manifest'].replace('\\','/')
                    require(digest(manifest)==reference['sha256'], 'actual prelaunch manifest changed')
                    files=get(manifest)['files'];require(files[installation['binary']]==cell['binary_sha256']
                        and files['artifacts/runner-readiness-ten-project-pass/active/fff/src/fff']==source_review['reviewed_inputs']['fff']
                        and files['artifacts/runner-readiness-ten-project-pass/'+package+name]==digest(package+name), 'actual executed bytes differ')
                    for step in row['steps']:
                        if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'], 'state came from another execution')
                    observed.append(dict(batch=batch['number'],spec=name,status=status,command=command,report_sha256=digest(report_name)))
            require(len(observed)==denominator and len(failed)==1, 'actual rejected-series accounting differs')
            cells.append(dict(host=host,observed=denominator,passed=denominator-1,failed=failed,
                archive_sha256=cell['archive_sha256'],runner_sha256=cell['binary_sha256'],retained_generation=generation,
                retained_index_sha256=sha256(retained/'index.json'),observations=observed))
    immutable_json(docs/'fff/final-first-series-rejected.json',dict(run=run,cells=cells,ordinary_observed=214,
        passed=212,failed=2,final_archive_qualified_cells=0,
        disposition='Rejected first final series. Linux E11 timed out waiting for exit after its resize/create screen passed; macOS segmented-input E03 exited0 then public same-execution state rejected missing source.txt. Original causes remain unestablished; no deadline padding, target repair, oracle update or automatic retry is claimed. Earlier 150 Linux E03 passes do not erase these different observed failures.'))
    print('Independently audited rejected fff final series: 214 actual ordinary outcomes, 212 pass/2 fail; zero qualified cells.')


if __name__=='__main__':main()
