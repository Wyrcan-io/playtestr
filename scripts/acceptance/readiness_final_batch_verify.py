"""Audit actual twelve-batch reports against frozen inputs and launch identities."""
from pathlib import Path

from readiness_evidence import sha256
from readiness_new_control_matrix import read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def verify_batches(packet,docs,profile,host,candidate,cell,installed,build,events,witness):
    project=docs.name;target=packet/project;package=target/'host-contracts'
    frozen=load(profile/'reviewed-contract-freeze.json')
    require(len(frozen['contracts'])==20,'twenty canonical cases required')
    for name,digest in frozen['all_package_inputs'].items():require(sha256(package/name)==digest,'native canonical input changed')
    final=target/'final-series';intent=load(final/'intent.json');declaration=load(docs/'final-series-declaration.json')
    require(intent['host']==host and intent['declaration_file']=='final-series-declaration.json'
        and intent['declaration_sha256']==sha256(docs/'final-series-declaration.json')
        and declaration['candidate_freeze_sha256']==sha256(docs.parent/'migration-candidate-freeze.json')
        and intent['runner_sha256']==cell['binary_sha256'] and intent['archive_sha256']==cell['archive_sha256']
        and intent['target_build_sha256']==sha256(target/'retained-source/build.json') and intent['target_pin']==build['pin']
        and intent['canonical_package_inputs']==frozen['all_package_inputs'],'different final intent')
    require(len(declaration['batches'])==12 and [b['number'] for b in declaration['batches']]==list(range(12)),
        'invalid twelve-batch declaration')
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
            require(sha256(profile/'contracts'/name)==frozen['contracts'][name],'canonical contract hash changed')
            if batch['input_chunks']:
                size=batch['input_chunks'];steps=[]
                allowed=declaration.get('segmented_text_steps_by_host',{}).get(host,{}).get(name)
                for step_number,step in enumerate(before['steps'],1):
                    if set(step)=={'text'} and len(step['text'])>size and (allowed is None or step_number in allowed):
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
                and observed['report_sha256']==sha256(report_path) and observed['invocation_id']==row['invocation_id']
                and row['spec_version']==3 and Path(row['spec_path'].replace('\\','/')).name==name,'actual report differs')
            result_ok(row,'passed')
            require(len(row['steps'])==len(contract['steps']) and all(s['status']=='passed' for s in row['steps']),'incomplete positive evidence')
            event=events[identity]['started']
            require(event['label']=='final-batch-'+str(batch['number'])+'-'+name
                and event['variation']==('owned 2-second 8-MiB SHA256 CPU worker' if batch['contention'] else 'ordinary'),'schedule differs')
            files=witness(identity,public=True)
            require(files[installed['binary']]==cell['binary_sha256'],'actual exact-archive executable differs')
            bind_inputs(files,current,contract,name,prepared['package_inputs']);rows.append(observed)
        complete=load(folder/'complete.json')
        require(complete['observed']==20 and complete['records']==rows[-20:],'incomplete actual batch')
    require(len(rows)==240 and len(invocations)==240,'incorrect ordinary denominator')
    return rows,commands,result_ok,bind_inputs
