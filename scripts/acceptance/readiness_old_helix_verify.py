"""Independently audit original case prefixes and actual public state evidence."""
import argparse
import base64
import hashlib
from pathlib import PurePosixPath
import re

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


from readiness_old_cookiecutter_verify import model_states


def audit(base,host,run=None,series='provisional-v1'):
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/helix'
    require(series in {'provisional-v1','migration-v2'},'undeclared private candidate series')
    review=load(docs/'source-review.json');frozen=load(docs.parents[1]/('migration-candidate-freeze.json' if series=='migration-v2' else 'provisional-candidate-freeze.json'))
    cell=next(c for c in frozen['cells'] if c['host']==host)
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/helix'
    inventory=load(docs.parents[1]/'old-migration-inventory.json')
    original=next(p for p in inventory['projects'] if p['project']=='helix')
    require(sha256(old/'scenarios.json')==original['original_scenarios_sha256'],'original declared scenarios changed')
    cases={c['name']:c for c in load(old/'scenarios.json')['cases']}
    target=base/'old-helix';retained=target/'retained-source'
    build=load(retained/'build.json');runtime=load(retained/'runtime.json');acquisition=load(retained/'acquisition.json')
    if host=='linux':
        from readiness_old_superfile_verify import canonical_archive
        canonical=canonical_archive(target,review,project='helix')
    else:canonical=retained/'source.tar.gz'
    require(build['pin']==review['pin']==original['pin']
            and acquisition['archive_sha256']==review['archive_sha256']==sha256(canonical),
            'actual original target/source identity differs')
    installed=load(base/('private-install/'+series+'/'+host+'-amd64/installation.json'))
    require(installed['binary_sha256']==cell['binary_sha256'] and installed['archive_sha256']==cell['archive_sha256'],'actual frozen runner/archive differs')
    prefix='artifacts/runner-readiness-ten-project-pass/active/old-helix/'
    require(runtime['rustc_sha256']==build['rustc_sha256'] and runtime['cargo_sha256']==build['cargo_sha256']
            and runtime['native_triple']==build['native_triple']==('x86_64-pc-windows-msvc' if host=='windows' else 'x86_64-unknown-linux-gnu'),
            'actual Rust/Cargo native profile differs')
    resource_inputs={n.removeprefix('runtime/'):h for n,h in review['reviewed_inputs'].items()
        if n.startswith('runtime/') and not n.startswith('runtime/grammars/')}
    require(build['runtime_resources']==resource_inputs,'original pinned runtime resources differ or external grammars included')
    original_binary=build['binary_sha256']
    def witness(identity,expected=0,mutated=None,runner=True,target_digest=original_binary):
        events={kind:load(base/'events'/(identity+'-'+kind+'.json')) for kind in ['started','identified','launched','finished']}
        if series=='migration-v2':require(all(e['phase']=='final-archive' for e in events.values()),'nonfinal migration event')
        require(all(r['id']==identity and r['event']==k and r['project']=='old-helix' for k,r in events.items()),'command event identity differs')
        finished=events['finished']
        require(events['started']['expected_exit']==expected and finished['category']=='passed' and finished['exit_code']==expected
                and finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'],'actual command outcome/cleanup differs')
        reference=events['identified']['identity'];manifest=packet_file(base,reference['manifest'].replace('\\','/'),2*1024**2)
        require(sha256(manifest)==reference['sha256'],'prelaunch identity changed')
        actual=load(manifest,maximum=2*1024**2);files=actual['files'];source=dict(review['reviewed_inputs'])
        if mutated:source['helix-term/src/application.rs']=mutated
        for name,digest in source.items():require(files[prefix+'src/'+name]==digest,'actual original/mutated source differs')
        require(actual['runtime_executables']['rustc']==runtime['rustc_sha256']
                and actual['runtime_executables']['cargo']==runtime['cargo_sha256'],'actual original Rust/Cargo differs')
        require(files[prefix+'runtime.json']==sha256(retained/'runtime.json'),'actual compiler receipt changed')
        for name,digest in resource_inputs.items():
            require(files[prefix+'bin/runtime/'+name]==digest,'actual runtime resource input differs')
        if target_digest is not None:
            require(files[prefix+build['binary_relative_path']]==target_digest,'actual original/mutated target binary differs')
        if runner:require(files[installed['binary']]==cell['binary_sha256'],'actual public runner differs')
        console=base/'old-helix'/identity/'console.log'
        require(sha256(console)==finished['console_sha256'],'actual command output changed')
        return files,console.read_text(encoding='utf-8-sig')
    parent=base/'old-migration/helix'/host
    runs=list((parent/'runs').glob('*/verified.json'));require(len(runs)==1,'ambiguous complete native migration suite')
    verified=load(runs[0]);root=runs[0].parent;package=root/'contracts'
    require(verified['cases']==12 and verified['runner_sha256']==cell['binary_sha256']
            and verified['provisional_archive_sha256']==cell['archive_sha256'],'wrong actual native migration scope')
    report=load(root/'results.json')
    require(sha256(root/'results.json')==verified['report_sha256'] and report['runner_version']==frozen['version']
            and report['summary']==dict(total=12,passed=12,failed=0,cancelled=0,not_run=0),'native original suite denominator differs')
    require(len({r['invocation_id'] for r in report['results']})==12,'duplicate migrated invocation')
    def clean(row,status):
        require(row['status']==status and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'result or managed cleanup differs')
        if status=='passed':require(all(s['status']=='passed' for s in row['steps']),'passing result contains incomplete actions')
        for step in row['steps']:
            if 'state' in step:
                require(step['state']['invocation_id']==row['invocation_id']
                        and step['state']['workspace_id']==row['workspace']['id'],'cross-execution saved-state proof')
    materialized=load(parent/'materialized.json');profile=load(root/'execution-profile.json')
    require(sha256(root/'execution-profile.json')==verified['execution_profile_sha256']
            and profile['original_materialized_sha256']==sha256(parent/'materialized.json'),'actual execution profile differs')
    for item in materialized['cases']:
        name=item['case'];native=ROOT/item['original_native_spec'];before=load(native);spec=package/(name+'.json');contract=load(spec)
        require(sha256(native)==item['original_native_spec_sha256'],'original native prefix source changed')
        expected=dict(before,version=3,steps=contract['steps'])
        require(contract==expected and contract['steps'][:len(before['steps'])]==before['steps'],'original native contract/prefix changed')
        model_states(cases[name],contract['steps'][len(before['steps']):])
        for step in before['steps']:
            if 'snapshot' in step:
                require(sha256(package/'snapshots'/step['snapshot'])==sha256(native.parent/'snapshots'/step['snapshot']),
                        'original snapshot weakened')
        fixture=before['workspace']['fixture']
        for path in (native.parent/fixture).rglob('*'):
            if path.is_file():require(sha256(package/fixture/path.relative_to(native.parent/fixture))==sha256(path),'original fixture bytes changed')
        rows=[r for r in report['results'] if r['spec_path'].replace('\\','/').split('/')[-1]==spec.name]
        require(len(rows)==1 and len(rows[0]['steps'])==len(contract['steps']),'missing/duplicate or partial original case')
        clean(rows[0],'passed')
    _,parent_output=witness(verified['parent_attempt'],runner=False)
    ids=re.findall(r'Immutable suite attempt: ([0-9a-f]{32})',parent_output);require(len(ids)==1,'actual public suite invocation missing')
    files,_=witness(ids[0])
    for path in package.rglob('*'):
        if path.is_file():
            key='artifacts/runner-readiness-ten-project-pass/'+path.relative_to(base).as_posix()
            require(files[key]==sha256(path),'actual public suite input not bound')
    controls=list((parent/'corruption').glob('*/verified.json'));require(len(controls)==1,'missing actual corruption/recovery proof')
    control=load(controls[0]);control_root=controls[0].parent;declaration=load(control_root/'declared.json')
    require(control['original_native_suite_sha256']==sha256(runs[0]) and control['restored_exact'] and control['approved_inputs_unchanged'],
            'corruption belongs to another case package or restoration failed')
    source=retained/'selected-restore/helix-term/src/application.rs';before=source.read_bytes()
    definition=load(old/'faults/definitions.json')[2]
    require(definition['name']=='silent-saved-document-corruption' and definition['file']=='helix-term/src/application.rs'
            and definition['case']=='normal-project','original fault definition differs')
    needle=definition['old'].encode();replacement=definition['new'].encode()
    require(before.count(needle)==1 and sha256(source)==review['reviewed_inputs']['helix-term/src/application.rs'],'original writer differs')
    changed=hashlib.sha256(before.replace(needle,replacement)).hexdigest()
    require(changed==control['mutated_source_sha256']==declaration['mutated_source_sha256'],'real source corruption differs')
    changed_build=control['builds']['actual-corrupted-writer-build'];restored_build=control['builds']['exact-original-writer-rebuild']
    changed_binary=changed_build['binary_sha256']
    require(changed_binary!=original_binary and changed_build['source_sha256']==changed
            and restored_build['source_sha256']==sha256(source)
            and restored_build['binary_sha256']==original_binary==control['original_binary_sha256'],
            'actual mutated build or exact compiled restoration differs')
    witness(changed_build['attempt'],mutated=changed,runner=False)
    witness(restored_build['attempt'],runner=False,target_digest=changed_binary)
    for label,expected in [('legacy-terminal-false-green',0),('public-state-corruption-rejected',1),('public-state-corruption-restored',0)]:
        call=control['calls'][label];corrupted=expected==1 or label.startswith('legacy-')
        witness(call['attempt'],expected,changed if corrupted else None,target_digest=changed_binary if corrupted else original_binary)
        value=load(control_root/(label+'.json'));row=value['results'][0]
        require(sha256(control_root/(label+'.json'))==call['report_sha256'],'corruption report changed')
        clean(row,'failed' if expected else 'passed')
        require(row['target']['exited'] and row['target']['exit_code']==0,'corruption did not preserve actual exit0')
        if expected:
            require(row['failure']['category']=='state_assertion_failure','wrong actual corruption category')
            failed=next(i for i,s in enumerate(row['steps']) if s['status']=='failed');prior=row['steps'][:failed]
            require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
                    and row['steps'][failed]['state']['kind']=='file','saved corruption lacks passing same-run screen/exit')
    index=load(retained/'verified-index.json');removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/old-helix'
            and prepared['source_archive_verified'] and prepared['managed_cleanup_verified'] and prepared['runtime_processes_verified'],
            'original source/runtime removal not confirmed')
    require({n:r['sha256'] for n,r in index['files'].items()}==review['reviewed_inputs'],'retained original source catalog differs')
    for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'selected source restoration differs')
    return dict(project='helix',host=host,run=run,scenarios=12,runner_sha256=cell['binary_sha256'],
        provisional_archive_sha256=cell['archive_sha256'],canonical_source_sha256=sha256(canonical),target_pin=review['pin'],full_suite_sha256=sha256(root/'results.json'),
        corruption_sha256=sha256(controls[0]),cleanup_sha256=sha256(retained/'removed.json'),
        scope='Original native case actions and exact baselines plus public same-execution saved outcomes; actual writer corruption and exact restoration.',
        new_project_credit=0,final_archive_credit=0)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['windows','linux'],required=True)
    parser.add_argument('--run');args=parser.parse_args()
    base=RAW
    if args.run:
        require(args.host=='linux' and args.run.isascii() and args.run.isdecimal(),'invalid native migration run')
        parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
        require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==1
                and metadata['jobs'][0]['name']=='original-linux' and metadata['jobs'][0]['conclusion']=='success',
                'complete successful native Linux migration job required')
        base=parent/'old-helix-Linux'
    else:require(args.host=='windows','local qualification is actual Windows only')
    receipt=audit(base,args.host,args.run)
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/helix'
    immutable_json(docs/('verified-'+args.host+'.json'),receipt)
    print('Independently verified original helix native cases, public saved-state rejection/recovery and checked cleanup:',args.host)


if __name__=='__main__':main()
