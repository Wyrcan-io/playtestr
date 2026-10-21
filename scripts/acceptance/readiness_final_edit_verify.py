"""Audit exact runner archives, actual rebuilt Edit faults and native cleanup."""
import argparse
from pathlib import Path

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require, verify_batches
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'],required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json');host=args.host
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2
        and all(j['status']=='completed' and j['conclusion']=='success' for j in metadata['jobs']),'incomplete native jobs')
    packet=parent/('final-edit-'+('Linux' if host=='linux' else 'Windows'));target=packet/'edit'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/edit';profile=docs/'final-native-profiles'/host
    candidate=load(docs.parent/'migration-candidate-freeze.json');cell=next(c for c in candidate['cells'] if c['host']==host)
    installed=load(packet/'private-install/migration-v2'/(host+'-amd64')/'installation.json')
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256']
        and installed['source_revision']==candidate['source_revision'],'different native private archive')
    review=load(docs/'source-review.json');retained=target/'retained-source';build=load(retained/'build.json');runtime=load(retained/'runtime.json')
    canonical=RAW/'edit/retained-source';original_index=load(canonical/'verified-index.json')
    require(sha256(canonical/'source.tar.gz')==original_index['archive_sha256']==review['archive_sha256'],'canonical original source differs')
    source={n:r['sha256'] for n,r in original_index['files'].items()}
    triple='x86_64-'+('unknown-linux-gnu' if host=='linux' else 'pc-windows-msvc')
    require(build['pin']==review['pin'] and build['native_triple']==runtime['native_triple']==triple
        and build['stable_build'] and not build['bootstrap'] and build['languages']=='en'
        and build['lock_sha256']==source['Cargo.lock'] and build['license_sha256']==review['license_sha256']==source['LICENSE']
        and build['dependencies_sha256']==sha256(retained/'dependencies.json') and build['review_sha256']==sha256(retained/'build-review.json'),
        'different actual locked native release build')
    index=load(retained/'verified-index.json')
    require(index['archive_sha256']==review['archive_sha256'] and {n:r['sha256'] for n,r in index['files'].items()}==source,
        'different retained native source catalog')
    prefix='artifacts/runner-readiness-ten-project-pass/active/edit/';target_key=prefix+build['binary_relative_path']
    selected={n:d for n,d in source.items() if Path(n).suffix in {'.rs','.toml','.lock','.rc','.manifest'} or Path(n).name=='LICENSE'}
    ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts()
    def witness(identity,expected=0,source_override=None,compiled=None,public=False,alias=False):
        event=events[identity];end=event['finished']
        require(all(e['phase']=='final-archive' for e in event.values()) and 'launched' in event,'missing final-phase launch')
        require(event['started']['expected_exit']==expected and end['category']=='passed' and end['exit_code']==expected
            and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'actual command outcome/cleanup differs')
        require(sha256(packet/event['started']['project']/identity/'console.log')==end['console_sha256'],'changed actual output')
        manifest=load_manifest(packet,event['identified']['identity']);files=manifest['files'];expected_source=dict(selected)
        if source_override:expected_source[source_override[0]]=source_override[1]
        observed={n[len(prefix+'src/'):]:d for n,d in files.items() if n.startswith(prefix+'src/')}
        require(all(observed.get(n)==d for n,d in expected_source.items())
            and all(n in source and d==source[n] for n,d in observed.items() if n not in expected_source),'actual Rust/resource source differs')
        for name in ['rustc','cargo']:require(manifest['runtime_executables'][name]==runtime[name+'_sha256'],'actual Rust compiler/tool differs')
        for name,digest in runtime['read_only_installed_prerequisites'].items():
            require(manifest['runtime_executables'][Path(name.replace('\\','/')).name]==digest,'actual native prerequisite differs')
        require(files[prefix+'dependencies.json']==build['dependencies_sha256'],'actual dependency inventory differs')
        if compiled is None and public:compiled=build['binary_sha256']
        if compiled:require(files[target_key]==compiled,'actual compiled target executable differs')
        if public:
            runner_key=prefix.replace('active/edit/','bin/playtestr'+('.exe' if host=='windows' else '')) if alias else installed['binary']
            require(files[runner_key]==cell['binary_sha256'],'actual exact runner archive differs')
        return files
    witness(build['build_attempt']);witness(build['version_attempt'],compiled=build['binary_sha256'])
    frozen=load(profile/'reviewed-contract-freeze.json');declaration=load(docs/'final-series-declaration.json')
    for name,indices in declaration['segmented_text_steps_by_host'][host].items():
        original=load(profile/'contracts'/name)
        derived=[i for i,s in enumerate(original['steps'],1) if set(s)=={'text'} and len(s['text'])>1
            and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
        require(indices==derived,'segmentation exceeds reviewed printable insertion fields')
    rows,commands,result_ok,bind_inputs=verify_batches(packet,docs,profile,host,candidate,cell,installed,build,events,witness)
    summaries=list((target/'faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
    summary=load(summaries[0]);root=summaries[0].parent
    require(summary['runner_sha256']==cell['binary_sha256'] and len(summary['faults'])==3
        and {f['id'] for f in summary['faults']}=={'F01','F02','F03'},'incomplete source fault set')
    calibration=[];rebuilds=[];expected_baseline=build['binary_sha256']
    require([f['id'] for f in summary['faults']]==['F01','F02','F03'],'actual fault order differs')
    for receipt in summary['faults']:
        original=load(docs/'original-source-faults'/(receipt['id']+'-receipt.json'))
        require(not receipt['held_out'] and receipt['restored_exact'] and all(receipt[k]==original[k]
            for k in ['id','path','before','after','spec','category','mutated_source_sha256','original_source_sha256'])
            and receipt['original_source_sha256']==source[receipt['path']],'reviewed actual source mutation differs')
        require((root/(receipt['id']+'.patch')).read_bytes()==(docs/'original-source-faults'/(receipt['id']+'.patch')).read_bytes(),'actual reviewed patch differs')
        mutated=receipt['mutation_build'];restored=receipt['restored_build']
        require(receipt['baseline_binary_sha256']==expected_baseline and mutated['binary_sha256']!=receipt['baseline_binary_sha256'],
            'mutation/baseline executable chain differs')
        for key,override in [('mutation_build',(receipt['path'],receipt['mutated_source_sha256'])),('restored_build',None)]:
            validation=receipt[key];witness(validation['attempt'],source_override=override)
            label=receipt['id'].lower()+('-mutated' if key=='mutation_build' else '-restored')
            paths=list((retained/'build-revisions').glob(label+'-*.json'));require(len(paths)==1,'ambiguous actual build revision')
            revision=load(paths[0]);code=7 if receipt['id']=='F02' and key=='mutation_build' else 0
            require(revision['binary_sha256']==validation['binary_sha256'] and revision['pin']==build['pin']
                and revision['native_triple']==triple and revision['stable_build'] and not revision['bootstrap']
                and revision['languages']==build['languages'] and revision['dependencies_sha256']==build['dependencies_sha256']
                and revision['review_sha256']==build['review_sha256'] and revision['lock_sha256']==build['lock_sha256']
                and revision['resource_compiler']==build['resource_compiler']
                and revision['version_exit_code']==code,'actual rebuilt release provenance differs')
            witness(revision['build_attempt'],source_override=override)
            witness(revision['version_attempt'],code,override,revision['binary_sha256'])
        for phase,code,digest,compiled,key in [('baseline',0,receipt['original_source_sha256'],receipt['baseline_binary_sha256'],'baseline_attempt'),
            ('mutated',1,receipt['mutated_source_sha256'],mutated['binary_sha256'],'mutation_attempt'),
            ('restored',0,receipt['original_source_sha256'],restored['binary_sha256'],'restored_attempt')]:
            identity=receipt[key];require(identity not in commands,'reused calibration command');commands.add(identity)
            files=witness(identity,code,(receipt['path'],digest),compiled,True,True)
            package=target/'host-contracts';contract=load(package/receipt['spec'])
            bind_inputs(files,package,contract,receipt['spec'],frozen['all_package_inputs'])
            path=root/(receipt['id']+'-'+phase+'.json');value=load(path);row=value['results'][0]
            require(value['runner_version']==candidate['version'] and row['spec_version']==3
                and Path(row['spec_path'].replace('\\','/')).name==receipt['spec'],'actual calibration version/spec differs')
            result_ok(row,'failed' if code else 'passed')
            if code:
                require(row['failure']['category']==receipt['category'],'wrong actual mutant diagnosis')
                if receipt['id']=='F03':
                    failed=next(i for i,s in enumerate(row['steps']) if s['status']=='failed');prior=row['steps'][:failed]
                    require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
                        and row['steps'][failed]['state']['kind']=='file' and row['target']['exit_code']==0,
                        'missing actual success-screen/exit false-green rejection')
            calibration.append(dict(fault=receipt['id'],phase=phase,command=identity,invocation_id=row['invocation_id'],report_sha256=sha256(path)))
        rebuilds.append(dict(fault=receipt['id'],baseline_binary_sha256=receipt['baseline_binary_sha256'],
            restored_binary_sha256=restored['binary_sha256'],byte_identical=receipt['baseline_binary_sha256']==restored['binary_sha256']))
        expected_baseline=restored['binary_sha256']
    removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/edit' and removed['source_archive_sha256']==review['archive_sha256']
        and prepared['runtime_processes_verified'],'unconfirmed target/runtime removal')
    for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'source selected restore changed')
    immutable_json(docs/('final-verified-'+host+'.json'),dict(run=args.run,host=host,ordinary_executions=240,calibration_executions=9,
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],target_pin=build['pin'],observations=rows,
        calibration_observations=calibration,target_rebuild_observations=rebuilds,source_fault_summary_sha256=sha256(summaries[0]),
        cleanup_receipt_sha256=sha256(retained/'removed.json'),final_archive_credit=0,
        scope='Exact frozen Playtestr archive/native twelve-by-twenty Edit profile; actual Rust/Cargo/native prerequisite identities, three normally rebuilt source/resource faults and exact pinned source restoration. Every rebuilt executable is independently identified and exercised; target binary byte reproducibility is not assumed. Overall final matrix gates remain separate.'))
    print('Independently verified final Edit ordinary and rebuilt-fault series:',host)


if __name__=='__main__':main()
