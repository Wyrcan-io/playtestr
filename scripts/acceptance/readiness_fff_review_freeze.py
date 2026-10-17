"""Independently review both native public authoring packets before fault selection."""
import argparse
import base64
from pathlib import Path
import shutil

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_fff_cases import rows, plan_hash
from readiness_build_fff import PIN
ARCHIVE_SHA256='9411c915529860e0134907fdb5b54282cdd191be202436a6d3df9ed32d175e6f'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--source-revision',default='e7b5f29e575e44babe7fdaa2e83e55b62d318305')
    args = parser.parse_args()
    source_revision=args.source_revision
    require(len(source_revision)==40 and all(c in '0123456789abcdef' for c in source_revision),'invalid source revision')
    require(args.run.isascii() and args.run.isdecimal(), 'invalid native run')
    run = RAW/'native'/args.run
    metadata = load(run/'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success', 'native freeze run not successful')
    reviewed = ROOT/'docs/validation/runner-readiness-ten-project-pass/fff'
    cells = []
    linux = run/'playtestr-Linux/fff/contracts'
    for host in ['Linux', 'macOS']:
        packet = run/('playtestr-'+host)
        ledger = object.__new__(Campaign)
        ledger.raw = packet
        attempts = ledger.attempts()
        declared_rows=rows('macos' if host=='macOS' else 'linux')
        freeze = load(packet/'fff/reviewed-contract-freeze.json')
        package = packet/'fff/contracts'
        require(freeze['normal_scenarios'] == 8 and freeze['edge_scenarios'] == 12 and len(freeze['contracts']) == 20,
                'incomplete declared breadth')
        require(set(freeze['contracts']) == {r['id']+'.json' for r in rows()}, 'wrong scenario identities')
        runner = load(packet/'fff-native-runner.json')
        build = load(packet/'fff/retained-source/build.json')
        require(runner['source_revision'] == source_revision and
                runner['candidate_sha256'] == runner['copied_sha256'] == freeze['runner_sha256'], 'wrong frozen runner')
        require(build['pin'] == PIN and build['archive_sha256'] == ARCHIVE_SHA256, 'wrong source build')
        require(build['binary_sha256']==load(reviewed/'source-review.json')['reviewed_inputs']['fff'],'interpreted source differs from independent pinned review')
        require(freeze['target_build_sha256'] == sha256(packet/'fff/retained-source/build.json'), 'changed build receipt')
        for name, digest in freeze['all_package_inputs'].items():
            require(sha256(package/name) == digest, 'frozen package changed')
            if name not in freeze['contracts'] and not name.startswith('snapshots/'):
                require(sha256(package/name) == sha256(linux/name), 'native fixture differs')

        def witness(identity):
            events = attempts[identity]
            require('launched' in events and events['started']['expected_exit'] == 0, 'missing successful launch')
            finished = events['finished']
            require(finished['category'] == 'passed' and finished['exit_code'] == 0 and
                    finished['harness_cleanup'] == 'harness_process_reaped' and not finished['cleanup_errors'], 'unconfirmed command')
            ref = events['identified']['identity']
            manifest = packet_file(packet, ref['manifest'], 1024**2)
            require(sha256(manifest) == ref['sha256'], 'changed manifest')
            console = packet_file(packet, events['started']['project']+'/'+identity+'/console.log', 4*1024**2)
            require(sha256(console) == finished['console_sha256'], 'changed console')
            return load(manifest)['files']

        def result_ok(result):
            require(result['status'] == 'passed' and result['cleanup']['confirmed_exited'] and
                    result['workspace']['cleaned'], 'scenario or cleanup not passing')
            for step in result['steps']:
                if 'state' in step:
                    require(step['state']['invocation_id'] == result['invocation_id'] and
                            step['state']['workspace_id'] == result['workspace']['id'], 'cross-execution state')

        for row in declared_rows:
            approval = load(packet/'fff/approved'/(row['id']+'.json'))
            require(approval['plan_sha256'] == plan_hash(row), 'authoring plan changed')
            relative = Path(approval['spec']).relative_to('artifacts/runner-readiness-ten-project-pass').as_posix()
            spec = packet_file(packet, relative, 1024**2)
            require(sha256(spec) == approval['spec_sha256'], 'public export changed')
            contract = load(spec)
            states = {s['state']['path']:base64.b64decode(s['state']['bytes_base64'])
                      for s in contract['steps'] if s.get('state', {}).get('kind') == 'file'}
            require(states == row['expected'], 'independent exact-byte oracle differs')
            require({s['state']['path'] for s in contract['steps'] if s.get('state', {}).get('kind') == 'absent'} == set(row['missing']),
                    'absence contract differs')
            for identity in [approval['capture_attempt'], approval['ordinary_attempt']]:
                files = witness(identity)
                require(files['artifacts/runner-readiness-ten-project-pass/bin/playtestr'] == runner['copied_sha256'] and
                        files['artifacts/runner-readiness-ten-project-pass/active/fff/src/fff'] == build['binary_sha256'], 'actual binary differs')
            ordinary = spec.parent/'ordinary-result.json'
            require(sha256(ordinary) == approval['report_sha256'], 'authoring result changed')
            result_ok(load(ordinary)['results'][0])
            native = load(package/(row['id']+'.json'))
            require(native['command']==['fff'] and native['env']==dict(FFF_CD_ON_EXIT='1',FFF_LS_COLORS='0',FFF_TRASH='trash',LC_ALL='en_US.UTF-8' if host=='macOS' else 'C.UTF-8',TERM='xterm-256color'),'unexpected native target/environment profile')
            require(native['steps']==contract['steps'],'assembly changed public actions or byte expectations')
            entry_states={step['state']['path']:step['state']['entries'] for step in native['steps']
                          if step.get('state',{}).get('kind')=='entries'}
            require({name:sorted(value) for name,value in entry_states.items()}==row['entry_sets'] and
                    all(len(value)==len(set(value)) for value in entry_states.values()),'unreviewed directory set')
            if row['snapshot']:
                snapshot=next(step['snapshot'] for step in native['steps'] if 'snapshot' in step)
                captured=load(package/'snapshots'/snapshot)
                cwd='destination' if row['id']=='N04' else '.'
                names=row['entry_sets'][cwd]
                directory_names=[];file_names=[]
                for name in names:
                    relative=name if cwd=='.' else cwd+'/'+name
                    (directory_names if relative in row['entry_sets'] else file_names).append(name)
                rendered=[name+'/' for name in sorted(directory_names)]+sorted(file_names)
                if host=='macOS':rendered=['empty',*[name+'/' for name in sorted(directory_names)],'',*sorted(file_names)]
                expected_text='\n'.join(rendered)+'\n'
                require(captured==dict(snapshot_version=1,first_row=1,last_row=24,text=expected_text),'independent native file-list screen oracle differs')
            if row['id'] in {'N07','N08'}:
                prefix=[]
                for control in row['actions']:
                    command,_,value=control.partition(' ')
                    if command=='/text':
                        import json
                        prefix.append({'text':json.loads(value)})
                    else:
                        field={'/expect':'expect','/absent':'expect_not','/key':'key'}[command]
                        prefix.append({field:value})
                require(native['steps'][:len(prefix)]==prefix,'native directory selection differs from explicit declaration')
            else:
                canonical=load(linux/(row['id']+'.json'))
                if host=='macOS':native['env']['LC_ALL']='C.UTF-8'
                for comparison in [native,canonical]:
                    for step in comparison['steps']:
                        if step.get('state',{}).get('kind')=='entries':step['state']['entries']=sorted(step['state']['entries'])
                require(native==canonical,'unexpected native action/profile change')
        witness(freeze['ordinary_parent'])
        reports = list((packet/'fff/suites').glob('*/results.json'))
        require(len(reports) == 1 and sha256(reports[0]) == freeze['ordinary_report_sha256'], 'changed frozen suite result')
        full = load(reports[0])
        require(full['summary'] == dict(total=20, passed=20, failed=0, cancelled=0, not_run=0), 'ordinary suite incomplete')
        for result in full['results']:
            result_ok(result)
        removal = load(packet/'fff/retained-source/removed.json')
        require(removal['removed'] and removal['source_archive_sha256'] == ARCHIVE_SHA256, 'source cleanup missing')
        cells.append(dict(host=host, freeze_sha256=sha256(packet/'fff/reviewed-contract-freeze.json'),
                          suite_report_sha256=sha256(reports[0]), runner_sha256=runner['copied_sha256']))
    # Publish exact reviewed exports only after both independent packet reviews.
    require(not (reviewed/'contracts').exists() and not (reviewed/'reviewed-contract-freeze.json').exists(), 'freeze already published')
    shutil.copytree(linux, reviewed/'contracts')
    shutil.copyfile(run/'playtestr-Linux/fff/reviewed-contract-freeze.json', reviewed/'reviewed-contract-freeze.json')
    macos=reviewed/'native-profiles/macos';macos.mkdir(parents=True)
    shutil.copytree(run/'playtestr-macOS/fff/contracts',macos/'contracts')
    shutil.copyfile(run/'playtestr-macOS/fff/reviewed-contract-freeze.json',macos/'reviewed-contract-freeze.json')
    immutable_json(reviewed/'native-authoring-review.json', dict(run=args.run, cells=cells, source_revision=source_revision,
                   public_contract_freeze_sha256=sha256(reviewed/'reviewed-contract-freeze.json'),
                   fault_selection='No source fault selected before this independently verified twenty-case freeze.',
                   development_admission=False, final_archive_credit=False))
    print('Reviewed both explicit native profiles for twenty public recordings, ordinary tests, unchanged native byte/screen oracles and frozen suites before fault selection.')


if __name__ == '__main__':
    main()
