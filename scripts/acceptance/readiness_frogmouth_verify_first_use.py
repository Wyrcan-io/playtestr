"""Independently verify native first-use commands, bytes, source and cleanup."""
import argparse
import base64

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_frogmouth_first_use import fixture_files

PIN='15c3e85a6e84b2e4a6845723acf12beb54c81eb2'
ARCHIVE='f6a61477300bc380494322b53e3a3957f9d939a8e099e5e82382cce6112a2b1a'


def require(condition,message):
    if not condition:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--controls',type=int,choices=[16,24],default=16)
    parser.add_argument('--source-revision',default='3d50d81aae8f1d24f7a718e6e05b39069697b1a6');args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    source=args.source_revision
    require(len(source)==40 and all(c in '0123456789abcdef' for c in source),'invalid source revision')
    run=RAW/'native'/args.run;metadata=load(run/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success','native first use failed or incomplete')
    require(len(metadata['jobs'])==2 and all(j['conclusion']=='success' for j in metadata['jobs']),'missing successful native jobs')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/frogmouth'
    reviewed=load(docs/'source-review.json')['reviewed_inputs'];seed=fixture_files();cells=[]
    expected=seed
    for host in ['Linux','Windows']:
        packet=run/('playtestr-'+host);ledger=object.__new__(Campaign);ledger.raw=packet;attempts=ledger.attempts()
        runner=load(packet/'frogmouth-native-runner.json');retained=packet/'frogmouth/retained-source'
        require(runner['source_revision']==source and runner['candidate_sha256']==runner['copied_sha256'],'wrong candidate')
        build=load(retained/'build.json');runtime=load(retained/'runtime.json');index=load(retained/'verified-index.json')
        require(build['pin']==runtime['source_pin']==PIN and index['archive_sha256']==ARCHIVE,'wrong upstream source')
        require(build['source_editable'] and load(retained/build['wheel_manifest'])==build['dependency_wheels'],'dependency manifest differs')
        journeys=list((packet/'frogmouth/first-use').glob('*/journey.json'));require(len(journeys)==1,'ambiguous first-use journey')
        journey=load(journeys[0]);package=journeys[0].parent
        require(journey['shell_invocations']==3 and journey['recorder_controls']==args.controls and not journey['handwritten_playtestr_json'],'wrong route count')
        require(journey['target_build_sha256']==sha256(retained/'build.json') and journey['runner_sha256']==runner['copied_sha256'],'journey identity differs')
        for identity in [*journey['attempts'],build['version_attempt']]:
            event=attempts[identity];finished=event['finished']
            require('launched' in event and event['started']['expected_exit']==0 and finished['category']=='passed' and finished['exit_code']==0,'missing actual successful command')
            require(finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'],'command cleanup unconfirmed')
            ref=event['identified']['identity'];manifest=packet_file(packet,ref['manifest'],1024**2)
            require(sha256(manifest)==ref['sha256'],'changed prelaunch manifest')
            console=packet_file(packet,event['started']['project']+'/'+identity+'/console.log',4*1024**2)
            require(sha256(console)==finished['console_sha256'],'changed command output')
            files=load(manifest)['files']
            for name,digest in reviewed.items():
                if name.endswith('.py') or name=='pyproject.toml':
                    require(files['artifacts/runner-readiness-ten-project-pass/active/frogmouth/src/'+name]==digest,'different actual editable source')
            if identity in journey['attempts']:
                suffix='.exe' if host=='Windows' else ''
                require(files['artifacts/runner-readiness-ten-project-pass/bin/playtestr'+suffix]==runner['copied_sha256'],'different actual runner')
            if identity in {journey['capture_attempt'],journey['ordinary_attempt']}:
                interpreter='artifacts/runner-readiness-ten-project-pass/active/frogmouth/venv/'+('Scripts/python.exe' if host=='Windows' else 'bin/python')
                require(files[interpreter]==runtime['python_sha256'],'actual interpreter differs')
                require(files['artifacts/runner-readiness-ten-project-pass/active/frogmouth/'+build['launcher_relative_path']]==build['launcher_sha256'],'actual installed launcher differs')
                for name in seed:
                    relative=(package/'fixture'/name).relative_to(packet).as_posix()
                    require(files['artifacts/runner-readiness-ten-project-pass/'+relative]==sha256(package/'fixture'/name),'actual prelaunch fixture bytes not bound')
        spec=package/'spec.json';contract=load(spec)
        require(sha256(spec)==journey['spec_sha256'] and contract['command'][0]=='frogmouth','changed public contract')
        require(contract['command']==['frogmouth','.' if args.controls==16 else 'alpha.md'],'unreviewed first-use launch route')
        actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps'] if s.get('state',{}).get('kind')=='file'}
        require(actual==expected,'independent saved-byte oracle differs')
        for name,value in seed.items():require((package/'fixture'/name).read_bytes()==value,'actual first-use fixture differs')
        snapshot=next(s['snapshot'] for s in contract['steps'] if 'snapshot' in s)
        selected=load(package/'snapshots'/snapshot);screen=selected['text']
        require(selected['snapshot_version']==1 and selected['first_row']==4 and selected['last_row']==26,'wrong explicit row scope')
        require(screen.count('Beta body independent source.')==1 and 'Second section' in screen and 'Alpha body independent source.' not in screen,'nondefault document screenshot differs')
        entries=next(s['state']['entries'] for s in contract['steps'] if s.get('state',{}).get('kind')=='entries')
        require(set(entries)==set(seed),'first-use preserved directory entries differ')
        report=load(package/'ordinary-results.json')
        require(report['runner_version']=='source-'+source and report['summary']==dict(total=1,passed=1,failed=0,cancelled=0,not_run=0),'wrong ordinary result')
        result=report['results'][0]
        require(result['status']=='passed' and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'ordinary cleanup incomplete')
        for step in result['steps']:
            if 'state' in step:require(step['state']['invocation_id']==result['invocation_id'] and step['state']['workspace_id']==result['workspace']['id'],'cross-execution state')
        removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
        require(removed['removed'] and removed['owned_relative_path']=='active/frogmouth' and removed['source_archive_sha256']==ARCHIVE,'source cleanup unconfirmed')
        require(prepared['managed_cleanup_verified'] and prepared['runtime_processes_verified'],'runtime cleanup unconfirmed')
        for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'selected restore changed')
        cells.append(dict(host=host,runner_sha256=runner['copied_sha256'],journey_sha256=sha256(journeys[0]),
            spec_sha256=sha256(spec),cleanup_sha256=sha256(retained/'removed.json')))
    immutable_json(docs/('first-use-native-'+args.run+'.json'),dict(run=args.run,cells=cells,source_revision=source,
        recorder_controls=args.controls,shell_invocations=3,development_admission=False,human_usability='unmeasured',claim='First route only; twenty scenarios and faults remain open.'))
    print('Verified actual Frogmouth first-use source, commands, selected screen, exact saved bytes and cleanup on Linux/Windows.')


if __name__=='__main__':main()
