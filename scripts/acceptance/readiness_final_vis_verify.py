"""Audit exact Vis archive series, normal C rebuilds and native cleanup."""
import argparse
from pathlib import Path

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require, verify_batches
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','macos'],required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    host=args.host;parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2
        and all(j['status']=='completed' and j['conclusion']=='success' for j in metadata['jobs']),'incomplete native jobs')
    packet=parent/('final-vis-'+('Linux' if host=='linux' else 'macOS'));target=packet/'vis'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/vis';profile=docs/'final-native-profiles'/host
    candidate=load(docs.parent/'migration-candidate-freeze.json');cell=next(c for c in candidate['cells'] if c['host']==('linux' if host=='linux' else 'darwin'))
    installed=load(packet/'private-install/migration-v2'/('linux-amd64' if host=='linux' else 'darwin-arm64')/'installation.json')
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256']
        and installed['source_revision']==candidate['source_revision'],'different native private archive')
    review=load(docs/'source-review.json');retained=target/'retained-source';build=load(retained/'build.json');runtime=load(retained/'runtime.json')
    canonical=load(RAW/'vis/retained-source/verified-index.json');index=load(retained/'verified-index.json')
    source={n:r['sha256'] for n,r in canonical['files'].items()}
    require(index['archive_sha256']==canonical['archive_sha256']==review['archive_sha256']
        and {n:r['sha256'] for n,r in index['files'].items()}==source,'different full retained source catalog')
    require(build['pin']==review['pin'] and build['archive_sha256']==review['archive_sha256']
        and build['license_sha256']==source['LICENSE']==review['license_sha256']
        and build['version_exit_code']==0 and build['binary_relative_path']=='src/vis'
        and all(build[n+'_sha256']==runtime[n+'_sha256'] for n in ['compiler','make']),'different native C build')
    prefix='artifacts/runner-readiness-ten-project-pass/active/vis/';target_key=prefix+'src/vis'
    selected={n:d for n,d in source.items() if Path(n).suffix in {'.c','.h','.inc','.mk'} or Path(n).name in {'configure','Makefile','LICENSE'}}
    selected.update({'config.mk':build['config_mk_sha256'],'config.h':build['config_h_sha256']})
    ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts()
    def witness(identity,expected=0,source_override=None,compiled=None,public=False,alias=False,generated_header=True):
        event=events[identity];end=event['finished']
        require(all(e['phase']=='final-archive' for e in event.values()) and 'launched' in event,'missing final-phase launch')
        require(event['started']['expected_exit']==expected and end['category']=='passed' and end['exit_code']==expected
            and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'actual command outcome/cleanup differs')
        require(sha256(packet/event['started']['project']/identity/'console.log')==end['console_sha256'],'changed actual output')
        manifest=load_manifest(packet,event['identified']['identity']);files=manifest['files'];expected_source=dict(selected)
        if not generated_header:expected_source.pop('config.h')
        if source_override:expected_source[source_override[0]]=source_override[1]
        observed={n[len(prefix+'src/'):]:d for n,d in files.items() if n.startswith(prefix+'src/') and n!=target_key}
        require(observed==expected_source,'actual complete C/header/configuration input map differs')
        for name in ['compiler','make']:require(manifest['runtime_executables'][name]==runtime[name+'_sha256'],'actual installed build tool differs')
        if compiled is None and public:compiled=build['binary_sha256']
        if compiled:require(files[target_key]==compiled,'actual compiled target differs')
        if public:require(files[prefix.replace('active/vis/','bin/playtestr') if alias else installed['binary']]==cell['binary_sha256'],'actual exact runner archive differs')
        return files
    witness(build['build_attempt'],generated_header=False);witness(build['version_attempt'],compiled=build['binary_sha256'])
    declaration=load(docs/'final-series-declaration.json');frozen=load(profile/'reviewed-contract-freeze.json')
    for name,indices in declaration['segmented_text_steps_by_host'][host].items():
        original=load(profile/'contracts'/name)
        derived=[i for i,s in enumerate(original['steps'],1) if set(s)=={'text'} and len(s['text'])>1
            and all(ord(c)>=32 and ord(c)!=127 for c in s['text']) and i>1 and original['steps'][i-2].get('expect')=='INSERT']
        require(indices==derived,'segmentation exceeds reviewed insertion fields')
    rows,commands,result_ok,bind_inputs=verify_batches(packet,docs,profile,host,candidate,cell,installed,build,events,witness)
    summaries=list((target/'faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
    summary=load(summaries[0]);root=summaries[0].parent
    require(summary['runner_sha256']==cell['binary_sha256'] and [f['id'] for f in summary['faults']]==['F01','F02','F03'],'incomplete actual source fault set')
    calibration=[];rebuilds=[];baseline=build['binary_sha256']
    for receipt in summary['faults']:
        original=load(docs/'original-source-faults'/(receipt['id']+'-receipt.json'))
        require(not receipt['held_out'] and receipt['restored_exact'] and all(receipt[k]==original[k]
            for k in ['id','path','before','after','spec','category','mutated_source_sha256','original_source_sha256'])
            and receipt['original_source_sha256']==source[receipt['path']],'reviewed actual source mutation differs')
        require((root/(receipt['id']+'.patch')).read_bytes()==(docs/'original-source-faults'/(receipt['id']+'.patch')).read_bytes(),'reviewed source patch differs')
        mutated=receipt['mutation_build'];restored=receipt['restored_build']
        require(receipt['baseline_binary_sha256']==baseline and mutated['binary_sha256']!=baseline,'actual executable chain differs')
        for key,override in [('mutation_build',(receipt['path'],receipt['mutated_source_sha256'])),('restored_build',None)]:
            validation=receipt[key];witness(validation['attempt'],source_override=override)
            label=receipt['id'].lower()+('-mutated' if key=='mutation_build' else '-restored')
            paths=list((retained/'build-revisions').glob(label+'-*.json'));require(len(paths)==1,'ambiguous rebuilt revision')
            revision=load(paths[0])
            require(revision['binary_sha256']==validation['binary_sha256'] and revision['version_exit_code']==0
                and all(revision[k]==build[k] for k in ['pin','archive_sha256','compiler_sha256','make_sha256','config_mk_sha256','config_h_sha256','license_sha256','features','build_command']),
                'actual ordinary C rebuild provenance differs')
            witness(revision['build_attempt'],source_override=override)
            witness(revision['version_attempt'],source_override=override,compiled=revision['binary_sha256'])
        for phase,code,digest,compiled,key in [('baseline',0,receipt['original_source_sha256'],baseline,'baseline_attempt'),
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
                        and row['steps'][failed]['state']['kind']=='file' and row['target']['exit_code']==0,'missing actual success-screen/exit false-green rejection')
            calibration.append(dict(fault=receipt['id'],phase=phase,command=identity,invocation_id=row['invocation_id'],report_sha256=sha256(path)))
        rebuilds.append(dict(fault=receipt['id'],baseline_binary_sha256=baseline,restored_binary_sha256=restored['binary_sha256'],byte_identical=baseline==restored['binary_sha256']))
        baseline=restored['binary_sha256']
    removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/vis' and removed['source_archive_sha256']==review['archive_sha256']
        and prepared['runtime_processes_verified'],'unconfirmed native runtime removal')
    for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'selected source restore changed')
    immutable_json(docs/('final-verified-'+host+'.json'),dict(run=args.run,host=host,ordinary_executions=240,calibration_executions=9,
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],target_pin=build['pin'],observations=rows,
        calibration_observations=calibration,target_rebuild_observations=rebuilds,source_fault_summary_sha256=sha256(summaries[0]),
        cleanup_receipt_sha256=sha256(retained/'removed.json'),final_archive_credit=0,
        scope='Exact frozen archive and reviewed native Vis twelve-by-twenty profile; complete C/header/configuration input identities, actual installed compiler/make, ordinary rebuilt source faults and exact restoration/runtime removal. Global final matrix gates remain separate.'))
    print('Independently verified final Vis ordinary and rebuilt-fault series:',host)


if __name__=='__main__':main()
