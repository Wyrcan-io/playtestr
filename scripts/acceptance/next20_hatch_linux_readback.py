"""Independently inspect actual Linux development, source and installed wheel bytes."""
from email.parser import BytesParser
import hashlib
import io
import json
import posixpath
import subprocess
import tarfile
import zipfile

from next20_check import DOC,RAW,NAME,ROOT
from next20_python_host_profile import application_profile
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    project='hatch';run='40925331521';revision='0ec1a3772556a61a3ce831b40721b62af5380565'
    package=DOC/project;packet=RAW/'native'/run/'next20-hatch-linux-development';scope='artifacts/'+NAME+'/'
    def data(name):return (packet/name).read_bytes()
    def value(name):return json.loads(data(name).decode('utf-8-sig'))
    provider=json.loads((RAW/project/('provider-linux-development-'+run+'.json')).read_text(encoding='utf-8'))
    require(provider['head_sha']==revision and provider['conclusion']=='success' and provider['run_attempt']==1,'wrong actual provider source/outcome')
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'--','scripts/acceptance','scripts/ci'],cwd=ROOT).decode().splitlines()
    names=[n for n in names if n.endswith('.py')]
    # Read raw Git blobs. Local `git archive` can apply Windows working-tree EOL
    # conversion, which is not the bytes executed on the Linux provider.
    git=subprocess.check_output(['git','cat-file','--batch'],input=''.join(revision+':'+n+'\n' for n in names).encode(),cwd=ROOT)
    require(len(git)<32*1024**2,'Git helper source blob bound')
    helpers={};offset=0
    for name in names:
        end=git.index(b'\n',offset);header=git[offset:end].split();require(len(header)==3 and header[1]==b'blob','Git raw source is not a blob')
        size=int(header[2]);require(0<=size<=2*1024**2,'Git helper blob size bound');start=end+1
        raw=git[start:start+size];require(len(raw)==size and git[start+size:start+size+1]==b'\n','Git blob framing differs')
        helpers[name]=hashlib.sha256(raw).hexdigest();offset=start+size+1
    require(offset==len(git),'trailing Git source bytes')
    retained='hatch/retained-source/';owner=value(retained+'task-owned.json');runtime=value(retained+'runtime.json');build=value(retained+'build.json')
    lock=json.loads((package/'native-runtime-lock.json').read_text(encoding='utf-8'));primary=json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))['files']
    require(value(retained+'acquisition.json')['source_files']==primary,'native source acquisition differs')
    source={}
    with tarfile.open(fileobj=io.BytesIO(data(retained+'source.tar.gz')),mode='r:gz') as archive:
        for member in archive:
            require(not member.issym() and not member.islnk(),'unexpected source archive link')
            if not member.isfile():continue
            name=member.name.split('/',1)[1]
            require(name not in source and member.size<=4*1024**2,'source archive member bound/duplicate')
            source[name]=hashlib.sha256(archive.extractfile(member).read()).hexdigest()
    require(source==primary and len(source)==546,'actual retained source archive differs from all546 pinned files')
    generated=value('hatch/native-generated-source.json')['generated_files']
    require(set(generated)==set(lock['generated_source_files']),'native generated source differs')
    for name,row in generated.items():
        raw=data(retained+'generated-source/'+name)
        require(hashlib.sha256(raw).hexdigest()==row['sha256'] and hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()==lock['generated_source_normalized_sha256'][name],'generated version module bytes differ')
    source.update({n:r['sha256'] for n,r in generated.items()})
    contracts='hatch/host-contracts/';declaration=value(contracts+'scenarios.json');frozen=value(contracts+'development-test-freeze.json')
    require(frozen['canonical_freeze_sha256']==sha256(package/'development-test-freeze.json'),'native contract freeze lacks canonical binding')
    for name,digest in frozen['inputs'].items():require(hashlib.sha256(data(contracts+name)).hexdigest()==digest,'changed native frozen input')
    summaries=list((packet/'hatch/development').glob('*/summary.json'));require(len(summaries)==1,'one native development window required')
    summary=json.loads(summaries[0].read_text(encoding='utf-8'));require(summary['passed']==20 and summary['failed']==0 and summary['declaration_sha256']==hashlib.sha256(data(contracts+'scenarios.json')).hexdigest(),'native20-case outcome differs')
    install=value('candidate-native-exit-v1/linux/installed.json')
    candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']=='linux')
    require(all(install[k]==candidate[k] for k in ['archive_sha256','binary_sha256']),'wrong native runner archive')
    observations=[]
    for case,observed in zip(declaration['cases'],summary['results'],strict=True):
        require(case['id']==observed['case'],'native case order differs')
        spec=value(contracts+case['spec']);canonical=json.loads((package/case['spec']).read_text(encoding='utf-8'))
        expected=application_profile(canonical,case,'linux');expected['command'][0]=posixpath.relpath(runtime['python'],owner['workspace']+'/'+scope+contracts.rstrip('/'))
        require(spec==expected,'actual host contract changes more than declared application profile')
        require(hashlib.sha256(data(contracts+case['spec'])).hexdigest()==case['spec_sha256'],'native spec digest differs')
        report_name=observed['report'].removeprefix(scope);report=value(report_name)
        require(hashlib.sha256(data(report_name)).hexdigest()==observed['report_sha256'] and len(report['results'])==1,'native actual report differs')
        result=report['results'][0]
        require(result['status']=='passed' and result['invocation_id']==observed['invocation'] and all(s['status']=='passed' for s in result['steps']),'nonpositive native steps or invocation')
        require(result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'native target/workspace cleanup incomplete')
        for step in result['steps']:
            if 'state' in step:require(step['state']['invocation_id']==result['invocation_id'] and step['state']['workspace_id']==result['workspace']['id'],'cross-invocation state evidence')
        events={kind:value('events/'+observed['attempt']+'-'+kind+'.json') for kind in ['started','identified','launched','finished']}
        require(all(e['project']=='hatch' and e['phase']=='development' for e in events.values()),'wrong native project/phase')
        require(events['started']['ci_run_id']==run and events['finished']['exit_code']==0 and events['finished']['category']=='passed' and not events['finished']['cleanup_errors'] and events['finished']['harness_cleanup']=='harness_process_reaped','native lifecycle/provider binding differs')
        ref=events['identified']['identity'];require(hashlib.sha256(data(ref['manifest'])).hexdigest()==ref['sha256'],'native identity hash differs');identity=value(ref['manifest'])
        for key in ['base','target_catalog']:
            ref=identity[key];require(hashlib.sha256(data(ref['manifest'])).hexdigest()==ref['sha256'],'native identity catalog hash differs')
        targets=value(identity['target_catalog']['manifest'])['files'];base=value(identity['base']['manifest'])['files']
        actual={n.removeprefix(scope+'active/hatch/src/'):d for n,d in targets.items() if n.startswith(scope+'active/hatch/src/')}
        require(actual==source and targets[scope+'active/hatch/runtime.json']==hashlib.sha256(data(retained+'runtime.json')).hexdigest(),'actual prelaunch source/runtime differs')
        require(all(base.get(n)==d for n,d in helpers.items()),'actual executed helper bytes differ from provider Git revision')
        require(base.get(scope+'candidate-native-exit-v1/linux/playtestr')==install['binary_sha256'] and base.get(scope+contracts+case['spec'])==case['spec_sha256'],'actual launched runner/spec differs')
        console=data('hatch/'+observed['attempt']+'/console.log');require(hashlib.sha256(console).hexdigest()==events['finished']['console_sha256'],'actual native console differs')
        observations.append(dict(case=case['id'],attempt=observed['attempt'],invocation=result['invocation_id'],report_sha256=observed['report_sha256'],positive_steps=len(result['steps']),same_invocation_state=True,source_files=len(source),target_cleanup=True,workspace_cleanup=True))
    require(len(observations)==20,'native cell incomplete')
    installed=value(retained+'installed-inventory.json')['files'];cleanup=value(retained+'cleanup-inventory.json');removed=value(retained+'removed.json')
    require(removed['removed'] and removed['cleanup_inventory_sha256']==hashlib.sha256(data(retained+'cleanup-inventory.json')).hexdigest(),'native actual source/runtime removal proof differs')
    for name,digest in installed.items():require(cleanup['files']['venv/'+name]['sha256']==digest,'actual removed installed file differs')
    for name,digest in source.items():require(cleanup['files']['src/'+name]['sha256']==digest,'actual removed source file differs')
    require(cleanup['actual_reports_with_confirmed_cleanup']==20,'wrong cleanup report denominator')
    site=next(n.removesuffix('hatch-'+lock['expected_version']+'.dist-info/METADATA') for n in installed if n.endswith('hatch-'+lock['expected_version']+'.dist-info/METADATA'))
    expected_wheels={r['filename']:r for r in lock['frozen_wheel_downloads']};wheel_inventory=value(retained+'wheels.json')
    require(set(wheel_inventory)==set(expected_wheels) and len(expected_wheels)==48,'actual native wheel closure differs')
    covered=set();payloads=0;code_files=0
    for filename,row in expected_wheels.items():
        raw=data(retained+'wheels/'+filename);require(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'] and wheel_inventory[filename]['sha256']==row['sha256'],'actual retained native wheel differs from reviewed primary lock')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            meta=next(i.filename for i in archive.infolist() if i.filename.endswith('.dist-info/METADATA') and len(i.filename.split('/'))==2)
            info=BytesParser().parsebytes(archive.read(meta));require(info['Version']==row['version'],'actual distribution version differs')
            covered.add(meta)
            for entry in archive.infolist():
                name=entry.filename
                if entry.is_dir() or name.endswith('.dist-info/RECORD'):continue
                if '.data/scripts/' in name:
                    target_name='bin/'+name.split('.data/scripts/',1)[1]
                else:
                    require('.data/' not in name,'unreviewed relocated wheel payload');target_name=site+name
                require(installed.get(target_name)==hashlib.sha256(archive.read(entry)).hexdigest(),'actual installed wheel payload differs: '+filename+':'+name)
                payloads+=1;code_files+=int(name.endswith(('.py','.so','.pyd','.dll','.pth')))
    actual_metadata={n.removeprefix(site) for n in installed if n.startswith(site) and n.endswith('.dist-info/METADATA') and len(n.removeprefix(site).split('/'))==2}
    require(actual_metadata-covered=={n for n in actual_metadata if n.startswith(('pip-','hatch-'))},'uncovered native installed distribution')
    hooks={n:d for n,d in installed.items() if n.endswith('.pth')}
    require(set(hooks)=={site+'distutils-precedence.pth',site+'_editable_impl_hatch.pth'},'unreviewed installed startup paths')
    require(hooks[site+'_editable_impl_hatch.pth']==hashlib.sha256((owner['workspace']+'/'+scope+'active/hatch/src/src').encode()).hexdigest(),'editable startup path not exact owned source/src')
    destination=package/'linux-development-readback.json'
    immutable_json(destination,dict(schema_version=1,run=run,revision=revision,host='linux',status='actual20-development-outcomes-source-runtime-dependencies-and-cleanup-verified',
        observations=observations,primary_source_files=546,generated_source_files=1,executed_helper_files=len(helpers),
        actual_dependency_wheels=48,installed_wheel_payloads_verified=payloads,installed_code_payloads_verified=code_files,
        actual_installed_inventory_files=len(installed),source_runtime_removed=True,canonical_freeze_sha256=sha256(package/'development-test-freeze.json'),
        native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),native_archive_sha256=install['archive_sha256'],native_binary_sha256=install['binary_sha256'],
        final_ordinary_credit=0,project_admissions=0,scope='Actual20-case native development plus exact installed dependency/source/prelaunch/lifecycle evidence; not final repetitions. Read-only Python SDK/venv bootstrap is a prerequisite, not retained full SDK or isolation.'))
    print('Independently verified actual20 Linux outcomes,547 source files,all48 reviewed wheel payloads,all launch identities and checked source/runtime removal.')


if __name__=='__main__':main()
