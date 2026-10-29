"""Independently audit actual interpreted PDM final-cell evidence."""
import argparse
import copy
import hashlib
import io
import json
import ntpath
import posixpath
from pathlib import PurePosixPath, PureWindowsPath
import tarfile
import uuid
import zipfile

from next20_check import DOC, RAW, ROOT, NAME
from next20_native_packet_reader import read_packet
from next20_python_host_profile import wizard_profile
from next20_verify_jrnl import source_hashes
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def audit(host,revision,window=None,generation=None,run=None):
    scope='artifacts/'+NAME+'/';package=DOC/'pdm';native=host=='linux';records=None;local_records=None;closed_records={}
    if native:
        require(generation is not None and run is not None and window is None,'explicit native packet required')
        _,records=read_packet('pdm',generation);prefix='native/'+run+'/next20-pdm-linux-final/'
        provider=json.loads(records['native/'+run+'/run-metadata.json'])
        require(provider['headSha']==revision and provider['conclusion']=='success' and provider['status']=='completed','wrong provider source/outcome')
        jobs=[j for j in provider['jobs'] if j['name']=='native-validation']
        require(len(jobs)==1 and jobs[0]['conclusion']=='success','missing successful actual native job')
        steps={s['name']:s['conclusion'] for s in jobs[0]['steps']}
        require(steps.get('Execute twelve fresh final batches and three real source faults')=='success' and
            steps.get('Retain verified sources and dependencies and confirm native cleanup')=='success','missing complete provider execution/cleanup steps')
    else:prefix=''
    def name(value):
        value=str(value).replace('\\','/').removeprefix(scope);value=posixpath.normpath(value)
        require(not value.startswith(('/','../')) and ':' not in value,'logical path escapes campaign')
        return value
    def data(relative):
        nonlocal local_records
        relative=name(relative)
        if native:
            require(prefix+relative in records,'required native payload missing: '+relative)
            return records[prefix+relative]
        path=RAW/relative
        if path.is_file():return path.read_bytes()
        for subset,packet in [('final-series-native-exit-v1-v2','retained-complete-final-v2'),('final-series-native-exit-v1','retained-failed-final-v1')]:
            if relative.startswith('pdm/'+subset+'/'):
                from next20_local_records import read_packet as read_local
                if packet not in closed_records:_,closed_records[packet]=read_local('pdm',packet=packet)
                require(relative in closed_records[packet],'closed final payload missing')
                return closed_records[packet][relative]
        if local_records is None:
            from next20_local_records import read_packet as read_local
            _,local_records=read_local('pdm')
        require(relative in local_records,'required local payload missing: '+relative)
        return local_records[relative]
    def load(relative):return json.loads(data(relative).decode('utf-8-sig'))
    def digest(relative):return hashlib.sha256(data(relative)).hexdigest()
    suffix='-'+window if window else ''
    declaration_path=package/('final-series-declaration-native-exit-v1'+suffix+'.json');declaration=json.loads(declaration_path.read_text())
    candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']==host)
    complete=load('pdm/final-execution-summary'+suffix+'.json');plan=load('pdm/final-execution-plan'+suffix+'.json')
    require(complete['plan_sha256']==digest('pdm/final-execution-plan'+suffix+'.json') and complete['declaration_sha256']==sha256(declaration_path),'final plan/declaration differs')
    require(complete['ordinary_executions']==240 and complete['calibrations']==9 and complete['host']==host,'partial final cell')
    target='pdm/retained-source/' if native or not (RAW/'active/pdm').is_dir() else 'active/pdm/'
    runtime=load(target+'runtime.json');inventory=load(target+'installed-inventory.json');owner=load(target+'task-owned.json')
    require(runtime['installed_inventory_sha256']==digest(target+'installed-inventory.json') and plan['runtime_sha256']==digest(target+'runtime.json'),'actual runtime inventory differs')
    pure=PurePosixPath if native else PureWindowsPath
    require(owner['pin']==json.loads((package/'source-provenance.json').read_text())['pin'] and owner['campaign']==NAME and owner['slug']=='pdm','wrong owned target')
    canonical=json.loads((package/'scenarios.json').read_text());cases={c['id']:c for c in canonical['cases']}
    host_decl=load('pdm/host-contracts/scenarios.json');native_cases={c['id']:c for c in host_decl['cases']}
    require(len(cases)==20 and set(cases)==set(native_cases),'missing/duplicate host cases')
    profile_path=package/('native-profile-v2.json' if native else 'windows-profile-v1.json');profile=json.loads(profile_path.read_text())
    frozen=load('pdm/host-contracts/development-test-freeze.json')
    require(frozen['explicit_profile_sha256']==sha256(profile_path) and frozen['canonical_freeze_sha256']==sha256(package/'development-test-freeze.json'),'host profile freeze differs')
    for relative,expected in frozen['inputs'].items():require(digest('pdm/host-contracts/'+relative)==expected,'native frozen input changed')
    for cid,case in cases.items():
        expected=wizard_profile(json.loads((package/case['spec']).read_text()),dict(case,**profile['case_profiles'].get(cid,{})),runtime['python'],host)
        directory=str(pure(owner['workspace'])/pure(scope+'pdm/host-contracts'))
        expected['command'][0]=(posixpath if native else ntpath).relpath(runtime['python'],directory).replace('\\','/')
        require(load('pdm/host-contracts/'+case['spec'])==expected,'host profile changed original inputs/oracles')
        require(native_cases[cid]['canonical_sha256']==case['spec_sha256'] and native_cases[cid]['spec_sha256']==digest('pdm/host-contracts/'+case['spec']),'host spec identity differs')
    provenance=json.loads((package/'source-provenance.json').read_text());primary=provenance['files'];acquired=load(target+'acquisition.json')
    require(acquired['source_files']==primary and acquired['archive_sha256']==digest(target+'source.tar.gz'),'source acquisition differs')
    source_bytes={}
    with tarfile.open(fileobj=io.BytesIO(data(target+'source.tar.gz')),mode='r:gz') as bundle:
        for member in bundle:
            if member.isdir():continue
            relative=member.name.split('/',1)[1]
            require(member.isfile() and relative in primary and relative not in source_bytes and member.size<=8*1024**2,'unsafe source archive entry')
            raw=bundle.extractfile(member).read(member.size+1);require(len(raw)==member.size and hashlib.sha256(raw).hexdigest()==primary[relative],'actual source blob differs')
            source_bytes[relative]=raw
    require(set(source_bytes)==set(primary),'source archive omitted primary files')
    generated=load('pdm/native-generated-source.json')['generated_files'] if native else json.loads((package/'runtime-generated-source.json').read_text())['generated_files']
    pristine={**primary,**{n:r['sha256'] for n,r in generated.items()}}
    installed=inventory['files'];events_seen=set();invocations=set();rows=[];fault_rows=[]
    def command(eid,expected_source,spec,calibration=False,runtime_catalog=None):
        require(eid not in events_seen,'duplicate execution attempt');events_seen.add(eid)
        events={kind:load('events/'+eid+'-'+kind+'.json') for kind in ['started','identified','launched','finished']}
        require(all(v['phase']=='final-archive' and v['project']=='pdm' and v['id']==eid and v['campaign']==NAME for v in events.values()),'wrong-phase/project actual event')
        require(events['started']['ci_run_id']==(run if native else None),'wrong actual provider identity')
        ended=events['finished'];require(ended['category']=='passed' and ended['harness_cleanup']=='harness_process_reaped' and not ended['cleanup_errors'],'incomplete actual harness lifecycle')
        require(events['launched']['pid']>0 and digest('pdm/'+eid+'/console.log')==ended['console_sha256'],'missing launch/changed console')
        def manifest(reference):
            require(digest(reference['manifest'])==reference['sha256'],'actual manifest changed');return load(reference['manifest'])
        combined=manifest(events['identified']['identity']);base=manifest(combined['base']);target_catalog=manifest(combined['target_catalog'])
        files={}
        for raw,value in base['files'].items():
            normalized=posixpath.normpath(raw.replace('\\','/'))
            require(not normalized.startswith(('/','../')) and ':' not in normalized,'base path escapes checkout')
            require(normalized not in files or files[normalized]==value,'ambiguous base path alias');files[normalized]=value
        require(files.get(scope+'candidate-native-exit-v1/'+host+'/playtestr'+('' if native else '.exe'))==candidate['binary_sha256'],'wrong actual launched candidate')
        require(files.get(scope+name(spec))==digest(spec),'actual launched spec differs')
        helpers=['next20_check.py','adversarial_process.py','readiness_evidence.py','next20_candidate.py',
            'next20_python_faults.py' if calibration else 'next20_jrnl_final.py']
        for helper in helpers:
            relative='scripts/acceptance/'+helper
            require(files.get(relative) in source_hashes(revision,relative),'stale actual execution helper '+helper)
        target_files=target_catalog['files'];actual={n.removeprefix(scope+'active/pdm/src/'):d for n,d in target_files.items() if n.startswith(scope+'active/pdm/src/')}
        require(actual==expected_source and target_files.get(scope+'active/pdm/runtime.json')==digest(target+'runtime.json'),'actual executed source/runtime differs')
        if runtime_catalog:require(target_files.get(scope+'active/pdm/launch-runtime-catalog.json')==digest(runtime_catalog),'actual launched runtime catalog differs')
        return events,files
    def outcome(report,spec,expected_status,category=None):
        require(report['report_version']==3 and report['runner_version']=='v0.4.0-rc.6' and report['os']==host and report['arch']=='amd64','wrong actual report/candidate/platform')
        require(len(report['results'])==1,'individual final report required');row=report['results'][0]
        require(row['status']==expected_status and row.get('failure',{}).get('category')==category,'wrong actual outcome')
        require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'target/workspace cleanup incomplete')
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'duplicate/cross invocation')
        invocations.add(row['invocation_id']);steps=load(spec)['steps']
        require([s['action'] for s in row['steps']]==[next(iter(s)) for s in steps],'omitted/changed actual action sequence')
        if expected_status=='passed':require(all(s['status']=='passed' for s in row['steps']),'nonpositive passing steps')
        else:require(any(s['status']=='failed' for s in row['steps']),'failed mutation lacks failing step')
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-invocation saved state')
        return row
    folder='pdm/final-series-native-exit-v1'+suffix+'/'
    for batch in range(12):
        base=folder+str(batch)+'/';summary=load(base+'summary.json');prepared=load(base+'prepared.json');catalog=load(base+'runtime-catalog.json')
        require(complete['batches'][base+'summary.json']==digest(base+'summary.json') and summary['ordinary_executions']==20 and summary['batch']==batch,'partial/changed batch')
        require(summary['archive_sha256']==candidate['archive_sha256'] and summary['runner_sha256']==candidate['binary_sha256'],'mixed final archive')
        require(prepared['declaration_sha256']==sha256(declaration_path) and prepared['actual_runtime_catalog_sha256']==digest(base+'runtime-catalog.json'),'prepared declaration/catalog differs')
        require(catalog['files']==installed and catalog['executable_sha256']==runtime['python_sha256'],'actual dependency bytes differ')
        require({r['case'] for r in summary['observations']}==set(cases) and len(summary['observations'])==20,'missing/duplicate batch case')
        for item in summary['observations']:
            cid=item['case'];case=native_cases[cid];planned=load(base+cid+'.planned.json');spec=name(planned['spec']);value=load(spec)
            require(planned['spec_sha256']==digest(spec)==item['spec_sha256'] and planned['phase']=='final-archive' and planned['case']==cid and planned['batch']==batch,'actual planned contract differs')
            expected=copy.deepcopy(load('pdm/host-contracts/'+case['spec']))
            expected['command'][0]=posixpath.relpath(catalog['executable'],posixpath.dirname(scope+spec))
            expected['command'][expected['command'].index('--python')+1]=str(pure(owner['workspace'])/pure(catalog['executable']))
            if batch==4:expected.update(width=expected['width']+10,height=expected['height']+2)
            if batch==7:
                split=[]
                for step in expected['steps']:
                    text=step.get('text')
                    if set(step)=={'text'} and len(text)>1 and all(ord(c)>=32 and ord(c)!=127 for c in text):split.extend({'text':text[i:i+3]} for i in range(0,len(text),3))
                    else:split.append(step)
                expected['steps']=split
            if batch==10 and cid=='N01':expected['height']=12
            if batch==11:expected['startup_timeout_ms']=declaration.get('startup_timeout_ms_by_host',{}).get(host,2000)
            require(value==expected,'actual repetition changed reviewed actions/oracles beyond declared variation')
            if batch==5:require(' ' in posixpath.basename(posixpath.dirname(spec)) and any(ord(c)>127 for c in posixpath.basename(posixpath.dirname(spec))),'missing actual Unicode relocation')
            report=load(base+cid+'.report.json');require(digest(base+cid+'.report.json')==item['report_sha256'],'actual report reference changed')
            actual=outcome(report,spec,'passed');events,files=command(item['attempt'],pristine,spec,runtime_catalog=base+'runtime-catalog.json')
            require(files.get(catalog['executable'])==runtime['python_sha256'],'actual selected interpreter differs')
            require(events['started']['variation']==('owned 2-second 8-MiB SHA256 CPU worker' if batch in {8,9} else 'ordinary'),'missing declared load schedule')
            rows.append(dict(batch=batch,case=cid,attempt=item['attempt'],invocation=actual['invocation_id'],report_sha256=digest(base+cid+'.report.json'),spec_sha256=digest(spec)))
    faults=load(complete['fault_summary']);require(digest(complete['fault_summary'])==complete['fault_summary_sha256'] and faults['phase']=='final-archive','fault summary/phase differs')
    declared={f['id']:f for f in json.loads((package/'fault-declaration.json').read_text())['faults']}
    require(len(faults['faults'])==3 and {f['id'] for f in faults['faults']}==set(declared),'missing actual source faults')
    for fault in faults['faults']:
        rule=declared[fault['id']];original=source_bytes[rule['path']];before=rule['before'].encode();after=rule['after'].encode()
        require(original.count(before)==1 and fault['original_sha256']==fault['restored_sha256']==hashlib.sha256(original).hexdigest() and fault['restored_exact'],'source original/restoration differs')
        require(fault['mutated_sha256']==hashlib.sha256(original.replace(before,after)).hexdigest(),'actual source mutation differs')
        require(len(fault['outcomes'])==3 and {p['phase'] for p in fault['outcomes']}=={'baseline','mutated','restored'},'partial calibration')
        for result in fault['outcomes']:
            mutated=result['phase']=='mutated';source=dict(pristine)
            if mutated:source[rule['path']]=fault['mutated_sha256']
            spec='pdm/host-contracts/'+json.loads((package/'fault-declaration.json').read_text())['primary_spec']
            report=load(result['report']);require(digest(result['report'])==result['report_sha256'] and result['spec_sha256']==digest(spec),'changed fault contract/report')
            actual=outcome(report,spec,'failed' if mutated else 'passed',rule['category'] if mutated else None)
            command(result['attempt'],source,spec,calibration=True)
            if mutated and fault['id']=='F03':
                first=next(i for i,s in enumerate(actual['steps']) if s['action']=='state')
                require(all(s['status']=='passed' for s in actual['steps'][:first]) and actual['steps'][first]['status']=='failed','saved corruption failed before terminal/exit/snapshot completion')
            fault_rows.append(dict(fault=fault['id'],phase=result['phase'],attempt=result['attempt'],invocation=actual['invocation_id'],report_sha256=result['report_sha256']))
    require(len(rows)==240 and len(fault_rows)==9 and len(events_seen)==249,'actual final execution count differs')
    removed=False
    if target.startswith('pdm/retained-source'):
        cleanup=load(target+'cleanup-inventory.json');removal=load(target+'removed.json');proof=load('pdm/process-proof.json')
        require(removal['removed'] and removal['cleanup_inventory_sha256']==digest(target+'cleanup-inventory.json') and cleanup['source_restored_exact'],'source/runtime removal incomplete')
        require(cleanup['process_proof_sha256']==digest('pdm/process-proof.json') and proof['confirmed_no_matching_live_processes'] and not proof['matching_live_processes'],'process cleanup unconfirmed')
        require(pure(cleanup['owned_target'])==pure(owner['workspace'])/pure(scope+'active/pdm'),'unsafe cleanup target')
        require({n.removeprefix('src/'):r['sha256'] for n,r in cleanup['files'].items() if n.startswith('src/')}==pristine,'actual removed source not pristine')
        require(cleanup['actual_reports_with_confirmed_cleanup']>=249,'cleanup omitted actual final reports')
        removed=True
    result=dict(schema_version=1,project='pdm',host=host,helper_source_revision=revision,provider_run=run,
        declaration_sha256=sha256(declaration_path),window=window,ordinary_readbacks=240,calibration_readbacks=9,
        source_blobs_verified=len(primary),generated_source_files=len(generated),actual_attempts_verified=len(events_seen),
        ordinary=rows,calibrations=fault_rows,source_runtime_removed=removed,all_target_workspace_cleanup=True,
        runner_sha256=candidate['binary_sha256'],archive_sha256=candidate['archive_sha256'],
        historical_screen_gap_open=True,project_admissions=0,
        scope='Actual reports,prelaunch helper/source/runtime/spec identities,reviewed host/repetition derivations,real source mutation/restoration and lifecycle readback. Historical frame completeness and project admission remain separate.')
    destination=RAW/'pdm/cell-readbacks'/(host+'-'+uuid.uuid4().hex+'.json');immutable_json(destination,result)
    print('Independently read back240 ordinary and9 real-source calibrations:',host,'source/runtime removed:',removed,'No project admission.')
    return destination


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['linux','windows'],required=True);parser.add_argument('--revision',required=True)
    parser.add_argument('--window');parser.add_argument('--generation',type=int);parser.add_argument('--run');args=parser.parse_args()
    audit(args.host,args.revision,args.window,args.generation,args.run)
