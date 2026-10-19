"""Verify actual two-host config state, compiled provenance and source cleanup."""
import argparse
import base64

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def require(condition, message):
    if not condition:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    run=RAW/'native'/args.run
    metadata=load(run/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success'
            and len(metadata['jobs'])==2 and all(j['conclusion']=='success' for j in metadata['jobs']),
            'missing two successful native first-use jobs')
    require({j['name'] for j in metadata['jobs']}=={'terminal (ubuntu-24.04)','terminal (windows-2025)'},
            'wrong actual native host matrix')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    frozen=load(docs/'provisional-candidate-freeze.json')
    review=load(docs/'rclone/source-review.json')
    cells=[]
    for artifact,host in [('Linux','linux'),('Windows','windows')]:
        packet=run/('playtestr-'+artifact)
        ledger=object.__new__(Campaign)
        ledger.raw=packet
        attempts=ledger.attempts()
        cell=next(r for r in frozen['cells'] if r['host']==host and r['architecture']=='amd64')
        installed=load(packet/'private-install/provisional-v1'/(host+'-amd64')/'installation.json')
        require(installed['archive_sha256']==cell['archive_sha256']
                and installed['binary_sha256']==cell['binary_sha256'] and installed['version']==frozen['version'],
                'different actual frozen native archive')
        retained=packet/'rclone/retained-source'
        index=load(retained/'verified-index.json')
        build=load(retained/'build.json')
        runtime=load(retained/'runtime.json')
        sdk=load(retained/'sdk.json')
        require(build['pin']==review['pin'] and build['source_review_sha256']==sha256(docs/'rclone/source-review.json')
                and build['version']=='v1.76.0-DEV' and not build['cgo_enabled'] and not build['target_hooks_executed']
                and sdk['host']==host and sdk['architecture']=='amd64' and sdk['version']=='go1.27.0'
                and build['sdk_sha256']==sha256(retained/'sdk.json')==runtime['sdk_sha256']
                and build['compiler_sha256']==runtime['compiler_sha256'],'wrong native target/compiler/build scope')
        require(build['native_settings']['GOOS']==host and build['native_settings']['GOARCH']=='amd64'
                and build['native_settings']['CGO_ENABLED']=='0' and build['native_settings']['GOVERSION']=='go1.27.0',
                'different actual native Go settings')
        require(index['archive_sha256']==review['archive_sha256']
                and {n:r['sha256'] for n,r in index['files'].items()}==review['reviewed_inputs'],
                'retained native source catalog differs from original source')
        receipts=packet/'rclone/build-receipts'
        receipt_index=load(receipts/'index.json')
        for name,digest in receipt_index['files'].items():
            require(sha256(packet_file(receipts,name,1024**2))==digest,'changed actual build receipt')
        for name in ['build.json','runtime.json']:
            require(sha256(receipts/name)==sha256(retained/name),'setup and retained build/runtime receipts differ')
        require(sha256(receipts/'toolchain/sdk.json')==sha256(retained/'sdk.json'),'setup and retained SDK differ')
        prefix='artifacts/runner-readiness-ten-project-pass/active/rclone/'

        def witness(identity,first_use=False):
            event=attempts[identity]
            finished=event['finished']
            require('launched' in event and event['started']['expected_exit']==0
                    and finished['category']=='passed' and finished['exit_code']==0
                    and not finished['cleanup_errors'] and finished['harness_cleanup']=='harness_process_reaped',
                    'actual command outcome/cleanup differs')
            reference=event['identified']['identity']
            manifest=packet_file(packet,reference['manifest'],2*1024**2)
            require(sha256(manifest)==reference['sha256'],'prelaunch manifest changed')
            actual=load(manifest,maximum=2*1024**2)
            files=actual['files']
            observed={n[len(prefix+'src/'):]:digest for n,digest in files.items() if n.startswith(prefix+'src/')}
            require(observed==review['reviewed_inputs'],'actual prelaunch target source differs')
            if first_use:
                require(files[prefix+build['binary_relative_path']]==build['binary_sha256']
                        and files[prefix+'toolchain/go/bin/'+('go.exe' if host=='windows' else 'go')]==build['compiler_sha256']
                        and actual['runtime_executables']['go']==build['compiler_sha256']
                        and files[installed['binary']]==cell['binary_sha256'],'actual compiled target/compiler/runner differs')
            console=packet/event['started']['project']/identity/'console.log'
            require(sha256(console)==finished['console_sha256'],'command output changed')
            return files,console.read_text(encoding='utf-8-sig')

        for key in ['build_attempt','settings_attempt','version_attempt']:witness(build[key])
        journeys=list((packet/'rclone/first-use').glob('*/journey.json'))
        require(len(journeys)==1,'missing or ambiguous successful first route')
        path=journeys[0]
        journey=load(path)
        package=path.parent
        require(journey['shell_invocations']==3 and journey['recorder_controls']==20
                and not journey['handwritten_playtestr_json'] and journey['runner_sha256']==cell['binary_sha256']
                and journey['provisional_archive_sha256']==cell['archive_sha256']
                and journey['target_build_sha256']==sha256(retained/'build.json'),'fresh route budget or identity differs')
        for identity in journey['attempts']:
            files,output=witness(identity,True)
            if identity==journey['capture_attempt']:
                require('Exported ' in output and 'unresolved control failures' not in output,'public replay/export refused')
            if identity in {journey['capture_attempt'],journey['ordinary_attempt']}:
                for name in ['rclone.conf','sentinel.bin']:
                    key='artifacts/runner-readiness-ten-project-pass/'+(package/'fixture'/name).relative_to(packet).as_posix()
                    require(files[key]==sha256(package/'fixture'/name),'actual first-route fixture not bound')
        require((package/'fixture/rclone.conf').read_bytes()==b''
                and (package/'fixture/sentinel.bin').read_bytes()==b'preserve\x00existing\r\n','original fixture changed')
        contract=load(package/'spec.json')
        require(sha256(package/'spec.json')==journey['spec_sha256']
                and contract['command']==['rclone','--config','rclone.conf','config'],'exported command/spec differs')
        newline=b'\r\n' if host=='windows' else b'\n'
        expected={'rclone.conf':newline.join([b'[demo]',b'type = alias',b'remote = .',b'',b'']),
                  'sentinel.bin':b'preserve\x00existing\r\n'}
        actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps']
                if s.get('state',{}).get('kind')=='file'}
        entries=[s['state'] for s in contract['steps'] if s.get('state',{}).get('kind')=='entries']
        require(actual==expected and len(entries)==1 and entries[0]['path']=='.'
                and entries[0]['entries']==['rclone.conf','sentinel.bin'],'independent exact file/entry oracle differs')
        snapshot=next(s['snapshot'] for s in contract['steps'] if 'snapshot' in s)
        text=(package/'snapshots'/snapshot).read_text(encoding='utf-8')
        require('Current remotes:' in text and 'demo' in text and 'alias' in text,'live saved-config screen lacks positive evidence')
        report=load(package/'ordinary-results.json')
        require(report['runner_version']==frozen['version']
                and report['summary']==dict(total=1,passed=1,failed=0,cancelled=0,not_run=0),'ordinary public report differs')
        result=report['results'][0]
        require(result['status']=='passed' and result['cleanup']['confirmed_exited']
                and result['workspace']['cleaned'],'ordinary cleanup unconfirmed')
        for step in result['steps']:
            require(step['status']=='passed','ordinary step incomplete')
            if 'state' in step:
                require(step['state']['invocation_id']==result['invocation_id']
                        and step['state']['workspace_id']==result['workspace']['id'],'state proof from another execution')
        removed=load(retained/'removed.json')
        prepared=load(retained/'removal-prepared.json')
        require(removed['removed'] and removed['owned_relative_path']=='active/rclone'
                and removed['source_archive_sha256']==review['archive_sha256']
                and prepared['runtime_processes_verified'] and prepared['source_archive_verified']
                and prepared['managed_cleanup_verified'],'native source/runtime cleanup unconfirmed')
        for name in index['selected_restore']:
            require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'selected source restore differs')
        cache_files,_=witness(load(retained/'owned-cache-cleanup.json')['attempt'])
        require(cache_files[prefix+build['binary_relative_path']]==build['binary_sha256']
                and cache_files[prefix+'toolchain/go/bin/'+('go.exe' if host=='windows' else 'go')]==build['compiler_sha256'],
                'owned-cache cleanup used another target/compiler identity')
        cells.append(dict(host=host,architecture='amd64',runner_sha256=cell['binary_sha256'],
            archive_sha256=cell['archive_sha256'],target_binary_sha256=build['binary_sha256'],
            journey_sha256=sha256(path),spec_sha256=sha256(package/'spec.json'),cleanup_sha256=sha256(retained/'removed.json')))
    immutable_json(docs/'rclone'/('first-use-native-'+args.run+'.json'),dict(run=args.run,cells=cells,
        fresh_route_shell_commands=3,fresh_route_controls=20,
        cumulative_windows_shell_commands=5,cumulative_windows_requested_controls=40,
        engineering_control_target='Missed cumulatively on Windows; original failed first route retained.',
        human_usability='unmeasured',development_admission=False,final_archive_credit=0))
    print('Verified real native local-alias first route, same-execution state, compiled identities and cleanup on Linux/Windows.')


if __name__=='__main__':main()
