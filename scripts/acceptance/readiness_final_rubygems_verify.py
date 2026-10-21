"""Audit final native Bundler archive runs and actual Ruby/ERB source faults."""
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
    packet=parent/('final-rubygems-'+('Linux' if host=='linux' else 'Windows'));target=packet/'rubygems'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rubygems';profile=docs/'final-native-profiles'/host
    candidate=load(docs.parent/'migration-candidate-freeze.json');cell=next(c for c in candidate['cells'] if c['host']==host)
    installed=load(packet/'private-install/migration-v2'/(host+'-amd64')/'installation.json')
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256']
        and installed['source_revision']==candidate['source_revision'],'different native private archive')
    review=load(docs/'source-review.json');retained=target/'retained-source';build=load(retained/'build.json');runtime=load(retained/'runtime.json')
    canonical=RAW/'rubygems/retained-source';original_index=load(canonical/'verified-index.json')
    require(sha256(canonical/'source.tar.gz')==original_index['archive_sha256']==review['archive_sha256'],'canonical original source differs')
    source={n:r['sha256'] for n,r in original_index['files'].items()}
    require(build['pin']==review['pin'] and build['source_runtime_interpreted'] and not build['build_hooks_executed']
        and not build['dependency_installation'] and build['license_sha256']==review['license_sha256']==source['MIT.txt']
        and build['runtime_sha256']==sha256(retained/'runtime.json') and review['bundler_version'] in build['bundled_cli_version'],
        'wrong actual interpreted target build')
    if host=='linux':require(runtime['installed_ruby_executable']=='/usr/bin/ruby3.2','different declared installed native Ruby')
    else:require(runtime['archive_sha256']==review['portable_runtime_archive_sha256'] and not runtime['installed_globally'],
        'different owned Windows Ruby archive')
    index=load(retained/'verified-index.json')
    require(index['archive_sha256']==review['archive_sha256'] and {n:r['sha256'] for n,r in index['files'].items()}==source,
        'different retained native source catalog')
    prefix='artifacts/runner-readiness-ten-project-pass/active/rubygems/'
    selected={n:d for n,d in source.items() if n.startswith('lib/') or n.startswith('exe/') or n=='bundler.gemspec'}
    ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts();manifests={}
    def witness(identity,expected=0,source_override=None,public=False,alias=False,runtime_required=True):
        event=events[identity];end=event['finished']
        require(all(e['phase']=='final-archive' for e in event.values()) and 'launched' in event,'missing final-phase launch')
        require(event['started']['expected_exit']==expected and end['category']=='passed' and end['exit_code']==expected
            and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'actual command outcome/cleanup differs')
        require(sha256(packet/event['started']['project']/identity/'console.log')==end['console_sha256'],'changed actual output')
        manifest=load_manifest(packet,event['identified']['identity']);files=manifest['files'];expected_source=dict(selected)
        manifests[identity]=manifest
        if source_override:expected_source['lib/'+source_override[0]]=source_override[1]
        observed={n[len(prefix+'src/'):]:d for n,d in files.items() if n.startswith(prefix+'src/')}
        require(all(observed.get(n)==d for n,d in expected_source.items())
            and all(n in source and d==source[n] for n,d in observed.items() if n not in expected_source),'actual Ruby/ERB source differs')
        if runtime_required:
            require(manifest['runtime_executables']['ruby']==runtime['ruby_sha256'],'actual Ruby executable differs')
            if host=='windows':require(files[prefix+runtime['ruby_relative_path']]==runtime['ruby_sha256'],'actual owned Windows Ruby differs')
        if public:
            runner_key=prefix.replace('active/rubygems/','bin/playtestr'+('.exe' if host=='windows' else '')) if alias else installed['binary']
            require(files[runner_key]==cell['binary_sha256'],'actual exact archive differs')
        return files
    witness(build['version_attempt'],runtime_required=False)
    frozen=load(profile/'reviewed-contract-freeze.json');declaration=load(docs/'final-series-declaration.json')
    for name,indices in declaration['segmented_text_steps_by_host'][host].items():
        original=load(profile/'contracts'/name)
        derived=[i for i,s in enumerate(original['steps'],1) if set(s)=={'text'} and len(s['text'])>1
            and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
        require(indices==derived,'segmentation exceeds reviewed printable responses')
    rows,commands,result_ok,bind_inputs=verify_batches(packet,docs,profile,host,candidate,cell,installed,build,events,witness)
    for batch in declaration['batches']:
        for relative in frozen['empty_directories']:
            folder=target/'final-series'/str(batch['number'])/batch['package_directory']/relative
            # Empty directories are absent from downloaded Actions artifacts;
            # require the actual prelaunch directory and exact fixture file set.
            observed=load(target/'final-series'/str(batch['number'])/'normal-build-gem.json.observed.json')
            key='artifacts/runner-readiness-ten-project-pass/'+folder.relative_to(packet).as_posix()
            require(key in manifests[observed['attempt']]['fixture_directories'],'reviewed empty fixture precondition absent before launch')
            require(not any(n.startswith(key+'/') for n in manifests[observed['attempt']]['files']),
                'reviewed empty fixture contained files before launch')
    summaries=list((target/'faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
    summary=load(summaries[0]);root=summaries[0].parent
    require(summary['runner_sha256']==cell['binary_sha256'] and len(summary['faults'])==3
        and {f['id'] for f in summary['faults']}=={'F01','F02','F03'},'incomplete source fault set')
    calibration=[]
    for receipt in summary['faults']:
        original=load(docs/'faults'/(receipt['id']+'-receipt.json'))
        require(not receipt['held_out'] and receipt['restored_exact'] and all(receipt[k]==original[k]
            for k in ['id','path','before','after','spec','mutated_source_sha256','original_source_sha256'])
            and receipt['original_source_sha256']==source['lib/'+receipt['path']],'reviewed real source mutation differs')
        require((root/(receipt['id']+'.patch')).read_text(encoding='utf-8')==(docs/'faults'/(receipt['id']+'.patch')).read_text(encoding='utf-8'),
            'actual reviewed patch differs')
        for phase,code,digest,key in [('baseline',0,receipt['original_source_sha256'],'baseline_attempt'),
            ('mutated',1,receipt['mutated_source_sha256'],'mutation_attempt'),('restored',0,receipt['original_source_sha256'],'restored_attempt')]:
            identity=receipt[key];require(identity not in commands,'reused calibration command');commands.add(identity)
            files=witness(identity,code,(receipt['path'],digest),public=True,alias=True)
            package=target/'host-contracts';contract=load(package/receipt['spec'])
            bind_inputs(files,package,contract,receipt['spec'],frozen['all_package_inputs'])
            path=root/(receipt['id']+'-'+phase+'.json');value=load(path);row=value['results'][0]
            require(value['runner_version']==candidate['version'] and row['spec_version']==3
                and Path(row['spec_path'].replace('\\','/')).name==receipt['spec'],'actual calibration version/spec differs')
            result_ok(row,'failed' if code else 'passed')
            if code:
                if receipt['id']=='F02':require(row['failure']['category']=='unexpected_exit' and row['target']['exit_code']==0,
                    'wrong actual native build-error exit mutation')
                if receipt['id']=='F03':
                    failed=next(i for i,s in enumerate(row['steps']) if s['status']=='failed');prior=row['steps'][:failed]
                    require(row['failure']['category']=='state_assertion_failure' and all(s['status']=='passed' for s in prior)
                        and {'snapshot','exit'}<={s['action'] for s in prior} and row['steps'][failed]['state']['kind']=='file'
                        and row['target']['exited'] and row['target']['exit_code']==0,'missing actual success-screen/exit false-green rejection')
            calibration.append(dict(fault=receipt['id'],phase=phase,command=identity,invocation_id=row['invocation_id'],report_sha256=sha256(path)))
    removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/rubygems' and removed['source_archive_sha256']==review['archive_sha256']
        and prepared['runtime_processes_verified'],'unconfirmed target/runtime removal')
    for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'source selected restore changed')
    immutable_json(docs/('final-verified-'+host+'.json'),dict(run=args.run,host=host,ordinary_executions=240,calibration_executions=9,
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],target_pin=build['pin'],observations=rows,
        calibration_observations=calibration,source_fault_summary_sha256=sha256(summaries[0]),cleanup_receipt_sha256=sha256(retained/'removed.json'),
        final_archive_credit=0,scope='Exact final archive/native twelve-by-twenty Bundler profile, reviewed complete artifact and state oracles, fresh actual Ruby/source/catalog identities, three real Ruby/ERB source faults and checked exact restoration/removal. Overall final matrix gates remain separate.'))
    print('Independently verified final Bundler ordinary and fault series:',host)


if __name__=='__main__':main()
