"""Independently verify native first-use commands, bytes, source and cleanup."""
import argparse
import base64

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_papis_first_use import fixture_files

PIN='c744b5efe9b307b9664f3e96c154cb620e140a8f'
ARCHIVE='779244bd1231195ad95f744816175ad09a96ad0dc8d23122404656df0b80da3e'


def require(condition,message):
    if not condition:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--source-revision',default='f46f2409985af077fd29723ab963d24792eabbbe');args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    source=args.source_revision
    require(len(source)==40 and all(c in '0123456789abcdef' for c in source),'invalid source revision')
    run=RAW/'native'/args.run;metadata=load(run/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success','native first use failed or incomplete')
    require(len(metadata['jobs'])==2 and all(j['conclusion']=='success' for j in metadata['jobs']),'missing successful native jobs')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/papis'
    reviewed=load(docs/'source-review.json')['reviewed_inputs'];seed=fixture_files();cells=[]
    expected={'exported/info.yaml':seed['library/beta/info.yaml'],'exported/paper.txt':seed['library/beta/paper.txt'],
        'library/alpha/info.yaml':seed['library/alpha/info.yaml'],'library/beta/info.yaml':seed['library/beta/info.yaml'],
        'sentinel.txt':seed['sentinel.txt']}
    for host in ['Linux','Windows']:
        packet=run/('playtestr-'+host);ledger=object.__new__(Campaign);ledger.raw=packet;attempts=ledger.attempts()
        runner=load(packet/'papis-native-runner.json');retained=packet/'papis/retained-source'
        require(runner['source_revision']==source and runner['candidate_sha256']==runner['copied_sha256'],'wrong candidate')
        build=load(retained/'build.json');runtime=load(retained/'runtime.json');index=load(retained/'verified-index.json')
        require(build['pin']==runtime['source_pin']==PIN and index['archive_sha256']==ARCHIVE,'wrong upstream source')
        require(build['source_editable'] and load(retained/build['wheel_manifest'])==build['dependency_wheels'],'dependency manifest differs')
        journeys=list((packet/'papis/first-use').glob('*/journey.json'));require(len(journeys)==1,'ambiguous first-use journey')
        journey=load(journeys[0]);package=journeys[0].parent
        require(journey['shell_invocations']==3 and journey['recorder_controls']==16 and not journey['handwritten_playtestr_json'],'wrong route count')
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
                    require(files['artifacts/runner-readiness-ten-project-pass/active/papis/src/'+name]==digest,'different actual editable source')
            if identity in journey['attempts']:
                suffix='.exe' if host=='Windows' else ''
                require(files['artifacts/runner-readiness-ten-project-pass/bin/playtestr'+suffix]==runner['copied_sha256'],'different actual runner')
            if identity in {journey['capture_attempt'],journey['ordinary_attempt']}:
                for name in seed:
                    relative=(package/'fixture'/name).relative_to(packet).as_posix()
                    require(files['artifacts/runner-readiness-ten-project-pass/'+relative]==sha256(package/'fixture'/name),'actual prelaunch fixture bytes not bound')
        spec=package/'spec.json';contract=load(spec)
        require(sha256(spec)==journey['spec_sha256'] and contract['command'][0]=='papis','changed public contract')
        actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps'] if s.get('state',{}).get('kind')=='file'}
        require(actual==expected,'independent saved-byte oracle differs')
        for name,value in seed.items():require((package/'fixture'/name).read_bytes()==value,'actual first-use fixture differs')
        snapshot=next(s['snapshot'] for s in contract['steps'] if 'snapshot' in s)
        screen=(package/'snapshots'/snapshot).read_text(encoding='utf-8-sig')
        require(screen.count('|Beta Book')==1 and screen.count('2/2  F1:help')==1 and ' Alpha Book' in screen,'nondefault selection screenshot differs')
        report=load(package/'ordinary-results.json')
        require(report['runner_version']=='source-'+source and report['summary']==dict(total=1,passed=1,failed=0,cancelled=0,not_run=0),'wrong ordinary result')
        result=report['results'][0]
        require(result['status']=='passed' and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'ordinary cleanup incomplete')
        for step in result['steps']:
            if 'state' in step:require(step['state']['invocation_id']==result['invocation_id'] and step['state']['workspace_id']==result['workspace']['id'],'cross-execution state')
        removed=load(retained/'removed.json');prepared=load(retained/'removal-prepared.json')
        require(removed['removed'] and removed['owned_relative_path']=='active/papis' and removed['source_archive_sha256']==ARCHIVE,'source cleanup unconfirmed')
        require(prepared['managed_cleanup_verified'] and prepared['runtime_processes_verified'],'runtime cleanup unconfirmed')
        for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'selected restore changed')
        cells.append(dict(host=host,runner_sha256=runner['copied_sha256'],journey_sha256=sha256(journeys[0]),
            spec_sha256=sha256(spec),cleanup_sha256=sha256(retained/'removed.json')))
    immutable_json(docs/('first-use-native-'+args.run+'.json'),dict(run=args.run,cells=cells,source_revision=source,
        development_admission=False,human_usability='unmeasured',claim='First route only; twenty scenarios and faults remain open.'))
    print('Verified actual Papis first-use source, commands, selected screen, exact saved bytes and cleanup on Linux/Windows.')


if __name__=='__main__':main()
