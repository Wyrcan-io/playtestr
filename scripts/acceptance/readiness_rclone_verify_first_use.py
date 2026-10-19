"""Verify actual two-host config state, compiled provenance and source cleanup."""
import argparse
import base64

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def require(condition, message):
    if not condition:raise RuntimeError(message)


def verify_native(run_id,publish=True,*,phase_only=False,hosts=None,job_hosts=None):
    require(hosts is None or set(hosts)<= {'linux','windows'} and len(set(hosts))==len(hosts) and hosts,
            'invalid first-use audit host selection')
    require(hosts is None or not publish,'partial host audit cannot publish a two-host first-use receipt')
    job_hosts=['linux','windows'] if job_hosts is None else job_hosts
    require(job_hosts and len(job_hosts)==len(set(job_hosts)) and set(job_hosts)<={'linux','windows'},'invalid native job scope')
    require(hosts is None or set(hosts)<=set(job_hosts),'audit host is outside actual job scope')
    names={'linux':'terminal (ubuntu-24.04)','windows':'terminal (windows-2025)'}
    args=argparse.Namespace(run=run_id)
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    run=RAW/'native'/args.run
    metadata=load(run/'run-metadata.json')
    require(metadata['status']=='completed' and len(metadata['jobs'])==len(job_hosts)
            and all(j['status']=='completed' for j in metadata['jobs']),
            'missing two completed native jobs')
    if phase_only:
        for job in metadata['jobs']:
            cleanup=('Verify Windows source restoration and runtime termination before removal'
                     if 'windows' in job['name'] else
                     'Verify Unix source restoration and runtime termination before removal')
            for name in ['Reviewed owned target setup',
                         'First public recording, explicit review, replay and ordinary test',cleanup]:
                matches=[s for s in job['steps'] if s['name']==name]
                require(len(matches)==1 and matches[0]['status']=='completed'
                        and matches[0]['conclusion']=='success','actual first-use/setup/cleanup phase failed')
    else:
        require(metadata['conclusion']=='success' and all(j['conclusion']=='success' for j in metadata['jobs']),
                'missing two successful native first-use jobs')
    require({j['name'] for j in metadata['jobs']}=={names[h] for h in job_hosts},
            'wrong actual native host matrix')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    frozen=load(docs/'provisional-candidate-freeze.json')
    review=load(docs/'rclone/source-review.json')
    cells=[]
    for artifact,host in [('Linux','linux'),('Windows','windows')]:
        if hosts is not None and host not in hosts:continue
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
        require(journey['shell_invocations']==3 and journey['recorder_controls']==16
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
        newline=b'\r\n' if host=='windows' else b'\n'
        require((package/'fixture/rclone.conf').read_bytes()==newline.join([b'[seed]',b'type = local',b'',b''])
                and (package/'fixture/sentinel.bin').read_bytes()==b'preserve\x00existing\r\n','original fixture changed')
        contract=load(package/'spec.json')
        require(sha256(package/'spec.json')==journey['spec_sha256']
                and contract['command']==['rclone','--config','rclone.conf','config'],'exported command/spec differs')
        expected={'rclone.conf':newline.join([b'[reviewed]',b'type = local',b'',b'']),
                  'sentinel.bin':b'preserve\x00existing\r\n'}
        actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps']
                if s.get('state',{}).get('kind')=='file'}
        entries=[s['state'] for s in contract['steps'] if s.get('state',{}).get('kind')=='entries']
        require(actual==expected and len(entries)==1 and entries[0]['path']=='.'
                and len(entries[0]['entries'])==2 and set(entries[0]['entries'])=={'rclone.conf','sentinel.bin'},
                'independent exact file/entry oracle differs')
        snapshot=next(s['snapshot'] for s in contract['steps'] if 'snapshot' in s)
        text=(package/'snapshots'/snapshot).read_text(encoding='utf-8')
        require('Current remotes:' in text and 'reviewed' in text and 'local' in text,'live saved-config screen lacks positive evidence')
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
    receipt=dict(run=args.run,cells=cells,workflow_conclusion=metadata['conclusion'],
        phase_only=phase_only,whole_workflow_success=metadata['conclusion']=='success',
        fresh_route_shell_commands=3,fresh_route_controls=16,
        initial_windows_first_use_window=dict(shell_commands=7,requested_controls=56),
        metric_scope='Fresh route repetitions are recorded per pipeline; initial-window metrics exclude later regression repetitions.',
        engineering_control_target='Missed cumulatively on Windows; original failed first route retained.',
        human_usability='unmeasured',development_admission=False,final_archive_credit=0)
    if publish:
        immutable_json(docs/'rclone'/('first-use-native-'+args.run+'.json'),receipt)
        print('Verified real native local-config rename, same-execution state, compiled identities and cleanup on Linux/Windows.')
    return receipt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--phase-only',action='store_true')
    args=parser.parse_args()
    verify_native(args.run,phase_only=args.phase_only)


if __name__=='__main__':main()
