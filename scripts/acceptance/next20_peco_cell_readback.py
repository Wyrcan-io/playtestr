"""Independently verify every actual peco final execution and compiled fault."""
import argparse
import copy
import hashlib
import io
import json
import ntpath
import posixpath
from pathlib import Path
import tarfile

from next20_check import DOC, RAW, ROOT, NAME
from next20_native_packet_reader import read_packet
from next20_peco_development_readback import audit as native_inputs, git_inputs
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def hashed(body):return hashlib.sha256(body).hexdigest()


class Evidence:
    def __init__(self,host,run=None,generation=None,artifact='next20-peco-linux-final'):
        self.host=host;self.scope='artifacts/'+NAME+'/';self.cache={}
        require(artifact in {'next20-peco-linux-final','next20-peco-linux-rebuild-recovery'},'undeclared native evidence artifact')
        self.prefix='native/'+run+'/'+artifact+'/' if host=='linux' else ''
        self.records=read_packet('peco',generation)[1] if host=='linux' else None

    def logical(self,name):
        name=str(name).replace('\\','/').removeprefix(self.scope)
        require(name and not name.startswith('/') and ':' not in name and all(p not in {'','.','..'} for p in name.split('/')),'unsafe logical evidence path')
        return name

    def data(self,name):
        name=self.logical(name)
        if self.records is not None:
            require(self.prefix+name in self.records,'required actual native body missing: '+name)
            return self.records[self.prefix+name]
        path=RAW/name
        if path.is_file():return path.read_bytes()
        for retained_prefix in ['peco/retained-source/','peco/retained-source-rebuild-v1/']:
            if not name.startswith(retained_prefix):continue
            key=name.removeprefix(retained_prefix);root=RAW/retained_prefix
            if (root/'review-inputs-index.json').is_file():
                from next20_review_input_packet import read
                cache_key='metadata:'+retained_prefix
                if cache_key not in self.cache:self.cache[cache_key]=read(root)
                if key in self.cache[cache_key]:return self.cache[cache_key][key]
            if (root/'canonical-native-references.json').is_file() and key in json.loads((root/'canonical-native-references.json').read_text())['files']:
                from next20_local_native_references import canonical,resolve
                manifest=json.loads((root/'canonical-native-references.json').read_text())
                _,base=canonical('peco',manifest['required_canonical_packet']['generation'],manifest['required_canonical_packet'])
                return resolve(key,manifest,base)
        for corpus_prefix in ['peco/go-module-corpus/','peco/go-module-corpus-rebuild-v1/']:
            if not name.startswith(corpus_prefix+'archives/') or not name.endswith('.zip'):continue
            from next20_local_native_references import canonical,resolve
            manifest=self.load(corpus_prefix+'canonical-native-references.json')
            _,base=canonical('peco',manifest['required_canonical_packet']['generation'],manifest['required_canonical_packet'])
            return resolve(name.removeprefix(corpus_prefix),manifest,base)
        from next20_local_records import read_packet as local
        for packet in ['retained-complete-final-v1','retained-local-v1']:
            if not (RAW/'peco'/packet/'index.json').is_file():continue
            if packet not in self.cache:self.cache[packet]=local('peco',packet=packet)[1]
            if name in self.cache[packet]:return self.cache[packet][name]
        raise ValueError('required actual Windows body missing: '+name)

    def load(self,name):return json.loads(self.data(name).decode('utf-8-sig'))
    def sha(self,name):return hashed(self.data(name))


def audit(host,revision,run=None,generation=None):
    require(host in {'windows','linux'} and (host=='windows' or run and generation),'explicit actual native scope required')
    package=DOC/'peco';scope='artifacts/'+NAME+'/';e=Evidence(host,run,generation)
    declaration_path=package/'final-series-declaration-native-exit-v1.json';declaration=json.loads(declaration_path.read_text())
    if host=='linux':
        inputs=native_inputs(generation,run,revision,True,'next20-peco-linux-final',269)
        require(inputs['source_runtime_removed'],'native final source/runtime not removed')
    target='active/peco/' if host=='windows' and (RAW/'active/peco').is_dir() else 'peco/retained-source/'
    runtime=e.load(target+'runtime.json');build=e.load(target+'build.json');owner=e.load(target+'task-owned.json')
    catalog=e.load(target+'dependency-source-catalog.json');primary=json.loads((package/'source-provenance.json').read_text())['files']
    source_bodies={};links={}
    with tarfile.open(fileobj=io.BytesIO(e.data(target+'source.tar.gz')),mode='r:gz') as stream:
        for member in stream:
            if member.isdir():continue
            name=member.name.split('/',1)[1]
            require(name not in source_bodies and name not in links and all(p not in {'','.','..'} for p in name.split('/')),'unsafe original primary source path')
            if member.issym():links[name]=member.linkname;continue
            require(member.isfile() and name in primary and member.size<=8*1024**2,'unreviewed actual primary source member')
            body=stream.extractfile(member).read(member.size+1)
            require(len(body)==member.size and hashed(body)==primary[name],'actual primary source archive bytes differ')
            source_bodies[name]=body
    require(set(source_bodies)==set(primary) and links==json.loads((package/'source-link-policy.json').read_text())['omitted_documentation_links'],'actual primary source/link coverage differs')
    require(owner['pin']==json.loads((package/'source-provenance.json').read_text())['pin'] and owner['slug']=='peco' and owner['campaign']==NAME,'foreign actual source ownership')
    require(build['source_catalog_sha256']==e.sha(target+'dependency-source-catalog.json') and build['source_review_sha256']==sha256(package/'dependency-source-review-declaration.json'),'actual source/build review binding differs')
    if host=='windows':
        # All archive/license/module bodies were independently verified in the
        # native development readback. Bind actual Windows installed sources to
        # that same complete code catalog, then check Windows-specific inputs.
        _,base=read_packet('peco',2);p='native/41041642421/next20-peco-linux-development/peco/retained-source/'
        reviewed=json.loads(base[p+'dependency-source-catalog.json'])
        require(catalog['files']==reviewed['files'],'Windows module/primary source bytes differ from reviewed archive bodies')
        actual_inputs=e.load(target+'native-package-inputs.json')
        require(actual_inputs['files']==catalog['actual_native_compile_inputs'] and all(catalog['files'].get(n)==h for n,h in actual_inputs['files'].items()),'Windows native compile inputs differ')
        removed_inventory=e.load(target+'cleanup-inventory.json') if not target.startswith('active/') else None
        for name,expected in catalog['files'].items():
            if target.startswith('active/'):
                require(sha256(RAW/'active/peco'/name)==expected,'actual restored Windows source/module bytes differ')
            else:require(removed_inventory['files'][name]['sha256']==expected,'removed actual source/module differs')
    binary_index=e.load('peco/go-module-corpus/executables-index.json');archive=e.data('peco/go-module-corpus/executables.tar.xz')
    require(hashed(archive)==binary_index['archive_sha256'],'actual retained executable archive differs')
    physical={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:xz') as stream:
        for member in stream:
            require(member.isfile() and member.name in binary_index['files'] and member.name not in physical and member.size<=16*1024**2,'unsafe actual executable payload')
            physical[member.name]=stream.extractfile(member).read(member.size+1)
    binaries={}
    for name,row in binary_index['files'].items():
        body=physical[row.get('member',name)]
        require(len(body)==row['bytes'] and hashed(body)==row['sha256'],'actual executable corpus body differs')
        binaries[name]=row['sha256']
    require({n.removeprefix('bin/'):h for n,h in binaries.items() if n.startswith('bin/')}==build['compiled_files'],'actual baseline app/capture binary differs')
    require(runtime['native_sha256']==build['binary_sha256'] and runtime['target_sha256']==build['actual_target_sha256'],'actual app/capture runtime differs')
    complete=e.load('peco/final-execution-summary.json');plan=e.load('peco/final-execution-plan.json')
    require(complete['ordinary_executions']==240 and complete['calibrations']==9 and complete['host']==host and complete['plan_sha256']==e.sha('peco/final-execution-plan.json') and complete['declaration_sha256']==sha256(declaration_path),'partial/mixed final cell')
    require(plan['runtime_sha256']==e.sha(target+'runtime.json') and plan['build_sha256']==e.sha(target+'build.json'),'final execution source/runtime changed')
    frozen=e.load('peco/host-contracts/development-test-freeze.json');cases=e.load('peco/host-contracts/scenarios.json')['cases'];by_id={c['id']:c for c in cases}
    require(len(cases)==len(by_id)==20 and frozen['canonical_freeze_sha256']==sha256(package/'development-test-freeze.json'),'missing actual frozen cases')
    for name,expected in frozen['inputs'].items():require(e.sha('peco/host-contracts/'+name)==expected,'actual host frozen input changed')
    candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']==host)
    helpers=git_inputs(revision);helper_accept=dict(helpers)
    if host=='windows':
        from next20_review_input_packet import read
        bodies=read(RAW/'peco/execution-helper-source-v1')
        for name,expected in helpers.items():
            require(name in bodies,'missing exact actual Windows helper source')
            body=bodies[name];normalized=body.replace(b'\r\n',b'\n')
            require(expected in {hashed(body),hashed(normalized),hashed(normalized.replace(b'\n',b'\r\n'))},'Windows actual helper differs beyond declared line endings')
            helper_accept[name]=hashed(body)
    attempts=set();invocations=set();ordinary=[];calibrations=[]
    def manifest(reference):
        require(e.sha(reference['manifest'])==reference['sha256'],'changed actual prelaunch identity')
        return e.load(reference['manifest'])
    def command(eid,spec,mutant=None,runtime_catalog=None):
        require(eid not in attempts,'duplicate actual attempt');attempts.add(eid)
        events={k:e.load('events/'+eid+'-'+k+'.json') for k in ['started','identified','launched','finished']}
        require(all(v['id']==eid and v['campaign']==NAME and v['phase']=='final-archive' and v['project']=='peco' for v in events.values()),'wrong actual execution phase/project')
        require(events['started']['ci_run_id']==(run if host=='linux' else None),'wrong actual provider execution')
        end=events['finished'];require(end['category']=='passed' and end['exit_code']==(1 if mutant else 0) and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'] and events['launched']['pid']>0,'incomplete actual harness execution/cleanup')
        require(e.sha('peco/'+eid+'/console.log')==end['console_sha256'],'changed actual target-command console')
        combined=manifest(events['identified']['identity'])
        if mutant:
            base=combined;fault=combined['native_source_fault'];receipt_name,receipt=mutant
            require(fault['build_receipt_sha256']==e.sha(receipt_name) and fault['actual_executable_sha256']==receipt['binary_sha256'] and fault['source_inputs']==receipt['source_inputs'],'actual compiled mutation launch differs')
        else:
            base=manifest(combined['base']);actual=manifest(combined['target_catalog'])['files']
            require({n.removeprefix(scope+'active/peco/src/'):h for n,h in actual.items() if n.startswith(scope+'active/peco/src/')}==primary and actual.get(scope+'active/peco/runtime.json')==e.sha(target+'runtime.json'),'actual pristine prelaunch source/runtime differs')
            if runtime_catalog:require(actual.get(scope+'active/peco/launch-runtime-catalog.json')==e.sha(runtime_catalog),'actual launch runtime schedule differs')
        files=base['files']
        require(all(files.get(n)==h for n,h in helper_accept.items()),'actual execution helper source differs from recorded revision')
        require(files.get(scope+e.logical(spec))==e.sha(spec) and files.get(scope+'candidate-native-exit-v1/'+host+'/playtestr'+('.exe' if host=='windows' else ''))==candidate['binary_sha256'],'actual spec/private candidate differs')
        return events
    def outcome(report_name,spec,status,category=None):
        report=e.load(report_name);require(report['report_version']==3 and report['runner_version']=='v0.4.0-rc.6' and report['os']==host and report['arch']=='amd64' and len(report['results'])==1,'actual report schema/candidate/platform differs')
        row=report['results'][0];steps=e.load(spec)['steps']
        require(row['status']==status and row.get('failure',{}).get('category')==category and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'nonqualifying actual outcome/cleanup')
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'duplicate/cross-invocation result');invocations.add(row['invocation_id'])
        require([s['action'] for s in row['steps']]==[next(iter(s)) for s in steps],'omitted/changed actual action sequence')
        if status=='passed':
            require(all(s['status']=='passed' for s in row['steps']),'false positive step outcome')
            exits=[s['exit'] for s in steps if 'exit' in s]
            require(len(exits)==1 and row['target']['exited'] and row['target']['exit_code']==exits[0],'actual exact declared exit differs')
        else:
            failed=[i for i,s in enumerate(row['steps']) if s['status']=='failed'];require(len(failed)==1,'mutation lacks one actual failing step')
            first=failed[0];require(all(s['status']=='passed' for s in row['steps'][:first]) and all(s['status']=='not_run' for s in row['steps'][first+1:]),'mutation steps continued or failed before declared boundary')
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-invocation saved state')
        return row
    for batch in range(12):
        root='peco/final-series-native-exit-v1/'+str(batch)+'/'
        summary=e.load(root+'summary.json');prepared=e.load(root+'prepared.json');selected=e.load(root+'runtime-catalog.json')
        require(complete['batches'][root+'summary.json']==e.sha(root+'summary.json') and summary['ordinary_executions']==20 and len(summary['observations'])==20 and {r['case'] for r in summary['observations']}==set(by_id),'partial actual final batch')
        require(summary['runner_sha256']==candidate['binary_sha256'] and summary['archive_sha256']==candidate['archive_sha256'] and prepared['declaration_sha256']==sha256(declaration_path),'mixed final candidate/declaration')
        expected_runtime='app-pair-native-exit-v1-'+str(batch//2) if batch<4 else 'bin'
        require(selected['runtime_root']==scope+'active/peco/'+expected_runtime and selected['files']==build['compiled_files'] and prepared['actual_runtime_catalog_sha256']==e.sha(root+'runtime-catalog.json'),'actual cold/warm/base schedule differs')
        for name,expected in selected['files'].items():require(binaries.get(expected_runtime+'/'+name)==expected,'actual selected runtime executable copy bytes missing/different')
        for item in summary['observations']:
            cid=item['case'];case=by_id[cid];planned=e.load(root+cid+'.planned.json');spec=e.logical(planned['spec']);value=e.load(spec)
            expected=copy.deepcopy(e.load('peco/host-contracts/'+case['spec']))
            expected['command'][0]=posixpath.relpath(selected['executable'],posixpath.dirname(scope+spec))
            if batch==4:expected.update(width=expected['width']+10,height=expected['height']+2)
            if batch==7:
                split=[]
                for step in expected['steps']:
                    text=step.get('text')
                    if set(step)=={'text'} and len(text)>1 and all(ord(c)>=32 and ord(c)!=127 for c in text):split.extend({'text':text[i:i+3]} for i in range(0,len(text),3))
                    else:split.append(step)
                expected['steps']=split
            if batch==10 and cid=='N01':expected['height']=12
            if batch==11:
                if case.get('startup_evidence')=='exact-first-exit':require(expected['steps'][0]=={'exit':1} and expected['run_timeout_ms']==expected['timeout_ms']==2000 and expected['startup_timeout_ms']==0,'quiet startup boundary weakened')
                else:expected['startup_timeout_ms']=2000
            require(value==expected and e.sha(spec)==planned['spec_sha256']==item['spec_sha256'],'actual variation changed reviewed actions/oracles')
            for name,hashed_input in frozen['inputs'].items():
                if not name.startswith(('fixture/','fixtures/','snapshots/')):continue
                override=declaration.get('batch_snapshot_profiles',{}).get(str(batch),{}).get(name)
                if override:
                    require(sha256(package/override['reviewed_input'])==override['reviewed_sha256'] and override['original_sha256']==hashed_input,'undeclared changed viewport snapshot')
                    hashed_input=override['reviewed_sha256']
                require(e.sha(posixpath.dirname(spec)+'/'+name)==hashed_input,'actual repeated fixture/snapshot differs')
            require(e.sha(root+cid+'.report.json')==item['report_sha256'],'changed actual report reference')
            row=outcome(root+cid+'.report.json',spec,'passed');events=command(item['attempt'],spec,runtime_catalog=root+'runtime-catalog.json')
            require(events['started']['variation']==('owned 2-second 8-MiB SHA256 CPU worker' if batch in {8,9} else 'ordinary'),'missing declared actual load')
            ordinary.append(dict(batch=batch,case=cid,attempt=item['attempt'],invocation=row['invocation_id'],report_sha256=item['report_sha256'],spec_sha256=item['spec_sha256']))
    faults=e.load(complete['fault_summary']);require(e.sha(complete['fault_summary'])==complete['fault_summary_sha256'] and faults['phase']=='final-archive' and len(faults['faults'])==3,'partial actual calibration')
    declared={f['id']:f for f in json.loads((package/'fault-declaration.json').read_text())['faults']}
    require({f['id'] for f in faults['faults']}==set(declared),'missing real declared source fault')
    for fault in faults['faults']:
        rule=declared[fault['id']];original=source_bodies[rule['path']]
        require(original.count(rule['before'].encode())==1 and hashed(original.replace(rule['before'].encode(),rule['after'].encode()))==rule['mutated_source_sha256'],'actual mutation does not match unique reviewed source edit')
        require(fault['original_sha256']==primary[rule['path']]==fault['restored_sha256'] and fault['mutated_sha256']==rule['mutated_source_sha256'] and fault['restored_exact'],'actual source fault/restoration differs')
        receipt_name=fault['compiled_receipt'];receipt=e.load(receipt_name)
        expected_sources={scope+'active/peco/src/'+n:h for n,h in primary.items()}
        expected_sources[scope+'active/peco/src/'+rule['path']]=rule['mutated_source_sha256']
        expected_sources.update({scope+'active/peco/'+n:h for n,h in catalog['actual_native_compile_inputs'].items()})
        expected_sources[scope+'active/peco/src/'+rule['path']]=rule['mutated_source_sha256']
        capture_relative=build['binary_relative_path'];expected_sources[scope+'active/peco/'+capture_relative]=build['binary_sha256']
        require(receipt['source_inputs']==expected_sources and e.sha(receipt_name)==fault['compiled_receipt_sha256'] and receipt['pristine_build_sha256']==e.sha(target+'build.json'),'actual mutant source/compile binding differs')
        require(receipt['compiler_sha256']==build['compiler_sha256'] and receipt['compiler_tools']==build['compiler_tools'] and receipt['binary_sha256']==fault['mutated_binary_sha256'] and receipt['binary_sha256']!=build['actual_target_sha256'],'actual compiled mutation identity differs')
        variant=e.logical(receipt['binary']).removeprefix('active/peco/')
        require(binaries.get(variant)==receipt['binary_sha256'] and fault['original_binary_sha256']==fault['restored_binary_sha256']==build['actual_target_sha256'],'retained real mutant/restored executable differs')
        require(len(fault['outcomes'])==3 and {r['phase'] for r in fault['outcomes']}=={'baseline','mutated','restored'},'partial source-fault triple')
        for observed in fault['outcomes']:
            mutated=observed['phase']=='mutated';spec='peco/host-contracts/'+json.loads((package/'fault-declaration.json').read_text())['primary_spec']
            require(e.sha(observed['report'])==observed['report_sha256'] and e.sha(spec)==observed['spec_sha256'],'actual fault report/contract changed')
            row=outcome(observed['report'],spec,'failed' if mutated else 'passed',rule['category'] if mutated else None)
            command(observed['attempt'],spec,(receipt_name,receipt) if mutated else None)
            frame=None
            if mutated:
                frame=row['evidence']['screen_path'];body=e.data(frame);require(body and len(body)<1024**2,'original actual failed source-fault frame missing')
                if fault['id']=='F03':
                    first=next(i for i,s in enumerate(row['steps']) if s['status']=='failed')
                    require(row['steps'][first]['action']=='state' and e.load(spec)['steps'][first]['state']['path']=='selected.txt' and {'expect','snapshot','exit'}<=set(s['action'] for s in row['steps'][:first]),'earlier failure posing as saved-output corruption')
            calibrations.append(dict(fault=fault['id'],phase=observed['phase'],attempt=observed['attempt'],invocation=row['invocation_id'],report_sha256=observed['report_sha256'],actual_failure_frame=frame,actual_failure_frame_sha256=e.sha(frame) if frame else None))
    require(len(ordinary)==240 and len(calibrations)==9 and len(attempts)==len(invocations)==249,'actual final cell count differs')
    removed=target.startswith('peco/retained-source/')
    if removed:
        cleanup=e.load(target+'cleanup-inventory.json');removal=e.load(target+'removed.json')
        require(removal['removed'] and removal['cleanup_inventory_sha256']==e.sha(target+'cleanup-inventory.json') and cleanup['source_restored_exact'] and cleanup['actual_reports_with_confirmed_cleanup']>=249,'final source/runtime checked removal incomplete')
    return dict(schema_version=1,project='peco',host=host,helper_source_revision=revision,provider_run=run,generation=generation,
        declaration_sha256=sha256(declaration_path),ordinary_readbacks=240,calibration_readbacks=9,actual_attempts_verified=249,
        helper_files_verified=len(helper_accept),source_blobs_verified=len(primary),reviewed_modules=26,actual_native_compile_inputs=len(catalog['actual_native_compile_inputs']),
        actual_retained_executable_paths=len(binaries),all_target_workspace_cleanup=True,source_runtime_removed=removed,ordinary=ordinary,calibrations=calibrations,project_admissions=0)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('host',choices=['windows','linux']);parser.add_argument('--revision',required=True);parser.add_argument('--run');parser.add_argument('--generation',type=int);args=parser.parse_args()
    result=audit(args.host,args.revision,args.run,args.generation)
    name=args.host+'-final-cell-readback'+('-removed' if result['source_runtime_removed'] else '-before-cleanup')+'.json'
    immutable_json(DOC/'peco'/name,result)
    print('Independently verified240ordinary/9calibration actual reports,compiled faults,source/runtime/helper identities on',args.host,'removed:',result['source_runtime_removed'])


if __name__=='__main__':main()
