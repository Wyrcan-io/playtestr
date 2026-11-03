"""Verify actual normal source rebuilds and their nine recovery-window phases."""
import argparse
import hashlib
import io
import json
import posixpath
from pathlib import PurePosixPath, PureWindowsPath
import tarfile

from next20_check import DOC, RAW, NAME
from next20_native_packet_reader import read_packet
from next20_peco_cell_readback import Evidence
from next20_peco_development_readback import git_inputs
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def audit(host,revision,run=None,generation=None):
    e=Evidence(host,run,generation,'next20-peco-linux-rebuild-recovery');scope='artifacts/'+NAME+'/'
    target='active/peco/' if host=='windows' and (RAW/'active/peco').is_dir() else 'peco/retained-source-rebuild-v1/'
    package=DOC/'peco';declaration_path=package/'rebuild-recovery-declaration-v1.json';declaration=json.loads(declaration_path.read_text())
    if host=='linux':
        provider=json.loads((RAW/'peco'/('retained-native-v'+str(generation))/'provider.json').read_text())
        require(provider['headSha']==revision and provider['conclusion']=='success' and provider['status']=='completed','normal-rebuild provider/source differs')
    complete=e.load('peco/rebuild-recovery-summary-v1.json');plan=e.load('peco/rebuild-recovery-execution-plan-v1.json')
    require(complete['host']==host and complete['calibrations']==9 and complete['normal_restoration_rebuilds']==3 and complete['plan_sha256']==e.sha('peco/rebuild-recovery-execution-plan-v1.json') and complete['declaration_sha256']==sha256(declaration_path),'normal-rebuild window incomplete/mixed')
    build=e.load(target+'build.json');runtime=e.load(target+'runtime.json');owner=e.load(target+'task-owned.json');fetch=e.load(target+'module-fetch.json');catalog=e.load(target+'dependency-source-catalog.json')
    require(plan['build_sha256']==e.sha(target+'build.json') and plan['runtime_sha256']==e.sha(target+'runtime.json'),'actual rebuild baseline metadata changed')
    baseline=declaration['original_baseline'][host]
    require(build['actual_target_sha256']==baseline['app_sha256'] and build['binary_sha256']==baseline['capture_sha256'] and build['compiler_sha256']==baseline['compiler_sha256'],'ordinary baseline/prerequisite changed')
    primary=json.loads((package/'source-provenance.json').read_text())['files'];review=json.loads((package/'dependency-source-review-declaration.json').read_text())
    _,original=read_packet('peco',2);original_catalog=json.loads(original['native/41041642421/next20-peco-linux-development/peco/retained-source/dependency-source-catalog.json'])
    require(catalog['files']==original_catalog['files'],'rebuild primary/module source differs from full reviewed archive bodies')
    source={};links={}
    with tarfile.open(fileobj=io.BytesIO(e.data(target+'source.tar.gz')),mode='r:gz') as stream:
        for member in stream:
            if member.isdir():continue
            name=member.name.split('/',1)[1]
            require(name not in source and name not in links,'duplicate original source archive entry')
            if member.issym():links[name]=member.linkname;continue
            require(member.isfile() and name in primary and member.size<=8*1024**2,'unsafe source archive body')
            raw=stream.extractfile(member).read(member.size+1)
            require(hashlib.sha256(raw).hexdigest()==primary[name],'source archive body changed');source[name]=raw
    require(set(source)==set(primary) and links==json.loads((package/'source-link-policy.json').read_text())['omitted_documentation_links'],'source/link coverage incomplete')
    corpus='peco/go-module-corpus-rebuild-v1/';corpus_index=e.load(corpus+'index.json')
    for name,row in corpus_index['files'].items():require(len(e.data(corpus+name))==row['bytes'] and e.sha(corpus+name)==row['sha256'],'retained module/graph metadata changed')
    for module in fetch['modules']:
        name='archives/'+module['Path']+'/@v/'+module['Version']+'.zip'
        require(e.sha(corpus+name)==review['modules'][module['Path']+'@'+module['Version']]['zip_sha256'],'actual normal-build module archive changed')
    binaries_index=e.load(corpus+'executables-index.json');archive=e.data(corpus+'executables.tar.xz')
    require(hashlib.sha256(archive).hexdigest()==binaries_index['archive_sha256'],'normal-build executable archive changed')
    physical={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:xz') as stream:
        for member in stream:
            require(member.isfile() and member.name in binaries_index['files'] and member.name not in physical and member.size<=16*1024**2,'unsafe normal-build binary body')
            physical[member.name]=stream.extractfile(member).read(member.size+1)
    binaries={}
    for name,row in binaries_index['files'].items():
        raw=physical[row.get('member',name)]
        require(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'actual rebuilt image body changed');binaries[name]=row['sha256']
    helpers=git_inputs(revision)
    if host=='windows':
        from next20_review_input_packet import read
        actual=read(RAW/'peco/execution-helper-source-rebuild-v1')
        for name,expected in list(helpers.items()):
            raw=actual[name];normalized=raw.replace(b'\r\n',b'\n')
            require(expected in {hashlib.sha256(raw).hexdigest(),hashlib.sha256(normalized).hexdigest(),hashlib.sha256(normalized.replace(b'\n',b'\r\n')).hexdigest()},'normal-build actual helper differs beyond line endings')
            helpers[name]=hashlib.sha256(raw).hexdigest()
    def manifest(reference):
        require(e.sha(reference['manifest'])==reference['sha256'],'actual normal-build identity changed')
        return e.load(reference['manifest'])
    attempts=set();compile_ids=set();invocations=set();rows=[]
    def events(eid,code):
        observed={k:e.load('events/'+eid+'-'+k+'.json') for k in ['started','identified','launched','finished']}
        require(all(v['project']=='peco' and v['phase']=='final-archive' and v['id']==eid for v in observed.values()) and observed['started']['ci_run_id']==(run if host=='linux' else None),'normal-rebuild event project/phase/provider differs')
        end=observed['finished'];require(end['category']=='passed' and end['exit_code']==code and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'] and observed['launched']['pid']>0 and e.sha('peco/'+eid+'/console.log')==end['console_sha256'],'normal-rebuild actual process/cleanup/console differs')
        identity=manifest(observed['identified']['identity']);base=manifest(identity['base']) if 'base' in identity else identity
        require(all(base['files'].get(n)==h for n,h in helpers.items()),'normal-rebuild executed helper source differs')
        return identity,base
    path_type=PureWindowsPath if host=='windows' else PurePosixPath
    owned=path_type(owner['workspace'])/path_type(scope+'active/peco');modflag='-modfile='+str(owned/'build-inputs/pinned.mod')
    declared={f['id']:f for f in json.loads((package/'fault-declaration.json').read_text())['faults']}
    faults=e.load(complete['fault_summary']);require(e.sha(complete['fault_summary'])==complete['fault_summary_sha256'] and faults['normal_restoration_rebuilds']==3 and len(faults['faults'])==3,'normal compiled triple summary differs')
    contracts='peco/'+('host-contracts-rebuild-v1' if host=='windows' else 'host-contracts')+'/'
    spec=contracts+json.loads((package/'fault-declaration.json').read_text())['primary_spec'];spec_value=e.load(spec)
    for fault in faults['faults']:
        rule=declared[fault['id']];before=source[rule['path']]
        require(before.count(rule['before'].encode())==1 and hashlib.sha256(before.replace(rule['before'].encode(),rule['after'].encode())).hexdigest()==rule['mutated_source_sha256'],'actual held source mutation changed')
        require(fault['normal_rebuild_recovery_executed'] and fault['restored_exact'] and fault['original_sha256']==fault['restored_sha256']==primary[rule['path']],'normal source restoration missing')
        receipts={}
        for kind,key in [('mutated','compiled_receipt'),('restored','normal_rebuild_receipt')]:
            name=fault[key];receipt=e.load(name);require(e.sha(name)==fault[key+'_sha256'],'compiled source receipt changed')
            expected={scope+'active/peco/src/'+n:h for n,h in primary.items()}
            expected.update({scope+'active/peco/'+n:h for n,h in catalog['actual_native_compile_inputs'].items()})
            if kind=='mutated':expected[scope+'active/peco/src/'+rule['path']]=rule['mutated_source_sha256']
            expected[scope+'active/peco/'+build['binary_relative_path']]=build['binary_sha256']
            require(receipt['source_inputs']==expected and receipt['compiler_sha256']==build['compiler_sha256'] and receipt['compiler_tools']==build['compiler_tools'] and receipt['pristine_build_sha256']==e.sha(target+'build.json'),'actual compiled source/compiler binding differs')
            require(receipt['effective_go_mod_sha256']==primary['go.mod'] and receipt['effective_go_sum_sha256']==sha256(package/'build-checksums-v2.txt'),'effective module inputs changed')
            relative=e.logical(receipt['binary']).removeprefix('active/peco/');require(binaries.get(relative)==receipt['binary_sha256'],'actual compiler output image not retained')
            expected_command=[fetch['compiler'],'build',*review['build_flags'],modflag,'-o',str(path_type(owner['workspace'])/path_type(receipt['binary'])),review['main_package']]
            require(receipt['command']==expected_command,'normal/mutated compiler command differs from approved recipe')
            if kind=='restored':require(receipt['purpose']=='normal-restored-source-rebuild','saved image substituted for normal build')
            compile_id=receipt['compile_attempt'];require(compile_id not in compile_ids,'duplicate compiler execution');compile_ids.add(compile_id)
            identity,_=events(compile_id,0);actual=manifest(identity['target_catalog'])['files']
            expected_primary=dict(primary)
            if kind=='mutated':expected_primary[rule['path']]=rule['mutated_source_sha256']
            require({n.removeprefix(scope+'active/peco/src/'):h for n,h in actual.items() if n.startswith(scope+'active/peco/src/')}==expected_primary,'actual compiler prelaunch source differs')
            receipts[kind]=(name,receipt)
        require(len(fault['outcomes'])==3 and {o['phase'] for o in fault['outcomes']}=={'baseline','mutated','restored'},'partial rebuilt recovery triple')
        for outcome in fault['outcomes']:
            stage=outcome['phase'];mutated=stage=='mutated';report=e.load(outcome['report']);row=report['results'][0]
            require(e.sha(outcome['report'])==outcome['report_sha256'] and outcome['spec_sha256']==e.sha(spec) and report['runner_version']=='v0.4.0-rc.6' and report['os']==host,'actual rebuilt recovery report/spec differs')
            require(row['status']==('failed' if mutated else 'passed') and row.get('failure',{}).get('category')==(rule['category'] if mutated else None) and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'actual rebuilt recovery outcome/cleanup differs')
            require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations and outcome['attempt'] not in attempts,'duplicate/cross-invocation rebuilt recovery')
            invocations.add(row['invocation_id']);attempts.add(outcome['attempt'])
            require([s['action'] for s in row['steps']]==[next(iter(s)) for s in spec_value['steps']],'rebuilt recovery omitted actions')
            if not mutated:require(all(s['status']=='passed' for s in row['steps']) and row['target']['exit_code']==0,'normal recovered image did not pass full unchanged contract')
            for step in row['steps']:
                if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'],'cross-invocation recovered saved state')
            identity,base=events(outcome['attempt'],1 if mutated else 0)
            if stage in receipts:
                receipt_name,receipt=receipts[stage];actual=identity['native_source_fault']
                require(actual['build_receipt_sha256']==e.sha(receipt_name) and actual['actual_executable_sha256']==receipt['binary_sha256'] and actual['source_inputs']==receipt['source_inputs'] and outcome['actual_target_binary_sha256']==receipt['binary_sha256'],'recovery did not execute actual normally rebuilt image')
            require(base['files'].get(scope+spec)==e.sha(spec),'actual recovered spec launch changed')
            frame=None
            if mutated:
                frame=row['evidence']['screen_path'];require(e.data(frame) and len(e.data(frame))<1024**2,'actual new mutation frame missing')
                if fault['id']=='F03':
                    first=next(i for i,s in enumerate(row['steps']) if s['status']=='failed')
                    require(row['steps'][first]['action']=='state' and spec_value['steps'][first]['state']['path']=='selected.txt' and all(s['status']=='passed' for s in row['steps'][:first]) and {'expect','snapshot','exit'}<=set(s['action'] for s in row['steps'][:first]),'earlier failure substituted for saved corruption')
            rows.append(dict(fault=fault['id'],phase=stage,attempt=outcome['attempt'],invocation=row['invocation_id'],report_sha256=outcome['report_sha256'],actual_binary_sha256=outcome['actual_target_binary_sha256'],frame=frame,frame_sha256=e.sha(frame) if frame else None))
    require(len(rows)==len(invocations)==len(attempts)==9 and len(compile_ids)==6,'normal rebuilt recovery count differs')
    removed=target.startswith('peco/retained-source-rebuild-v1/')
    if removed:
        proof=e.load(target+'removed.json');inventory=e.load(target+'cleanup-inventory.json')
        require(proof['removed'] and proof['cleanup_inventory_sha256']==e.sha(target+'cleanup-inventory.json') and inventory['source_restored_exact'] and inventory['actual_reports_with_confirmed_cleanup']>=9,'normal rebuild source/runtime removal incomplete')
    return dict(schema_version=1,project='peco',host=host,source_revision=revision,run=run,generation=generation,normal_rebuilds_verified=3,actual_compiler_executions_verified=6,calibrations_verified=9,
        declaration_sha256=sha256(declaration_path),summary_sha256=e.sha('peco/rebuild-recovery-summary-v1.json'),actual_normal_rebuilt_images=complete['actual_rebuilt_images'],actual_phases=rows,
        source_runtime_removed=removed,original_ordinary_matrix_unchanged=True,ordinary_credit=0,project_admissions=0)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('host',choices=['windows','linux']);parser.add_argument('--revision',required=True);parser.add_argument('--run');parser.add_argument('--generation',type=int);args=parser.parse_args()
    result=audit(args.host,args.revision,args.run,args.generation)
    immutable_json(DOC/'peco'/(args.host+'-normal-rebuild-readback'+('-removed' if result['source_runtime_removed'] else '-before-cleanup')+'.json'),result)
    print('Verified9fresh phases,6actual compiler runs and3normal rebuilt recovery images on',args.host,'; removed:',result['source_runtime_removed'])


if __name__=='__main__':main()
