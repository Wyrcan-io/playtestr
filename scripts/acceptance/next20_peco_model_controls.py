"""Challenge normalized actual peco cells without granting admission credit."""
import copy
import argparse
import json
import lzma
import uuid

from next20_check import DOC, RAW
from next20_peco_cell_readback import Evidence
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--normal-rebuild',action='store_true');args=parser.parse_args()
    package=DOC/'peco';history=json.loads((package/'all-attempt-evidence.json').read_text())
    require(history['historical_frames_complete'] and len(history['unlaunched_reports'])==3 and len(history['original_failed_report_frames'])>=18,'original failed/refused history incomplete')
    declared={f['id']:f for f in json.loads((package/'fault-declaration.json').read_text())['faults']}
    candidate=json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())
    root=RAW/'peco/audit-controls'/uuid.uuid4().hex;root.mkdir(parents=True)
    cells=[]
    for host in ['windows','linux']:
        e=Evidence(host,'41043810230' if host=='linux' else None,3 if host=='linux' else None)
        target='active/peco/' if host=='windows' and (RAW/'active/peco').is_dir() else 'peco/retained-source/'
        runtime=e.load(target+'runtime.json');complete=e.load('peco/final-execution-summary.json');fault_reader=e
        if args.normal_rebuild:
            fault_reader=Evidence(host,'41713430365' if host=='linux' else None,4 if host=='linux' else None,'next20-peco-linux-rebuild-recovery')
            correction=fault_reader.load('peco/rebuild-recovery-summary-v1.json');faults=fault_reader.load(correction['fault_summary'])
            if faults['normal_restoration_rebuilds']!=3:raise ValueError('normal rebuild model requires actual rebuilt recoveries')
        else:faults=e.load(complete['fault_summary'])
        expected_candidate=next(c for c in candidate['cells'] if c['host']==host)
        def normalize(report_name,eid,phase,spec,reader=None):
            reader=reader or e;row=reader.load(report_name)['results'][0];value=reader.load(spec)
            return dict(attempt=eid,phase=phase,status=row['status'],category=row.get('failure',{}).get('category'),
                invocation=row['invocation_id'],workspace=row['workspace']['id'],confirmed_exited=row['cleanup']['confirmed_exited'],cleaned=row['workspace']['cleaned'],
                target_exit=row['target'].get('exit_code'),runner_sha256=expected_candidate['binary_sha256'],
                expected_actions=[next(iter(s)) for s in value['steps']],expected_states={str(i):s['state'] for i,s in enumerate(value['steps']) if 'state' in s},
                steps=[dict(action=s['action'],status=s['status'],state=s.get('state')) for s in row['steps']],
                timeout_ms=value['timeout_ms'],run_timeout_ms=value['run_timeout_ms'],startup_timeout_ms=value.get('startup_timeout_ms',0))
        model=dict(project='peco',repository='peco/peco',host=host,candidate='v0.4.0-rc.6',archive_sha256=expected_candidate['archive_sha256'],runner_sha256=expected_candidate['binary_sha256'],
            app_sha256=runtime['target_sha256'],capture_sha256=runtime['native_sha256'],runtime_sha256=e.sha(target+'runtime.json'),
            helper_source_revision='4d31e08b3d6da92d94f7eb393b43689fd89bbf25',required_executable_index_sha256=e.sha('peco/go-module-corpus/executables-index.json'),
            historical_frames_complete=True,all_attempt_evidence_sha256=sha256(package/'all-attempt-evidence.json'),first_public_sha256=sha256(package/'first-use.json'),project_admitted=False,
            viewport_declaration_sha256=sha256(package/'viewport-snapshot-declaration-v1.json'),ordinary=[],faults=[])
        if args.normal_rebuild:model['calibration_helper_revision']='ce4012850a43b81fa0968f11cc7f147cd27aa7b2'
        expected_specs={};expected_states={}
        for batch in range(12):
            folder='peco/final-series-native-exit-v1/'+str(batch)+'/'
            summary=e.load(folder+'summary.json')
            for item in summary['observations']:
                planned=e.load(folder+item['case']+'.planned.json');spec=planned['spec']
                started=e.load('events/'+item['attempt']+'-started.json')
                row=normalize(folder+item['case']+'.report.json',item['attempt'],started['phase'],spec)
                row.update(batch=batch,case=item['case'],spec_sha256=e.sha(spec));model['ordinary'].append(row)
                expected_specs[(batch,item['case'])]=e.sha(spec);expected_states[(batch,item['case'])]=copy.deepcopy(row['expected_states'])
        primary='peco/'+('host-contracts-rebuild-v1' if args.normal_rebuild and host=='windows' else 'host-contracts')+'/'+json.loads((package/'fault-declaration.json').read_text())['primary_spec']
        expected_mutants={}
        for fault in faults['faults']:
            outcomes=[normalize(p['report'],p['attempt'],p['phase'],primary,fault_reader) for p in fault['outcomes']]
            model['faults'].append(dict(id=fault['id'],original_sha256=fault['original_sha256'],mutated_sha256=fault['mutated_sha256'],restored_sha256=fault['restored_sha256'],restored_exact=fault['restored_exact'],
                original_binary_sha256=fault['original_binary_sha256'],mutated_binary_sha256=fault['mutated_binary_sha256'],restored_binary_sha256=fault['restored_binary_sha256'],outcomes=outcomes))
            if args.normal_rebuild:
                model['faults'][-1].update(normal_rebuild_recovery_executed=fault['normal_rebuild_recovery_executed'],normal_rebuild_receipt_sha256=fault['normal_rebuild_receipt_sha256'])
            expected_mutants[fault['id']]=fault['mutated_binary_sha256']
        baseline={k:copy.deepcopy(v) for k,v in model.items() if k not in {'ordinary','faults'}}
        rebuild_receipts={f['id']:f.get('normal_rebuild_receipt_sha256') for f in model['faults']}
        canonical={c['id'] for c in json.loads((package/'scenarios.json').read_text())['cases']}
        def validate(value):
            require(all(value[k]==v for k,v in baseline.items()),'wrong project/candidate/runtime/helper/history/payload/viewport identity or false admission')
            require(len(value['ordinary'])==240 and len(value['faults'])==3 and {f['id'] for f in value['faults']}==set(declared),'partial actual matrix or calibration')
            invocations=set();attempts=set()
            def outcome(row,status):
                require(row['status']==status and row['confirmed_exited'] and row['cleaned'],'false outcome or unconfirmed cleanup')
                require(row['invocation']==row['workspace'] and row['invocation'] not in invocations and row['attempt'] not in attempts,'cross/duplicate invocation or attempt')
                invocations.add(row['invocation']);attempts.add(row['attempt'])
                require([s['action'] for s in row['steps']]==row['expected_actions'],'missing actual action')
                if status=='passed':require(all(s['status']=='passed' for s in row['steps']),'nonpositive passing steps')
                else:require(sum(s['status']=='failed' for s in row['steps'])==1,'missing genuine failing step')
                for i,step in enumerate(row['steps']):
                    if step['state']:
                        require(step['state']['invocation_id']==row['invocation'] and step['state']['workspace_id']==row['workspace'],'cross-invocation saved state')
                        expected=row['expected_states'][str(i)]
                        require(step['state']['path']==expected['path'] and step['state']['kind']==expected['kind'],'wrong actual saved-state path/kind')
                        if step['status']=='passed':require(step['state']['outcome']=='matched','false matched saved state')
            for batch in range(12):
                rows=[r for r in value['ordinary'] if r['batch']==batch]
                require(len(rows)==20 and {r['case'] for r in rows}==canonical,'missing/duplicate actual case')
                for row in rows:
                    require(row['phase']=='final-archive' and row['runner_sha256']==value['runner_sha256'] and row['spec_sha256']==expected_specs[(batch,row['case'])] and row['expected_states']==expected_states[(batch,row['case'])],'wrong phase/runner/contract/state oracle')
                    if batch==11 and row['case']=='E10':require(row['startup_timeout_ms']==0 and row['timeout_ms']==row['run_timeout_ms']==2000 and row['target_exit']==1,'quiet exact completion boundary weakened')
                    outcome(row,'passed')
            for fault in value['faults']:
                rule=declared[fault['id']]
                if args.normal_rebuild:require(fault['normal_rebuild_recovery_executed'] and fault['normal_rebuild_receipt_sha256']==rebuild_receipts[fault['id']],'copied image posing as normal rebuilt source recovery')
                require(fault['restored_exact'] and fault['original_sha256']==fault['restored_sha256']==rule['original_source_sha256'] and fault['mutated_sha256']==rule['mutated_source_sha256'],'source mutation/restoration differs')
                require(fault['original_binary_sha256']==fault['restored_binary_sha256']==value['app_sha256'] and fault['mutated_binary_sha256']==expected_mutants[fault['id']] and fault['mutated_binary_sha256']!=value['app_sha256'],'fake compiled mutation or executable restoration')
                require(len(fault['outcomes'])==3 and {r['phase'] for r in fault['outcomes']}=={'baseline','mutated','restored'},'partial actual fault triple')
                for row in fault['outcomes']:
                    mutated=row['phase']=='mutated';outcome(row,'failed' if mutated else 'passed')
                    if mutated:
                        require(row['category']==rule['category'],'wrong actual mutation rejection')
                        if fault['id']=='F03':
                            first=next(i for i,s in enumerate(row['steps']) if s['status']=='failed')
                            require(row['steps'][first]['action']=='state' and row['steps'][first]['state']['path']=='selected.txt' and all(s['status']=='passed' for s in row['steps'][:first]) and {'expect','exit','snapshot'}<=set(s['action'] for s in row['steps'][:first]),'earlier failure posing as saved-output corruption')
            require(len(invocations)==len(attempts)==249,'missing actual distinct executions')
            return dict(ordinary=240,calibrations=9,real_faults=3,project_admissions=0)
        counts=validate(model);state=next(i for i,s in enumerate(model['ordinary'][0]['steps']) if s['state'])
        quiet=next(i for i,r in enumerate(model['ordinary']) if r['batch']==11 and r['case']=='E10')
        patches=[('missing-case',['ordinary'],model['ordinary'][:-1]),('wrong-runtime',['runtime_sha256'],'0'*64),('duplicate-project',['project'],'cargo-generate'),
            ('changed-contract',['ordinary',0,'spec_sha256'],'0'*64),('missing-restoration',['faults',0,'restored_exact'],False),
            ('cross-state',['ordinary',0,'steps',state,'state','invocation_id'],'other'),('wrong-phase',['ordinary',0,'phase'],'development'),
            ('missing-first-public',['first_public_sha256'],'0'*64),('unconfirmed-descendants',['ordinary',0,'confirmed_exited'],False),
            ('missing-payload',['required_executable_index_sha256'],'0'*64),('stale-helper',['helper_source_revision'],'0'*40),
            ('mixed-runner',['ordinary',0,'runner_sha256'],'0'*64),('hidden-frame-loss',['historical_frames_complete'],False),('false-admission',['project_admitted'],True),
            ('false-green-mutation',['faults',2,'outcomes',1,'status'],'passed'),('earlier-failure-as-state',['faults',2,'outcomes',1,'steps',0,'status'],'failed'),
            ('wrong-app-pair',['app_sha256'],'0'*64),('fake-mutant-executable',['faults',0,'mutated_binary_sha256'],runtime['target_sha256']),
            ('weakened-quiet-budget',['ordinary',quiet,'run_timeout_ms'],10000),('wrong-saved-path',['ordinary',0,'steps',state,'state','path'],'sentinel.txt')]
        if args.normal_rebuild:patches.append(('copied-image-as-rebuild',['faults',0,'normal_rebuild_recovery_executed'],False))
        controls=[]
        for label,path,replacement in patches:
            changed=copy.deepcopy(model);parent=changed
            for key in path[:-1]:parent=parent[key]
            parent[path[-1]]=replacement
            try:validate(changed)
            except ValueError as error:controls.append(dict(control=label,rejected=True,reason=str(error)))
            else:raise ValueError('corrupted actual model accepted: '+label)
        validate(model);encoded=json.dumps(model,sort_keys=True,separators=(',',':')).encode()
        require(len(encoded)<=8*1024**2,'actual model byte bound');archive=root/(host+'-actual-model.json.xz');archive.write_bytes(lzma.compress(encoded,preset=6))
        require(json.loads(lzma.decompress(archive.read_bytes(),memlimit=64*1024**2))==model,'actual model exact restoration differs')
        cells.append(dict(host=host,counts=counts,model=archive.relative_to(RAW).as_posix(),model_sha256=sha256(archive),controls=controls))
    immutable_json(root/'results.json',dict(schema_version=1,cells=cells,semantic_corruptions_rejected=42 if args.normal_rebuild else 40,normal_rebuild_calibration_model=args.normal_rebuild,all_attempt_evidence_sha256=sha256(package/'all-attempt-evidence.json'),project_admissions=0,
        scope='Two normalized actual249-execution cells,20 corrupted copies rejected per host; positive models restored. Evidence-integrity controls only,no new project/scenario/whole-control credit.'))
    print('Both actual249-execution models restored;all'+str(42 if args.normal_rebuild else 40)+' semantic corruptions rejected; no admission.')


if __name__=='__main__':main()
