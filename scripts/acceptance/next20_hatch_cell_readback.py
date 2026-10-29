"""Independently audit actual interpreted Hatch final-cell evidence."""
import argparse
import copy
from email.parser import BytesParser
import hashlib
import io
import json
import ntpath
import posixpath
import subprocess
from pathlib import PurePosixPath, PureWindowsPath
import tarfile
import uuid
import zipfile

from next20_check import DOC, RAW, ROOT, NAME
from next20_native_packet_reader import read_packet
from next20_python_host_profile import application_profile
from next20_verify_jrnl import source_hashes
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def audit(host,revision,window=None,generation=None,run=None):
    scope='artifacts/'+NAME+'/';package=DOC/'hatch';native=host=='linux';records=None;local_records=None;closed_records={}
    if native:
        require(generation is not None and run is not None and window is None,'explicit native packet required')
        _,records=read_packet('hatch',generation);prefix='native/'+run+'/next20-hatch-linux-final/'
        provider_name='hatch/provider-linux-final-'+run+'.json';provider_path=RAW/provider_name
        if provider_path.is_file():provider=json.loads(provider_path.read_text())
        else:
            from next20_local_records import read_packet as read_local
            _,retained_local=read_local('hatch');provider=json.loads(retained_local[provider_name])
        require(provider['head_sha']==revision and provider['conclusion']=='success' and provider['status']=='completed' and provider['run_attempt']==1,'wrong provider source/outcome')
    else:prefix=''
    def logical_name(value):
        value=str(value).replace('\\','/').removeprefix(scope);value=posixpath.normpath(value)
        require(not value.startswith(('/','../')) and ':' not in value,'logical path escapes campaign')
        return value
    def data(relative):
        nonlocal local_records
        relative=logical_name(relative)
        if native:
            require(prefix+relative in records,'required native payload missing: '+relative)
            return records[prefix+relative]
        path=RAW/relative
        if path.is_file():return path.read_bytes()
        if relative.startswith('hatch/retained-source/'):
            key=relative.removeprefix('hatch/retained-source/')
            review_packet=RAW/'hatch/retained-source'
            if (review_packet/'review-inputs-index.json').is_file():
                from next20_review_input_packet import read
                if 'metadata' not in closed_records:closed_records['metadata']=read(review_packet)
                if key in closed_records['metadata']:return closed_records['metadata'][key]
            reference_manifest=RAW/'hatch/retained-source/canonical-native-references.json'
            if reference_manifest.exists():
                if key in json.loads(reference_manifest.read_text())['files']:
                    from next20_local_native_references import read_reference
                    return read_reference('hatch',key)
        if relative.startswith('hatch/final-series-native-exit-v1/'):
            from next20_local_records import read_packet as read_local
            if 'final' not in closed_records:_,closed_records['final']=read_local('hatch',packet='retained-complete-final-v1')
            require(relative in closed_records['final'],'closed complete final payload missing')
            return closed_records['final'][relative]
        if local_records is None:
            from next20_local_records import read_packet as read_local
            _,local_records=read_local('hatch')
        require(relative in local_records,'required local payload missing: '+relative)
        return local_records[relative]
    def load(relative):return json.loads(data(relative).decode('utf-8-sig'))
    def digest(relative):return hashlib.sha256(data(relative)).hexdigest()
    suffix='-'+window if window else ''
    declaration_path=package/('final-series-declaration-native-exit-v1'+suffix+'.json');declaration=json.loads(declaration_path.read_text())
    candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']==host)
    complete=load('hatch/final-execution-summary'+suffix+'.json');plan=load('hatch/final-execution-plan'+suffix+'.json')
    require(complete['plan_sha256']==digest('hatch/final-execution-plan'+suffix+'.json') and complete['declaration_sha256']==sha256(declaration_path),'final plan/declaration differs')
    require(complete['ordinary_executions']==240 and complete['calibrations']==9 and complete['host']==host,'partial final cell')
    target='hatch/retained-source/' if native or not (RAW/'active/hatch').is_dir() else 'active/hatch/'
    runtime=load(target+'runtime.json');inventory=load(target+'installed-inventory.json');owner=load(target+'task-owned.json')
    require(runtime['installed_inventory_sha256']==digest(target+'installed-inventory.json') and plan['runtime_sha256']==digest(target+'runtime.json'),'actual runtime inventory differs')
    pure=PurePosixPath if native else PureWindowsPath
    require(owner['pin']==json.loads((package/'source-provenance.json').read_text())['pin'] and owner['campaign']==NAME and owner['slug']=='hatch','wrong owned target')
    canonical=json.loads((package/'scenarios.json').read_text());cases={c['id']:c for c in canonical['cases']}
    host_decl=load('hatch/host-contracts/scenarios.json');native_cases={c['id']:c for c in host_decl['cases']}
    require(len(cases)==20 and set(cases)==set(native_cases),'missing/duplicate host cases')
    profile_path=package/'windows-profile-v1.json';profile=json.loads(profile_path.read_text())
    frozen=load('hatch/host-contracts/development-test-freeze.json')
    require(frozen['canonical_freeze_sha256']==sha256(package/'development-test-freeze.json'),'host canonical freeze differs')
    if not native:require(frozen['explicit_profile_sha256']==sha256(profile_path),'Windows application profile differs')
    for relative,expected in frozen['inputs'].items():require(digest('hatch/host-contracts/'+relative)==expected,'native frozen input changed')
    for cid,case in cases.items():
        expected=application_profile(json.loads((package/case['spec']).read_text()),case,host)
        directory=str(pure(owner['workspace'])/pure(scope+'hatch/host-contracts'))
        expected['command'][0]=(posixpath if native else ntpath).relpath(runtime['python'],directory).replace('\\','/')
        require(load('hatch/host-contracts/'+case['spec'])==expected,'host profile changed original inputs/oracles')
        require(native_cases[cid]['canonical_sha256']==case['spec_sha256'] and native_cases[cid]['spec_sha256']==digest('hatch/host-contracts/'+case['spec']),'host spec identity differs')
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
    generated=load('hatch/native-generated-source.json')['generated_files'] if native else json.loads((package/'runtime-generated-source.json').read_text())['generated_files']
    pristine={**primary,**{n:r['sha256'] for n,r in generated.items()}}
    lock=json.loads((package/'native-runtime-lock.json').read_text())
    review_root=RAW/('active/hatch' if (RAW/'active/hatch').is_dir() else 'hatch/retained-source')
    def review_data(relative):
        path=review_root/relative
        if path.is_file():return path.read_bytes()
        if (review_root/'review-inputs-index.json').is_file():
            from next20_review_input_packet import read
            if 'primary' not in closed_records:closed_records['primary']=read(review_root)
            if relative in closed_records['primary']:return closed_records['primary'][relative]
        from next20_local_records import read_packet as read_local
        if 'review' not in closed_records:_,closed_records['review']=read_local('hatch')
        key=path.relative_to(RAW).as_posix()
        require(key in closed_records['review'],'reviewed primary body missing')
        return closed_records['review'][key]
    primary_wheels={};primary_bodies=set()
    for directory,index_name,expected_hash in [('wheel-review-inputs','index-v2.json',lock['common_primary_inputs_sha256']),('linux-review-inputs','index.json',lock['linux_review_inputs_sha256'])]:
        index_body=review_data(directory+'/'+index_name)
        require(hashlib.sha256(index_body).hexdigest()==expected_hash,'reviewed wheel primary index differs')
        for wheel in json.loads(index_body)['wheels']:
            normalized=wheel['name'].lower().replace('_','-').replace('.','-')
            relative=directory+'/'+(wheel['wheel']+'.pypi.json' if directory=='wheel-review-inputs' else normalized+'-'+wheel['version']+'.json')
            primary_body=review_data(relative);primary_bodies.add(relative)
            require(hashlib.sha256(primary_body).hexdigest()==wheel['primary_metadata_sha256'],'primary release body differs')
            matches=[f for f in json.loads(primary_body)['urls'] if f['filename']==wheel['wheel'] and f['digests']['sha256']==wheel['sha256'] and f['size']==wheel['bytes']]
            require(len(matches)==1,'reviewed wheel absent from actual primary body')
            primary_wheels[wheel['wheel']]=wheel['sha256']
    for relative,row in generated.items():
        body=data(target+'generated-source/'+relative) if target.startswith('hatch/retained-source') else data(target+'src/'+relative)
        require(hashlib.sha256(body).hexdigest()==row['sha256'] and hashlib.sha256(body.replace(b'\r\n',b'\n')).hexdigest()==lock['generated_source_normalized_sha256'][relative],'actual generated source differs')
    installed=inventory['files'];events_seen=set();invocations=set();rows=[];fault_rows=[]
    site=next(n.removesuffix('hatch-'+lock['expected_version']+'.dist-info/METADATA') for n in installed if n.endswith('hatch-'+lock['expected_version']+'.dist-info/METADATA'))
    wheel_rows={r['filename']:r for r in lock['frozen_wheel_downloads']} if native else load(target+'dependency-fetch-v2.json')['wheels']
    require(len(wheel_rows)==(48 if native else 43),'dependency closure differs')
    covered=set();payload_count=0;code_count=0
    for filename,rule in wheel_rows.items():
        body=data(target+'wheels/'+filename)
        require(len(body)==rule['bytes'] and hashlib.sha256(body).hexdigest()==rule['sha256'],'retained reviewed wheel differs')
        require(primary_wheels.get(filename)==rule['sha256'],'actual wheel lacks independently read primary release digest')
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            metas=[n for n in archive.namelist() if n.endswith('.dist-info/METADATA') and len(n.split('/'))==2]
            require(len(metas)==1 and metas[0] not in covered,'ambiguous/duplicate top-level distribution metadata');meta=metas[0];covered.add(meta)
            info=BytesParser().parsebytes(archive.read(meta))
            distribution=info['Name'].lower().replace('_','-').replace('.','-')
            require(lock['versions'].get(distribution)==info['Version'],'installed distribution version differs from reviewed lock')
            for entry in archive.infolist():
                name=entry.filename
                if entry.is_dir() or name.endswith('.dist-info/RECORD'):continue
                if '.data/scripts/' in name:destination=('bin/' if native else 'Scripts/')+name.split('.data/scripts/',1)[1]
                else:
                    require('.data/' not in name,'unreviewed relocated wheel payload');destination=site+name
                require(installed.get(destination)==hashlib.sha256(archive.read(entry)).hexdigest(),'actual installed payload differs: '+filename+':'+name)
                payload_count+=1;code_count+=int(name.endswith(('.py','.so','.pyd','.dll','.pth','.exe')) or '.data/scripts/' in name)
    actual_metadata={n.removeprefix(site) for n in installed if n.startswith(site) and n.endswith('.dist-info/METADATA') and len(n.removeprefix(site).split('/'))==2}
    require(actual_metadata-covered=={n for n in actual_metadata if n.startswith(('pip-','hatch-'))},'uncovered installed distribution')
    hooks={n:d for n,d in installed.items() if n.endswith('.pth')}
    require(set(hooks)=={site+'distutils-precedence.pth',site+'_editable_impl_hatch.pth'},'unreviewed startup paths')
    editable=str(pure(owner['workspace'])/pure(scope+'active/hatch/src/src')).encode()
    require(hooks[site+'_editable_impl_hatch.pth']==hashlib.sha256(editable).hexdigest(),'editable startup is not exact owned source path')
    cleanup=load(target+'cleanup-inventory.json') if target.startswith('hatch/retained-source') else None
    for runtime_dir in ['venv','venv-pair-native-exit-v1-0','venv-pair-native-exit-v1-1']:
        for name,digest_value in installed.items():
            actual=cleanup['files'][runtime_dir+'/'+name]['sha256'] if cleanup else sha256(RAW/'active/hatch'/runtime_dir/name)
            require(actual==digest_value,'actual base/copied runtime bytes differ')
        if runtime_dir!='venv':
            expected_copy=(json.dumps(dict(source_inventory_sha256=digest(target+'installed-inventory.json'),source_relative_path='venv',cold_scope='First use of a newly materialized verified runtime, not OS-cache eviction'),sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
            actual=cleanup['files'][runtime_dir+'/copy-identity.json']['sha256'] if cleanup else sha256(RAW/'active/hatch'/runtime_dir/'copy-identity.json')
            require(actual==hashlib.sha256(expected_copy).hexdigest(),'cold runtime copy identity differs')
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'--','scripts/acceptance','scripts/ci'],cwd=ROOT).decode().splitlines()
    names=[n for n in names if n.endswith('.py')]
    blobs=subprocess.check_output(['git','cat-file','--batch'],input=''.join(revision+':'+n+'\n' for n in names).encode(),cwd=ROOT)
    require(len(blobs)<32*1024**2,'helper source bound');offset=0;helpers={};mixed_eol_helpers={}
    for n in names:
        end=blobs.index(b'\n',offset);header=blobs[offset:end].split();require(len(header)==3 and header[1]==b'blob','invalid helper blob')
        size=int(header[2]);require(0<=size<=2*1024**2,'helper blob bound');start=end+1;raw=blobs[start:start+size]
        require(len(raw)==size and blobs[start+size:start+size+1]==b'\n','helper framing')
        helpers[n]={hashlib.sha256(raw).hexdigest()}
        if not native:
            helpers[n].add(hashlib.sha256(raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest())
            working=(ROOT/n).read_bytes();working_sha=hashlib.sha256(working).hexdigest()
            if working_sha not in helpers[n] and working.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'):
                helpers[n].add(working_sha)
                mixed_eol_helpers[n]=dict(working_sha256=working_sha,git_sha256=hashlib.sha256(raw).hexdigest(),crlf_lines=working.count(b'\r\n'))
        offset=start+size+1
    require(offset==len(blobs),'trailing helper bytes')
    def command(eid,expected_source,spec,calibration=False,runtime_catalog=None):
        require(eid not in events_seen,'duplicate execution attempt');events_seen.add(eid)
        events={kind:load('events/'+eid+'-'+kind+'.json') for kind in ['started','identified','launched','finished']}
        require(all(v['phase']=='final-archive' and v['project']=='hatch' and v['id']==eid and v['campaign']==NAME for v in events.values()),'wrong-phase/project actual event')
        require(events['started']['ci_run_id']==(run if native else None),'wrong actual provider identity')
        ended=events['finished'];require(ended['category']=='passed' and ended['harness_cleanup']=='harness_process_reaped' and not ended['cleanup_errors'],'incomplete actual harness lifecycle')
        require(events['launched']['pid']>0 and digest('hatch/'+eid+'/console.log')==ended['console_sha256'],'missing launch/changed console')
        def manifest(reference):
            require(digest(reference['manifest'])==reference['sha256'],'actual manifest changed');return load(reference['manifest'])
        combined=manifest(events['identified']['identity']);base=manifest(combined['base']);target_catalog=manifest(combined['target_catalog'])
        files={}
        for raw,value in base['files'].items():
            normalized=posixpath.normpath(raw.replace('\\','/'))
            require(not normalized.startswith(('/','../')) and ':' not in normalized,'base path escapes checkout')
            require(normalized not in files or files[normalized]==value,'ambiguous base path alias');files[normalized]=value
        require(files.get(scope+'candidate-native-exit-v1/'+host+'/playtestr'+('' if native else '.exe'))==candidate['binary_sha256'],'wrong actual launched candidate')
        require(files.get(scope+logical_name(spec))==digest(spec),'actual launched spec differs')
        for relative,accepted in helpers.items():
            require(files.get(relative) in accepted,'stale actual execution helper '+relative)
        target_files=target_catalog['files'];actual={n.removeprefix(scope+'active/hatch/src/'):d for n,d in target_files.items() if n.startswith(scope+'active/hatch/src/')}
        require(actual==expected_source and target_files.get(scope+'active/hatch/runtime.json')==digest(target+'runtime.json'),'actual executed source/runtime differs')
        if runtime_catalog:require(target_files.get(scope+'active/hatch/launch-runtime-catalog.json')==digest(runtime_catalog),'actual launched runtime catalog differs')
        return events,files
    def outcome(report,spec,expected_status,category=None):
        require(report['report_version']==3 and report['runner_version']=='v0.4.0-rc.6' and report['os']==host and report['arch']=='amd64','wrong actual report/candidate/platform')
        require(len(report['results'])==1,'individual final report required');row=report['results'][0]
        require(row['status']==expected_status and row.get('failure',{}).get('category')==category,'wrong actual outcome')
        require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'target/workspace cleanup incomplete')
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'duplicate/cross invocation')
        invocations.add(row['invocation_id']);steps=load(spec)['steps']
        actions=[s['action'] for s in row['steps']];expected=[next(iter(s)) for s in steps]
        require(actions==expected if expected_status=='passed' else actions==expected[:len(actions)],'omitted/changed actual action sequence')
        if expected_status=='passed':require(all(s['status']=='passed' for s in row['steps']),'nonpositive passing steps')
        else:require(any(s['status']=='failed' for s in row['steps']),'failed mutation lacks failing step')
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-invocation saved state')
        if expected_status=='passed':
            expected_exits=[s['exit'] for s in steps if 'exit' in s]
            require(len(expected_exits)==1 and row['target']['exited'] and row['target']['exit_code']==expected_exits[0],'actual target exit differs from reviewed contract')
        return row
    folder='hatch/final-series-native-exit-v1'+suffix+'/'
    for batch in range(12):
        base=folder+str(batch)+'/';summary=load(base+'summary.json');prepared=load(base+'prepared.json');catalog=load(base+'runtime-catalog.json')
        require(complete['batches'][base+'summary.json']==digest(base+'summary.json') and summary['ordinary_executions']==20 and summary['batch']==batch,'partial/changed batch')
        require(summary['archive_sha256']==candidate['archive_sha256'] and summary['runner_sha256']==candidate['binary_sha256'],'mixed final archive')
        require(prepared['declaration_sha256']==sha256(declaration_path) and prepared['actual_runtime_catalog_sha256']==digest(base+'runtime-catalog.json'),'prepared declaration/catalog differs')
        require(catalog['files']==installed and catalog['executable_sha256']==runtime['python_sha256'],'actual dependency bytes differ')
        selected='venv-pair-native-exit-v1-'+str(batch//2) if batch<4 else 'venv'
        require(catalog['runtime_root']==scope+'active/hatch/'+selected and catalog['source_inventory_sha256']==digest(target+'installed-inventory.json'),'declared cold/reuse/base runtime schedule differs')
        require({r['case'] for r in summary['observations']}==set(cases) and len(summary['observations'])==20,'missing/duplicate batch case')
        for item in summary['observations']:
            cid=item['case'];case=native_cases[cid];planned=load(base+cid+'.planned.json');spec=logical_name(planned['spec']);value=load(spec)
            require(planned['spec_sha256']==digest(spec)==item['spec_sha256'] and planned['phase']=='final-archive' and planned['case']==cid and planned['batch']==batch,'actual planned contract differs')
            expected=copy.deepcopy(load('hatch/host-contracts/'+case['spec']))
            expected['command'][0]=posixpath.relpath(catalog['executable'],posixpath.dirname(scope+spec))
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
            for relative,expected_sha in frozen['inputs'].items():
                if relative.startswith(('fixture/','fixtures/','snapshots/')):
                    require(digest(posixpath.dirname(spec)+'/'+relative)==expected_sha,'repetition fixture/snapshot bytes changed')
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
            spec='hatch/host-contracts/'+json.loads((package/'fault-declaration.json').read_text())['primary_spec']
            report=load(result['report']);require(digest(result['report'])==result['report_sha256'] and result['spec_sha256']==digest(spec),'changed fault contract/report')
            actual=outcome(report,spec,'failed' if mutated else 'passed',rule['category'] if mutated else None)
            command(result['attempt'],source,spec,calibration=True)
            if mutated and fault['id']=='F03':
                first=next(i for i,s in enumerate(actual['steps']) if s['status']=='failed')
                require(all(s['status']=='passed' for s in actual['steps'][:first]) and actual['steps'][first]['action']=='state' and
                    load(spec)['steps'][first]['state']['path']=='pyproject.toml' and
                    {'expect','exit','snapshot'}<=set(s['action'] for s in actual['steps'][:first]),'saved corruption failed before terminal/exit/snapshot completion')
            frame=None
            if mutated:
                frame=actual['evidence']['screen_path'];body=data(frame)
                require(body and len(body)<1024**2,'actual failed calibration screen missing/bound')
                if fault['id']=='F01':require(b'Metadata detail' in body,'wrong source-prompt fault screen')
                if fault['id'] in {'F02','F03'}:require(b'Updated: pyproject.toml' in body and actual['target']['exit_code']==(7 if fault['id']=='F02' else 0),'wrong completed source-fault evidence/exit')
            fault_rows.append(dict(fault=fault['id'],phase=result['phase'],attempt=result['attempt'],invocation=actual['invocation_id'],report_sha256=result['report_sha256'],
                actual_failure_frame=frame,actual_failure_frame_sha256=digest(frame) if frame else None))
    require(len(rows)==240 and len(fault_rows)==9 and len(events_seen)==249,'actual final execution count differs')
    removed=False
    if target.startswith('hatch/retained-source'):
        cleanup=load(target+'cleanup-inventory.json');removal=load(target+'removed.json');proof=load('hatch/process-proof.json')
        require(removal['removed'] and removal['cleanup_inventory_sha256']==digest(target+'cleanup-inventory.json') and cleanup['source_restored_exact'],'source/runtime removal incomplete')
        require(cleanup['process_proof_sha256']==digest('hatch/process-proof.json') and proof['confirmed_no_matching_live_processes'] and not proof['matching_live_processes'],'process cleanup unconfirmed')
        require(pure(cleanup['owned_target'])==pure(owner['workspace'])/pure(scope+'active/hatch'),'unsafe cleanup target')
        require({n.removeprefix('src/'):r['sha256'] for n,r in cleanup['files'].items() if n.startswith('src/')}==pristine,'actual removed source not pristine')
        require(cleanup['actual_reports_with_confirmed_cleanup']>=249,'cleanup omitted actual final reports')
        removed=True
    result=dict(schema_version=1,project='hatch',host=host,helper_source_revision=revision,provider_run=run,
        declaration_sha256=sha256(declaration_path),window=window,ordinary_readbacks=240,calibration_readbacks=9,
        source_blobs_verified=len(primary),generated_source_files=len(generated),actual_attempts_verified=len(events_seen),
        ordinary=rows,calibrations=fault_rows,source_runtime_removed=removed,all_target_workspace_cleanup=True,
        helper_files_verified=len(helpers),explicit_mixed_eol_helper_bindings=mixed_eol_helpers,
        reviewed_dependency_wheels=len(wheel_rows),installed_wheel_payloads_verified=payload_count,installed_code_payloads_verified=code_count,
        reviewed_primary_release_bodies=len(primary_bodies),
        verified_runtime_roots=3,installed_inventory_files=len(installed),startup_paths_verified=True,
        runner_sha256=candidate['binary_sha256'],archive_sha256=candidate['archive_sha256'],
        project_admissions=0,
        scope='Actual reports,prelaunch helper/source/runtime/spec identities,reviewed host/repetition derivations,real source mutation/restoration and lifecycle readback. All-attempt completeness, retained evidence and project admission remain separate.')
    destination=RAW/'hatch/cell-readbacks'/(host+'-'+uuid.uuid4().hex+'.json');immutable_json(destination,result)
    print('Independently read back240 ordinary and9 real-source calibrations:',host,'source/runtime removed:',removed,'No project admission.')
    return destination


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['linux','windows'],required=True);parser.add_argument('--revision',required=True)
    parser.add_argument('--window');parser.add_argument('--generation',type=int);parser.add_argument('--run');args=parser.parse_args()
    audit(args.host,args.revision,args.window,args.generation,args.run)
