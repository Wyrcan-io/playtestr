"""Independently audit real Plop final native batches, faults and cleanup."""
import argparse
from pathlib import Path

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require, verify_batches
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','macos'],required=True)
    parser.add_argument('--packet-root',type=Path);parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    parent=args.packet_root.resolve(strict=True) if args.packet_root else RAW/'native'/args.run
    parent.resolve(strict=True).relative_to(RAW.resolve(strict=True))
    metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2
        and all(j['status']=='completed' and j['conclusion']=='success' for j in metadata['jobs']),'incomplete native jobs')
    packet=parent/('final-plop-'+('Linux' if args.host=='linux' else 'macOS'));target=packet/'plop'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/plop';profile=docs/'final-native-profile'
    candidate=load(docs.parent/'migration-candidate-freeze.json');host='linux' if args.host=='linux' else 'darwin'
    cell=next(c for c in candidate['cells'] if c['host']==host)
    installed=load(packet/'private-install/migration-v2'/(host+'-'+cell['architecture'])/'installation.json')
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256']
        and installed['source_revision']==candidate['source_revision'],'different native private archive')
    review=load(docs/'source-review.json');retained=target/'retained-source';build=load(retained/'build.json');runtime=load(retained/'runtime.json')
    require(build['pin']==review['pin'] and build['scripts_disabled'] and build['runtime']==runtime
        and build['yarn_lock_sha256']==review['reviewed_inputs']['yarn.lock']
        and build['license_sha256']==review['reviewed_inputs']['LICENSE.md']
        and build['yarn_sha256']==review['reviewed_inputs']['.yarn/releases/yarn-4.9.4.cjs'],'wrong actual target build')
    index=load(retained/'verified-index.json')
    require(index['archive_sha256']==review['archive_sha256']
        and {n:r['sha256'] for n,r in index['files'].items()}==review['reviewed_inputs'],'different retained source catalog')
    prefix='artifacts/runner-readiness-ten-project-pass/active/plop/src/'
    selected={n:d for n,d in review['reviewed_inputs'].items() if n=='yarn.lock'
        or n.endswith('.js') and any(n.startswith(p) for p in ['packages/plop/src/','packages/plop/bin/','packages/node-plop/src/'])}
    ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts()
    def witness(identity,expected=0,source_override=None,public=False,alias=False):
        event=events[identity];end=event['finished']
        require(all(e['phase']=='final-archive' for e in event.values()) and 'launched' in event,'missing final-phase launch')
        require(event['started']['expected_exit']==expected and end['category']=='passed' and end['exit_code']==expected
            and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'actual command outcome/cleanup differs')
        require(sha256(packet/event['started']['project']/identity/'console.log')==end['console_sha256'],'changed actual output')
        manifest=load_manifest(packet,event['identified']['identity']);files=manifest['files'];expected_source=dict(selected)
        if source_override:expected_source[source_override[0]]=source_override[1]
        observed={n[len(prefix):]:d for n,d in files.items() if n.startswith(prefix)}
        require(all(observed.get(n)==d for n,d in expected_source.items())
            and all(n in review['reviewed_inputs'] and d==review['reviewed_inputs'][n]
                for n,d in observed.items() if n not in expected_source),'actual interpreted source/lock differs')
        require(manifest['runtime_executables']['node']==runtime['sha256'],'actual installed Node differs')
        if public:
            runner_key='artifacts/runner-readiness-ten-project-pass/bin/playtestr' if alias else installed['binary']
            require(files[runner_key]==cell['binary_sha256'],'actual exact archive differs')
        return files
    witness(build['attempt'])
    frozen=load(profile/'reviewed-contract-freeze.json');declaration=load(docs/'final-series-declaration.json')
    for name,indices in declaration['segmented_text_steps_by_host'][args.host].items():
        original=load(profile/'contracts'/name)
        derived=[i for i,s in enumerate(original['steps'],1) if set(s)=={'text'} and len(s['text'])>1
            and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
        require(indices==derived,'segmentation exceeds reviewed printable responses')
    rows,commands,result_ok,bind_inputs=verify_batches(packet,docs,profile,args.host,candidate,cell,installed,build,events,witness)
    summaries=list((target/'faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
    summary=load(summaries[0]);root=summaries[0].parent
    require(summary['phase']=='final-archive' and len(summary['faults'])==3 and {f['id'] for f in summary['faults']}=={'F01','F02','F03'},
        'incomplete actual source fault set')
    choices={f['id']:f for f in load(docs/'faults/selected-faults.json')['faults']};calibration=[]
    for receipt in summary['faults']:
        choice=choices[receipt['id']];original=load(docs/'faults'/(receipt['id']+'-receipt.json'))
        require(receipt['source']==choice['source'] and not receipt['held_out'] and receipt['cleanup_confirmed']
            and receipt['mutated_source_sha256']==original['mutated_source_sha256']
            and receipt['restored_source_sha256']==original['restored_source_sha256']==review['reviewed_inputs'][choice['source']]
            and receipt['spec_sha256']==frozen['contracts'][choice['spec']],'reviewed actual source mutation differs')
        require(sha256(root/(receipt['id']+'.patch'))==sha256(docs/'faults'/(receipt['id']+'.patch')),'actual patch differs')
        for phase,code,digest in [('baseline',0,receipt['restored_source_sha256']),('mutated',1,receipt['mutated_source_sha256']),
            ('restored',0,receipt['restored_source_sha256'])]:
            identity=receipt[phase];require(identity not in commands,'reused calibration command');commands.add(identity)
            files=witness(identity,code,(choice['source'],digest),public=True,alias=True)
            package=target/'host-contracts';contract=load(package/choice['spec'])
            bind_inputs(files,package,contract,choice['spec'],frozen['all_package_inputs'])
            path=root/(receipt['id']+'-'+phase+'.json');value=load(path);row=value['results'][0]
            require(value['runner_version']==candidate['version'] and row['spec_version']==3
                and Path(row['spec_path'].replace('\\','/')).name==choice['spec'],'actual calibration version/spec differs')
            result_ok(row,'failed' if code else 'passed')
            if code:
                require(row['failure']['category']==receipt['rejection'],'wrong actual mutant rejection')
                if receipt['id']=='F03':
                    failed=next(i for i,s in enumerate(row['steps']) if s['status']=='failed');prior=row['steps'][:failed]
                    require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
                        and row['steps'][failed]['state']['kind']=='file' and row['target']['exit_code']==0,'missing actual false-green state rejection')
            calibration.append(dict(fault=receipt['id'],phase=phase,command=identity,invocation_id=row['invocation_id'],report_sha256=sha256(path)))
    removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/plop' and removed['source_archive_sha256']==review['archive_sha256']
        and prepared['node_processes_verified'],'unconfirmed target/runtime removal')
    for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'source selected restore changed')
    if args.check_only:
        print('Reverified final Plop without publishing another receipt:',args.host)
        return
    immutable_json(docs/('final-verified-'+args.host+'.json'),dict(run=args.run,host=args.host,ordinary_executions=240,calibration_executions=9,
        runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],target_pin=build['pin'],observations=rows,
        calibration_observations=calibration,source_fault_summary_sha256=sha256(summaries[0]),cleanup_receipt_sha256=sha256(retained/'removed.json'),
        final_archive_credit=0,scope='Exact final archive, native twelve-by-twenty reviewed POSIX profile, actual Node/JavaScript/lock identities, three real source mutations, unchanged public outcomes and exact restoration/cleanup. Overall final matrix and control gates remain separate.'))
    print('Independently verified final Plop ordinary and fault series:',args.host)


if __name__=='__main__':main()
