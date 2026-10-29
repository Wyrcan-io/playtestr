"""Challenge normalized actual PDM cells while keeping admission explicitly closed."""
import copy
import hashlib
import json
import lzma
import uuid

from next20_check import DOC, RAW
from next20_local_records import read_packet as local_packet
from next20_native_packet_reader import read_packet as native_packet
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    package=DOC/'pdm';_,local=local_packet('pdm');_,completed=local_packet('pdm',packet='retained-complete-final-v2')
    _,rejected=local_packet('pdm',packet='retained-failed-final-v1');_,native=native_packet('pdm',3)
    require(not set(local)&set(completed),'overlapping retained ordinary records')
    windows={**local,**completed};rejection=json.loads((package/'windows-first-final-rejection.json').read_text())
    for row in rejection['observations']:require(hashlib.sha256(rejected[row['report']]).hexdigest()==row['sha256'],'original rejected report missing/changed')
    destination=RAW/'pdm/audit-controls'/uuid.uuid4().hex;destination.mkdir(parents=True)
    cells=[];canonical={c['id'] for c in json.loads((package/'scenarios.json').read_text())['cases']}
    candidate=json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())
    scope='artifacts/'+RAW.name+'/'
    def bytes_for(records,prefix,name):
        name=name.replace('\\','/').removeprefix(scope)
        key=prefix+name
        return records[key] if key in records else (RAW/name).read_bytes()
    for host,records,prefix,suffix in [('windows',windows,'','-v2'),('linux',native,'native/40869293414/next20-pdm-linux-final/','')]:
        def load(name):return json.loads(bytes_for(records,prefix,name).decode('utf-8-sig'))
        complete=load('pdm/final-execution-summary'+suffix+'.json');runtime=load('pdm/retained-source/runtime.json')
        faults=load(complete['fault_summary']);native_cases={c['id']:c for c in load('pdm/host-contracts/scenarios.json')['cases']}
        expected_candidate=next(r for r in candidate['cells'] if r['host']==host)
        def normalize(report,eid,phase,spec):
            row=report['results'][0];started=load('events/'+eid+'-started.json')
            require(started['phase']=='final-archive','actual event wrong phase')
            return dict(attempt=eid,phase=started['phase'] if phase=='ordinary' else phase,status=row['status'],
                category=row.get('failure',{}).get('category'),invocation=row['invocation_id'],workspace=row['workspace']['id'],
                confirmed_exited=row['cleanup']['confirmed_exited'],cleaned=row['workspace']['cleaned'],
                target_exit=row.get('target',{}).get('exit_code'),runner_sha256=expected_candidate['binary_sha256'],
                expected_actions=[next(iter(s)) for s in spec['steps']],
                steps=[dict(action=s['action'],status=s['status'],state=s.get('state')) for s in row['steps']])
        model=dict(project='pdm',repository='pdm-project/pdm',host=host,candidate='v0.4.0-rc.6',
            archive_sha256=expected_candidate['archive_sha256'],runner_sha256=expected_candidate['binary_sha256'],
            runtime_sha256=hashlib.sha256(bytes_for(records,prefix,'pdm/retained-source/runtime.json')).hexdigest(),
            helper_source_revision='8454a1f34e873582311afc1ad851411fa0abcf04' if host=='windows' else '5ccd20b8ce38c3496ca5e5095819f1272dcf9e81',
            required_index_sha256=sha256(RAW/'pdm'/('retained-local-v1' if host=='windows' else 'retained-native-v3')/'index.json'),
            project_admitted=False,historical_frames_complete=False,
            first_rejection_sha256=sha256(package/'windows-first-final-rejection.json'),ordinary=[],faults=[])
        expected_specs={}
        folder='pdm/final-series-native-exit-v1'+suffix+'/'
        for batch in range(12):
            base=folder+str(batch)+'/';summary=load(base+'summary.json')
            for item in summary['observations']:
                cid=item['case'];planned=load(base+cid+'.planned.json');spec=load(planned['spec'])
                actual=normalize(load(base+cid+'.report.json'),item['attempt'],'ordinary',spec)
                actual.update(batch=batch,case=cid,spec_sha256=planned['spec_sha256']);model['ordinary'].append(actual)
                expected_specs[(batch,cid)]=planned['spec_sha256']
        declared={f['id']:f for f in json.loads((package/'fault-declaration.json').read_text())['faults']}
        primary=load('pdm/host-contracts/'+json.loads((package/'fault-declaration.json').read_text())['primary_spec'])
        for fault in faults['faults']:
            outcomes=[normalize(load(p['report']),p['attempt'],p['phase'],primary) for p in fault['outcomes']]
            model['faults'].append(dict(id=fault['id'],original_sha256=fault['original_sha256'],mutated_sha256=fault['mutated_sha256'],
                restored_sha256=fault['restored_sha256'],restored_exact=fault['restored_exact'],outcomes=outcomes))
        baseline=dict(runtime=model['runtime_sha256'],helper=model['helper_source_revision'],index=model['required_index_sha256'])
        def validate(value):
            require(value['project']=='pdm' and value['repository']=='pdm-project/pdm' and value['host']==host,'wrong/duplicate canonical project')
            require(value['candidate']=='v0.4.0-rc.6' and value['archive_sha256']==expected_candidate['archive_sha256'] and value['runner_sha256']==expected_candidate['binary_sha256'],'wrong/mixed candidate')
            require(value['runtime_sha256']==baseline['runtime'] and value['helper_source_revision']==baseline['helper'] and value['required_index_sha256']==baseline['index'],'wrong actual runtime/helper/required retained payload')
            require(not value['project_admitted'] and value['historical_frames_complete'] is False,'unreported history gap or false admission')
            require(value['first_rejection_sha256']==sha256(package/'windows-first-final-rejection.json'),'missing original rejected window')
            require(len(value['ordinary'])==240,'partial ordinary matrix');invocations=set();attempts=set()
            def outcome(row,status):
                require(row['status']==status and row['confirmed_exited'] and row['cleaned'],'false outcome or unconfirmed cleanup')
                require(row['invocation']==row['workspace'] and row['invocation'] not in invocations and row['attempt'] not in attempts,'cross/duplicate invocation or attempt')
                invocations.add(row['invocation']);attempts.add(row['attempt'])
                require([s['action'] for s in row['steps']]==row['expected_actions'],'missing actual action')
                if status=='passed':require(all(s['status']=='passed' for s in row['steps']),'nonpositive passing steps')
                else:require(any(s['status']=='failed' for s in row['steps']),'missing actual mutation failure')
                for step in row['steps']:
                    if step['state']:require(step['state']['invocation_id']==row['invocation'] and step['state']['workspace_id']==row['workspace'],'cross-invocation saved state')
            for batch in range(12):
                rows=[r for r in value['ordinary'] if r['batch']==batch]
                require(len(rows)==20 and {r['case'] for r in rows}==canonical,'missing/duplicate batch case')
                for row in rows:
                    require(row['phase']=='final-archive' and row['runner_sha256']==value['runner_sha256'] and row['spec_sha256']==expected_specs[(batch,row['case'])],'wrong phase/runner/reviewed contract')
                    outcome(row,'passed')
            require(len(value['faults'])==3 and {f['id'] for f in value['faults']}==set(declared),'missing real source fault')
            for fault in value['faults']:
                require(fault['restored_exact'] and fault['original_sha256']==fault['restored_sha256'] and fault['mutated_sha256']!=fault['original_sha256'],'missing source restoration')
                require(len(fault['outcomes'])==3 and {r['phase'] for r in fault['outcomes']}=={'baseline','mutated','restored'},'partial calibration')
                for row in fault['outcomes']:
                    mutated=row['phase']=='mutated';outcome(row,'failed' if mutated else 'passed')
                    if mutated:
                        require(row['category']==declared[fault['id']]['category'],'wrong genuine mutation rejection')
                        if fault['id']=='F03':
                            first=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
                            require(all(s['status']=='passed' for s in row['steps'][:first]),'earlier failure posing as saved corruption')
            require(len(invocations)==249,'missing actual distinct execution')
            return dict(ordinary=240,calibrations=9,real_faults=3,project_admissions=0)
        counts=validate(model);state=next(i for i,s in enumerate(model['ordinary'][0]['steps']) if s['state'])
        patches=[('missing-case',['ordinary'],model['ordinary'][:-1]),('wrong-runtime',['runtime_sha256'],'0'*64),
            ('duplicate-project',['project'],'cargo-generate'),('changed-contract',['ordinary',0,'spec_sha256'],'0'*64),
            ('missing-restoration',['faults',0,'restored_exact'],False),('cross-state',['ordinary',0,'steps',state,'state','invocation_id'],'other'),
            ('wrong-phase',['ordinary',0,'phase'],'development'),('missing-first-failure',['first_rejection_sha256'],'0'*64),
            ('unconfirmed-descendants',['ordinary',0,'confirmed_exited'],False),('missing-payload',['required_index_sha256'],'0'*64),
            ('stale-helper',['helper_source_revision'],'0'*40),('mixed-runner',['ordinary',0,'runner_sha256'],'0'*64),
            ('waived-frame-gap',['historical_frames_complete'],True),('false-admission',['project_admitted'],True),
            ('false-green-mutation',['faults',2,'outcomes',1,'status'],'passed'),('earlier-failure-as-state',['faults',2,'outcomes',1,'steps',0,'status'],'failed')]
        controls=[]
        for label,path,replacement in patches:
            changed=copy.deepcopy(model);parent=changed
            for key in path[:-1]:parent=parent[key]
            parent[path[-1]]=replacement
            try:validate(changed)
            except ValueError as error:controls.append(dict(control=label,rejected=True,reason=str(error),path=path,
                operation='truncate' if label=='missing-case' else 'replace',value=len(replacement) if label=='missing-case' else replacement))
            else:raise ValueError('corrupted actual model accepted: '+label)
        validate(model);encoded=json.dumps(model,sort_keys=True,separators=(',',':')).encode()
        require(len(encoded)<=8*1024**2,'actual model byte bound');archive=destination/(host+'-actual-model.json.xz')
        archive.write_bytes(lzma.compress(encoded,preset=6));require(json.loads(lzma.decompress(archive.read_bytes(),memlimit=64*1024**2))==model,'actual normalized model restore differs')
        cells.append(dict(host=host,counts=counts,model=archive.relative_to(RAW).as_posix(),model_sha256=sha256(archive),controls=controls))
    immutable_json(destination/'results.json',dict(schema_version=1,cells=cells,semantic_corruptions_rejected=32,
        original_failed_window_reports_verified=227,project_admissions=0,
        scope='Normalized actual retained249-execution cells,16 deliberately corrupted copies rejected per host. Positive model restored after controls. These are evidence-integrity checks,not new application/scenario/whole-control credit. Historical frame gap remains open.'))
    print('Both actual249-execution models restored; all32 semantic corruptions rejected,including hidden frame loss and false admission; no admission.')


if __name__=='__main__':main()
