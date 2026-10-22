"""Audit final native Frogmouth/Papis runs and actual editable Python faults."""
import argparse
import hashlib
import json
from pathlib import Path

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require, verify_batches
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import packet_file, read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['frogmouth','papis'],required=True)
    parser.add_argument('--run',required=True);parser.add_argument('--host',choices=['linux','windows'],required=True);args=parser.parse_args()
    project=args.project;host=args.host;require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2
        and all(j['status']=='completed' and j['conclusion']=='success' for j in metadata['jobs']),'incomplete native jobs')
    packet=parent/('final-'+project+'-'+('Linux' if host=='linux' else 'Windows'));target=packet/project
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'/project
    profile=docs if host=='linux' else docs/'native-profiles/windows'
    candidate=load(docs.parent/'migration-candidate-freeze.json');cell=next(c for c in candidate['cells'] if c['host']==host)
    installed=load(packet/'private-install/migration-v2'/(host+'-amd64')/'installation.json')
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256']
        and installed['source_revision']==candidate['source_revision'],'different native private archive')
    review=load(docs/'source-review.json');retained=target/'retained-source';build=load(retained/'build.json');runtime=load(retained/'runtime.json')
    require(build['pin']==runtime['source_pin']==review['pin'] and build['source_editable']
        and build['license_sha256']==review['reviewed_inputs']['LICENSE'],'wrong actual editable target build')
    index=load(retained/'verified-index.json')
    canonical=load(RAW/project/'retained-source/verified-index.json')
    full_source={n:r['sha256'] for n,r in index['files'].items()}
    require(index['archive_sha256']==canonical['archive_sha256']==review['archive_sha256']
        and full_source=={n:r['sha256'] for n,r in canonical['files'].items()}
        and all(full_source.get(n)==d for n,d in review['reviewed_inputs'].items()),'different retained native source catalog')
    wheel_sha=hashlib.sha256((json.dumps(build['dependency_wheels'],sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()).hexdigest()
    require(sha256(retained/build['wheel_manifest'])==wheel_sha,'retained actual dependency wheel inventory differs')
    prefix='artifacts/runner-readiness-ten-project-pass/active/'+project+'/'
    python_key=prefix+'venv/'+('Scripts/python.exe' if host=='windows' else 'bin/python')
    launcher_key=prefix+build['launcher_relative_path']
    selected={n:d for n,d in full_source.items() if n=='pyproject.toml'
        or n.startswith(project+'/') and n.endswith('.py')}
    ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts();manifests={}
    def witness(identity,expected=0,source_override=None,public=False,runtime_required=True):
        event=events[identity];end=event['finished']
        require(all(e['phase']=='final-archive' for e in event.values()) and 'launched' in event,'missing final-phase launch')
        require(event['started']['expected_exit']==expected and end['category']=='passed' and end['exit_code']==expected
            and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'actual command outcome/cleanup differs')
        require(sha256(packet/event['started']['project']/identity/'console.log')==end['console_sha256'],'changed actual output')
        manifest=load_manifest(packet,event['identified']['identity']);manifests[identity]=manifest
        files=manifest['files'];expected_source=dict(selected)
        if source_override:expected_source[source_override[0]]=source_override[1]
        observed={n[len(prefix+'src/'):]:d for n,d in files.items() if n.startswith(prefix+'src/')}
        require(all(observed.get(n)==d for n,d in expected_source.items())
            and all(n in full_source and d==full_source[n]
                for n,d in observed.items() if n not in expected_source),'actual editable Python source differs')
        require(files[python_key]==runtime['python_sha256'] and files[prefix+build['wheel_manifest']]==wheel_sha,
            'actual owned interpreter/dependency inventory differs')
        if runtime_required:
            require(manifest['runtime_executables']['python']==runtime['python_sha256']
                and files[launcher_key]==build['launcher_sha256'],'actual interpreter/launcher differs')
        if public:require(files[installed['binary']]==cell['binary_sha256'],'actual exact runner archive differs')
        return files
    witness(build['version_attempt'],runtime_required=False)
    frozen=load(profile/'reviewed-contract-freeze.json')
    declaration_file='final-series-declaration-v2.json' if project=='frogmouth' else 'final-series-declaration.json'
    declaration=load(docs/declaration_file)
    require(declaration['helper_runtime_policy'].startswith('Target-only setup --no-path-export'),'unqualified helper interpreter profile')
    for name,indices in declaration['segmented_text_steps_by_host'][host].items():
        original=load(profile/'contracts'/name)
        derived=[i for i,s in enumerate(original['steps'],1) if set(s)=={'text'} and len(s['text'])>1
            and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
        require(indices==derived,'segmentation exceeds reviewed printable fields')
    rows,commands,result_ok,bind_inputs=verify_batches(packet,docs,profile,host,candidate,cell,installed,build,events,witness,
        declaration_file=declaration_file)
    if project=='papis':
        planned=load(docs/'scenario-declaration-revision-3.json')['host_profiles'][host]
        for batch in declaration['batches']:
            folder=target/'final-series'/str(batch['number']);current=folder/batch['package_directory']
            for case in planned:
                for relative in case['dirs']:
                    name=case['id']+'.json';observed=load(folder/(name+'.observed.json'))
                    key='artifacts/runner-readiness-ten-project-pass/'+(current/'fixtures'/case['id']/relative).relative_to(packet).as_posix()
                    require(key in manifests[observed['attempt']]['fixture_directories'],'declared fixture directory absent before launch')
    selection=load(docs/'fault-selection-revision-2.json');source_faults={r['id']:r for r in load(docs/'source-fault-review-revision-2.json')['faults']}
    require(declaration['fault_selection']['selection_sha256']==sha256(docs/'fault-selection-revision-2.json')
        and declaration['fault_selection']['review_sha256']==sha256(docs/'source-fault-review-revision-2.json'),'declared fault selection changed')
    summaries=list((target/'faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous actual source fault batch')
    summary=load(summaries[0]);root=summaries[0].parent;ids=declaration['fault_selection']['ids']
    require([r['id'] for r in summary['faults']]==ids and summary['runner_sha256']==cell['binary_sha256']
        and summary['interpreter_sha256']==runtime['python_sha256'],'actual source fault coverage/identity differs')
    selected_receipt=load(root/'selected-faults.json')
    require(not selected_receipt['original_heldout'] and selected_receipt['selection_revision']==2
        and selected_receipt['frozen_contract_sha256']==sha256(docs/'reviewed-contract-freeze.json')
        and selected_receipt['native_freeze_sha256']==sha256(profile/'reviewed-contract-freeze.json'),'fault freeze/holdout accounting differs')
    calibration=[]
    for receipt in summary['faults']:
        original=next(f for f in selection['faults'] if f['id']==receipt['id']);reviewed=source_faults[receipt['id']]
        require(not receipt['held_out'] and receipt['restored_exact']
            and all(receipt[k]==original[k] for k in ['id','path','spec','before','after','category'])
            and all(receipt[k]==reviewed[k] for k in ['path','mutated_source_sha256','original_source_sha256'])
            and receipt['original_source_sha256']==full_source[receipt['path']],'reviewed actual source fault differs')
        for key,digest in [('mutation_validation',receipt['mutated_source_sha256']),('restored_validation',receipt['original_source_sha256'])]:
            validation=receipt[key]
            require(validation['source_sha256']==digest and validation['interpreter_sha256']==runtime['python_sha256'],'source syntax/version identity differs')
            for event in [validation['syntax_attempt'],validation['version_attempt']]:witness(event,source_override=(receipt['path'],digest))
        for phase,code,digest,key in [('baseline',0,receipt['original_source_sha256'],'baseline_attempt'),
            ('mutated',1,receipt['mutated_source_sha256'],'mutation_attempt'),('restored',0,receipt['original_source_sha256'],'restored_attempt')]:
            identity=receipt[key];require(identity not in commands,'reused calibration command');commands.add(identity)
            files=witness(identity,code,(receipt['path'],digest),public=True)
            package=target/'host-contracts';contract=load(package/receipt['spec'])
            bind_inputs(files,package,contract,receipt['spec'],frozen['all_package_inputs'])
            path=root/(receipt['id']+'-'+phase+'.json');value=load(path);row=value['results'][0]
            require(value['runner_version']==candidate['version'] and row['spec_version']==3
                and Path(row['spec_path'].replace('\\','/')).name==receipt['spec'],'actual calibration version/spec differs')
            result_ok(row,'failed' if code else 'passed')
            if code:
                require(row['failure']['category']==receipt['category'],'wrong actual mutant diagnosis')
                if receipt['category']=='state_assertion_failure':
                    failed=next(i for i,s in enumerate(row['steps']) if s['status']=='failed');prior=row['steps'][:failed];state=row['steps'][failed]['state']
                    require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
                        and row['target']['exited'] and row['target']['exit_code']==0,'missing actual success-screen/exit false-green rejection')
                    wanted=('file','beta.md') if project=='frogmouth' else (
                        ('file','exported/info.yaml') if receipt['id']=='F03' else ('entries','exported'))
                    require((state['kind'],state['path'])==wanted,'wrong saved-state rejection')
                    if project=='frogmouth':
                        reference=row['evidence']['screen_path'].replace('\\','/');prefix_path='artifacts/runner-readiness-ten-project-pass/'
                        require(reference.startswith(prefix_path),'unsafe final screen reference')
                        screen=packet_file(packet,reference.removeprefix(prefix_path),4*1024**2).read_text(encoding='utf-8-sig')
                        require(screen.count('Beta body independent source.')==1,'final useful Frogmouth TUI frame missing')
            calibration.append(dict(fault=receipt['id'],phase=phase,command=identity,invocation_id=row['invocation_id'],report_sha256=sha256(path)))
    require(len(calibration)==len(ids)*3,'calibration denominator differs')
    removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/'+project and removed['source_archive_sha256']==review['archive_sha256']
        and prepared['runtime_processes_verified'],'unconfirmed target/runtime removal')
    for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'source selected restore changed')
    immutable_json(docs/('final-verified-'+host+'.json'),dict(run=args.run,host=host,ordinary_executions=240,calibration_executions=len(calibration),
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],target_pin=build['pin'],observations=rows,
        calibration_observations=calibration,source_fault_summary_sha256=sha256(summaries[0]),cleanup_receipt_sha256=sha256(retained/'removed.json'),
        final_archive_credit=0,scope='Exact final archive and reviewed native twelve-by-twenty profile; actual owned Python/launcher/source/dependency inventory identities, unchanged reviewed source-fault replicas, same-execution state and checked exact source/runtime restoration/removal. Helpers remain on bootstrap Python; target environment stays explicit per public invocation. Overall final matrix gates remain separate.'))
    print('Independently verified final',project,'native ordinary and actual source-fault series:',host)


if __name__=='__main__':main()
