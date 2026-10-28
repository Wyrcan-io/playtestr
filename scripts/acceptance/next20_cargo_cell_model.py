"""Semantic challenges to independently read-back complete native Cargo cells."""
import copy
import hashlib
import json
import lzma
import uuid

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def normalize(report,phase):
    row=report['results'][0]
    return dict(phase=phase,status=row['status'],category=row.get('failure',{}).get('category'),
        invocation=row['invocation_id'],workspace=row['workspace']['id'],cleaned=row['workspace']['cleaned'],
        confirmed_exited=row['cleanup']['confirmed_exited'],steps=[dict(action=s['action'],status=s['status'],state=s.get('state')) for s in row['steps']])


def validate(model):
    package=DOC/'cargo-generate';host=model['host']
    require(model['project']=='cargo-generate' and host in {'linux','windows'},'wrong native project/host')
    candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']==host)
    require(model['archive_sha256']==candidate['archive_sha256'] and model['runner_sha256']==candidate['binary_sha256'],'wrong exact current candidate')
    require(model['first_development_disposition_sha256']==sha256(package/'development-outcome-disposition.json'),'missing original first-failure disposition')
    for name,digest in model['native_failure_dispositions'].items():require(sha256(package/name)==digest,'changed original native failure disposition')
    require(set(model['native_failure_dispositions'])=={'native-linux-first-final-rejection.json','native-linux-second-final-rejection.json'},'missing rejected-window history')
    require(all(model['cleanup'][name] for name in ['removed','source_restored','process_confirmed']),'source/process cleanup incomplete')
    canonical={c['id'] for c in json.loads((package/'scenarios.json').read_text())['cases']}
    require(len(model['ordinary'])==240 and len(canonical)==20,'partial ordinary series')
    for batch in range(12):
        cases=[r['case'] for r in model['ordinary'] if r['batch']==batch]
        require(len(cases)==20 and set(cases)==canonical,'missing/duplicated batch case')
    seen=set();attempts=set()
    def outcome(row,status):
        require(row['status']==status and row['cleaned'] and row['confirmed_exited'],'wrong outcome or descendant/workspace cleanup')
        require(row['invocation']==row['workspace'] and row['invocation'] not in seen,'cross/duplicate invocation')
        require(row['attempt'] not in attempts,'duplicate execution attempt')
        seen.add(row['invocation']);attempts.add(row['attempt'])
        actions=[s['action'] for s in row['steps']]
        require(actions==(row['expected_actions'] if status=='passed' else row['expected_actions'][:len(actions)]),'changed/omitted action sequence')
        if status=='failed':require(any(s['status']=='failed' for s in row['steps']),'missing actual failing step')
        if status=='passed':require(all(s['status']=='passed' for s in row['steps']),'missing positive step evidence')
        for step in row['steps']:
            if step['state']:require(step['state']['invocation_id']==row['invocation'] and step['state']['workspace_id']==row['workspace'],'cross-invocation state')
    for row in model['ordinary']:
        require(row['phase']=='final-archive' and row['archive_sha256']==model['archive_sha256'] and row['runner_sha256']==model['runner_sha256'],'wrong phase/mixed runner archive')
        outcome(row,'passed')
    faults=json.loads((package/'fault-declaration.json').read_text())['faults'];declared={f['id']:f for f in faults}
    require(len(model['faults'])==3 and {f['id'] for f in model['faults']}==set(declared),'missing real source fault')
    for fault in model['faults']:
        require(fault['restored_exact'] and len(fault['outcomes'])==3 and {r['phase'] for r in fault['outcomes']}=={'baseline','mutated','restored'},'missing source restoration phase')
        for row in fault['outcomes']:
            outcome(row,'failed' if row['phase']=='mutated' else 'passed')
            if row['phase']=='mutated':
                require(row['category']==declared[fault['id']]['category'],'wrong actual source-fault rejection')
                if fault['id']=='F03':
                    first=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
                    require(all(s['status']=='passed' for s in row['steps'][:first]),'saved corruption failed before successful terminal/exit')
    return dict(ordinary=240,calibrations=9,cases=20,real_source_faults=3)


def build(host,records,prefix,readback):
    def data(name):
        path=RAW/(prefix+name)
        return path.read_bytes() if path.is_file() else records[prefix+name]
    def load(name):return json.loads(data(name).decode('utf-8-sig'))
    package=DOC/'cargo-generate';candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']==host)
    removed=load('cargo-generate/retained-source/removed.json');cleanup=load('cargo-generate/retained-source/cleanup-inventory.json');process=load('cargo-generate/process-proof.json')
    require(removed['cleanup_inventory_sha256']==hashlib.sha256(data('cargo-generate/retained-source/cleanup-inventory.json')).hexdigest(),'unbound source cleanup inventory')
    require(cleanup['process_proof_sha256']==hashlib.sha256(data('cargo-generate/process-proof.json')).hexdigest(),'unbound native process proof')
    provenance=json.loads((package/'source-provenance.json').read_text())
    restored={n.removeprefix('src/'):r['sha256'] for n,r in cleanup['files'].items() if n.startswith('src/')}
    require(restored==provenance['files'],'actual source bytes not restored exactly')
    model=dict(schema_version=1,project='cargo-generate',host=host,archive_sha256=candidate['archive_sha256'],runner_sha256=candidate['binary_sha256'],
        independent_readback=readback,first_development_disposition_sha256=sha256(package/'development-outcome-disposition.json'),
        native_failure_dispositions={n:sha256(package/n) for n in ['native-linux-first-final-rejection.json','native-linux-second-final-rejection.json']},
        cleanup=dict(removed=removed['removed'],source_restored=removed['source_restored_exact'] and cleanup['source_restored_exact'],
            process_confirmed=process['confirmed_no_matching_live_processes'] and not process['matching_live_processes']),ordinary=[],faults=[])
    profile=load('cargo-generate/host-contracts/scenarios.json');cases={c['id']:c for c in profile['cases']}
    for batch in range(12):
        folder='cargo-generate/final-series-native-exit-v1/'+str(batch)+'/'
        summary=load(folder+'summary.json')
        for item in summary['observations']:
            row=normalize(load(folder+item['case']+'.report.json'),'final-archive')
            spec=load(folder+('relocated caf\u00e9 \u96ea/' if batch==5 else 'contracts/')+cases[item['case']]['spec'])
            row.update(batch=batch,case=item['case'],attempt=item['attempt'],archive_sha256=summary['archive_sha256'],runner_sha256=summary['runner_sha256'],expected_actions=[next(iter(s)) for s in spec['steps']])
            model['ordinary'].append(row)
    folder='cargo-generate/source-fault-final-native-exit-v1/v1/'
    faults=json.loads((package/'fault-declaration.json').read_text())['faults']
    for declared,item in zip(faults,load(folder+'summary.json')['observations']):
        outcomes=[];spec=load('cargo-generate/host-contracts/'+declared['spec'])
        for phase in ['baseline','mutated','restored']:
            row=normalize(load(folder+item['fault']+'-'+phase+'.report.json'),phase)
            row.update(attempt=item[phase]['attempt'],expected_actions=[next(iter(s)) for s in spec['steps']]);outcomes.append(row)
        model['faults'].append(dict(id=item['fault'],restored_exact=model['cleanup']['source_restored'],outcomes=outcomes))
    validate(model);return model


def challenge(model):
    validate(model);state=next(i for i,s in enumerate(model['ordinary'][0]['steps']) if s['state'])
    patches=[('missing-case',['ordinary'],model['ordinary'][:-1]),('wrong-phase',['ordinary',0,'phase'],'development'),
        ('duplicate-batch-case',['ordinary',1,'case'],model['ordinary'][0]['case']),('duplicate-invocation',['ordinary',1,'invocation'],model['ordinary'][0]['invocation']),
        ('cross-invocation-state',['ordinary',0,'steps',state,'state','invocation_id'],'another-execution'),('missing-restoration',['faults',0,'restored_exact'],False),
        ('earlier-failure-as-saved-corruption',['faults',2,'outcomes',1,'steps',0,'status'],'failed'),('false-green-mutation',['faults',2,'outcomes',1,'status'],'passed'),
        ('missing-first-failure-disposition',['first_development_disposition_sha256'],'0'*64),('unconfirmed-descendants',['ordinary',0,'confirmed_exited'],False),
        ('mixed-archive',['ordinary',0,'archive_sha256'],'0'*64),('mixed-runner',['ordinary',0,'runner_sha256'],'0'*64)]
    results=[]
    for name,path,value in patches:
        altered=copy.deepcopy(model);parent=altered
        for key in path[:-1]:parent=parent[key]
        parent[path[-1]]=value
        try:validate(altered)
        except ValueError as error:results.append(dict(control=name,rejected=True,reason=str(error),path=path,
            mutation=dict(operation='truncate',length=len(value)) if name=='missing-case' else dict(operation='replace',value=value),
            altered_sha256=hashlib.sha256(json.dumps(altered,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
        else:raise ValueError('corrupted actual cell model accepted: '+name)
    validate(model);return results


def main():
    from next20_local_records import read_packet as local_packet
    from next20_native_packet_reader import read_packet
    local_index,local=local_packet('cargo-generate');native_index,native=read_packet('cargo-generate',13)
    destination=RAW/'cargo-generate/audit-controls'/uuid.uuid4().hex;destination.mkdir(parents=True)
    observations=[]
    for host,records,prefix in [('windows',local,''),('linux',native,'native/40758514842/next20-cargo-linux-final/')]:
        matches=[]
        for path in (RAW/'cargo-generate').glob('final-cell-readback-'+host+'-*.json'):
            row=json.loads(path.read_text())
            if row['ordinary_readbacks']==240 and row['calibration_readbacks']==9 and row['revision']==('bba80ce82ca0cb4746ff7dd80ffd43346a7b7171' if host=='windows' else '2808b670751e5d1d59bffd3ac2793412667ae6b0'):matches.append(path)
        require(bool(matches),'complete actual independent cell readback missing')
        selected=sorted(matches)[0];model=build(host,records,prefix,dict(path=selected.relative_to(RAW).as_posix(),sha256=sha256(selected)))
        controls=challenge(model);encoded=json.dumps(model,sort_keys=True,separators=(',',':')).encode();compressed=lzma.compress(encoded,preset=6)
        require(len(encoded)<=8*1024**2 and len(compressed)<=1024**2,'actual cell model evidence bound')
        path=destination/(host+'-actual-model.json.xz');path.write_bytes(compressed)
        require(json.loads(lzma.decompress(path.read_bytes(),memlimit=64*1024**2))==model,'actual cell model full restoration differs')
        observations.append(dict(host=host,counts=validate(model),model=path.relative_to(RAW).as_posix(),model_sha256=sha256(path),decoded_model_sha256=hashlib.sha256(encoded).hexdigest(),controls=controls))
    immutable_json(destination/'results.json',dict(schema_version=1,cells=observations,semantic_corruptions_rejected=24,
        scope='Two actual independently read-back complete cell models,12 reconstructible challenges each. Source/executable retention and project admission remain separate gates; no global whole-control or scenario credit.'))
    print('Actual complete Windows/Linux cell models restored; all24 semantic corruptions rejected; no project admission yet')


if __name__=='__main__':main()
