"""Audit and curate both actual native twenty-case public Rclone exports."""
import argparse
import base64
import copy
import shutil

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_cases import plan_hash, serialise
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_rclone_cases import rows
from readiness_rclone_verify_first_use import require, verify_native


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'])
    args=parser.parse_args()
    first_route=verify_native(args.run,publish=False,hosts=[args.host] if args.host else None)
    run=RAW/'native'/args.run
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'
    review=load(docs/'source-review.json')
    candidate=load(docs.parent/'provisional-candidate-freeze.json')
    profiles=[]
    for artifact,host,suffix in [('Linux','linux',''),('Windows','windows','native-profiles/windows')]:
        if args.host and host!=args.host:continue
        packet=run/('playtestr-'+artifact)
        target=packet/'rclone'
        package=target/'contracts'
        frozen_path=target/'reviewed-contract-freeze.json'
        frozen=load(frozen_path)
        build=load(target/'retained-source/build.json')
        cell=next(r for r in first_route['cells'] if r['host']==host)
        installed=load(packet/'private-install/provisional-v1'/(host+'-amd64')/'installation.json')
        ledger=object.__new__(Campaign)
        ledger.raw=packet
        attempts=ledger.attempts()
        require(frozen['normal_scenarios']==8 and frozen['edge_scenarios']==12 and len(frozen['contracts'])==20
                and frozen['runner_sha256']==cell['runner_sha256']
                and frozen['provisional_archive_sha256']==cell['archive_sha256']
                and frozen['source_revision']==candidate['source_revision']
                and frozen['target_build_sha256']==sha256(target/'retained-source/build.json'),
                'native freeze scope/build differs')
        prefix='artifacts/runner-readiness-ten-project-pass/active/rclone/'

        def witness(identity):
            event=attempts[identity]
            finished=event['finished']
            require('launched' in event and event['started']['expected_exit']==0
                    and finished['category']=='passed' and finished['exit_code']==0
                    and finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'],
                    'actual command failed or cleanup unconfirmed')
            reference=event['identified']['identity']
            manifest=packet_file(packet,reference['manifest'],2*1024**2)
            require(sha256(manifest)==reference['sha256'],'prelaunch identity changed')
            inputs=load(manifest,maximum=2*1024**2)
            files=inputs['files']
            require({n[len(prefix+'src/'):]:digest for n,digest in files.items() if n.startswith(prefix+'src/')}
                    ==review['reviewed_inputs'],'actual original target source differs')
            require(files[prefix+build['binary_relative_path']]==build['binary_sha256']
                    and inputs['runtime_executables']['go']==build['compiler_sha256']
                    and files[installed['binary']]==cell['runner_sha256'],'actual target/compiler/runner differs')
            console=packet/event['started']['project']/identity/'console.log'
            require(sha256(console)==finished['console_sha256'],'actual command log changed')
            return files,console.read_text(encoding='utf-8-sig')

        def passed_report(report,total):
            require(report['runner_version']==candidate['version'] and report['summary']==
                    dict(total=total,passed=total,failed=0,cancelled=0,not_run=0),'ordinary denominator/version differs')
            require(len({r['invocation_id'] for r in report['results']})==total,'duplicated execution identities')
            for result in report['results']:
                require(result['status']=='passed' and result['cleanup']['confirmed_exited']
                        and result['workspace']['cleaned'],'result/process/workspace cleanup unconfirmed')
                for step in result['steps']:
                    require(step['status']=='passed','ordinary step incomplete')
                    if 'state' in step:
                        require(step['state']['invocation_id']==result['invocation_id']
                                and step['state']['workspace_id']==result['workspace']['id'],'state proof from another execution')

        require({p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()}
                ==set(frozen['all_package_inputs']),'missing/extra frozen package payload')
        for name,digest in frozen['all_package_inputs'].items():
            require(sha256(packet_file(package,name,1024**2))==digest,'frozen package payload changed')
        for row in rows(host):
            approval_path=target/'approved'/(row['id']+'.json')
            approval=load(approval_path)
            require(approval['plan_sha256']==plan_hash(row),'approved native scenario differs')
            bound=[r for r in frozen['approvals'] if r['id']==row['id']]
            require(len(bound)==1 and bound[0]['approval_sha256']==sha256(approval_path)
                    and bound[0]['plan_sha256']==plan_hash(row),'frozen approval binding differs')
            exported=packet_file(packet,approval['spec'].removeprefix('artifacts/runner-readiness-ten-project-pass/'),1024**2)
            require(sha256(exported)==approval['spec_sha256'],'original public export changed')
            require(load(exported.parent/'declared-plan.json')==serialise(row),'actual declared fixture/actions differ')
            original=load(exported)
            contract_path=package/(row['id']+'.json')
            contract=load(contract_path)
            require(sha256(contract_path)==frozen['contracts'][row['id']+'.json']
                    and contract['command']==['rclone','--config','rclone.conf','config'],'actual public spec/command differs')
            actions=copy.deepcopy(contract['steps'])
            renamed=bound[0]['reference_relocation']
            for step in actions:
                if 'snapshot' in step:
                    require(step['snapshot'] in renamed,'unexpected baseline relocation')
                    new=step['snapshot']
                    step['snapshot']=renamed[new]
                    require(sha256(package/'snapshots'/new)==sha256(exported.parent/'snapshots'/step['snapshot']),
                            'relocation changed a reviewed screen baseline')
            require(actions==original['steps'],'relocation changed actions or expected bytes')
            states=[s['state'] for s in contract['steps'] if 'state' in s]
            actual_files={s['path']:base64.b64decode(s['bytes_base64']) for s in states if s['kind']=='file'}
            entries={s['path']:s['entries'] for s in states if s['kind']=='entries'}
            require(actual_files==row['expected'] and {s['path'] for s in states if s['kind']=='directory'}==set(row['directories'])
                    and {n:sorted(v) for n,v in entries.items()}==row['entry_sets']
                    and all(len(v)==len(set(v)) for v in entries.values()),'independent saved-state oracle differs')
            absent=[(i,s['state']['path']) for i,s in enumerate(contract['steps']) if s.get('state',{}).get('kind')=='absent']
            require([name for _,name in absent]==row['initial_absent'],'initial absence proof differs')
            if absent:
                first_input=next(i for i,s in enumerate(contract['steps']) if any(k in s for k in ['text','key','resize']))
                require(all(i<first_input for i,_ in absent),'initial absence checkpoint moved after input')
            for name,value in row['files'].items():
                require((package/'fixtures'/row['id']/name).read_bytes()==value,'frozen native fixture differs')
            for identity in [approval['capture_attempt'],approval['ordinary_attempt']]:
                files,output=witness(identity)
                if identity==approval['capture_attempt']:
                    require('Exported ' in output and 'Recorder:' not in output,'public capture contains failed controls')
                else:
                    key='artifacts/runner-readiness-ten-project-pass/'+exported.relative_to(packet).as_posix()
                    require(files[key]==sha256(exported),'actual individual ordinary spec not bound')
                for name in row['files']:
                    path=exported.parent/'fixture'/name
                    key='artifacts/runner-readiness-ten-project-pass/'+path.relative_to(packet).as_posix()
                    require(files[key]==sha256(path),'actual individual input fixture not bound')
            report=exported.parent/'ordinary-result.json'
            require(sha256(report)==approval['report_sha256'],'individual ordinary result changed')
            passed_report(load(report),1)
        reports=[p for p in (target/'suites').glob('*/results.json') if sha256(p)==frozen['ordinary_report_sha256']]
        require(len(reports)==1,'missing or ambiguous full-suite result')
        report=load(reports[0])
        passed_report(report,20)
        require({r['spec_path'].replace('\\','/').split('/')[-1] for r in report['results']}==set(frozen['contracts']),
                'full-suite scenario set differs')
        witness(frozen['ordinary_parent'])
        full_calls=[identity for identity,event in attempts.items() if event['started']['label']=='public-recorded-suite']
        require(len(full_calls)==1,'ambiguous public full-suite execution')
        files,_=witness(full_calls[0])
        for name,digest in frozen['all_package_inputs'].items():
            require(files['artifacts/runner-readiness-ten-project-pass/rclone/contracts/'+name]==digest,
                    'actual full-suite inputs not bound')
        profiles.append(dict(host=host,suffix=suffix,package=package,freeze=frozen_path,
            report_sha256=sha256(reports[0]),cleanup_sha256=sha256(target/'retained-source/removed.json')))
    for profile in profiles:
        destination=docs/profile['suffix']
        require(not (destination/'contracts').exists() and not (destination/'reviewed-contract-freeze.json').exists(),
                'refuse to overwrite an existing reviewed native profile')
    cells=[]
    for profile in profiles:
        destination=docs/profile['suffix']
        destination.mkdir(parents=True,exist_ok=True)
        shutil.copytree(profile['package'],destination/'contracts')
        shutil.copyfile(profile['freeze'],destination/'reviewed-contract-freeze.json')
        cells.append(dict(host=profile['host'],architecture='amd64',freeze_sha256=sha256(destination/'reviewed-contract-freeze.json'),
            report_sha256=profile['report_sha256'],cleanup_sha256=profile['cleanup_sha256']))
    if args.host:
        immutable_json(docs/('native-authoring-review-'+args.host+'.json'),dict(run=args.run,cells=cells,
            metadata_sha256=sha256(run/'run-metadata.json'),source_commit=load(run/'run-metadata.json')['headSha'],
            scope='One independently audited native profile; no two-host admission.'))
        paths=[docs/('native-authoring-review-'+host+'.json') for host in ['linux','windows']]
        if not all(p.exists() for p in paths):
            print('One native twenty-case freeze audited; second native audit remains required.')
            return
        partials=[load(p) for p in paths]
        require(all(p['run']==args.run and p['metadata_sha256']==sha256(run/'run-metadata.json') for p in partials),
                'host audits belong to different runs or job metadata')
        cells=[c for p in partials for c in p['cells']]
        require({c['host'] for c in cells}=={'linux','windows'} and len(cells)==2,'incomplete audited host matrix')
        for c in cells:
            base=docs if c['host']=='linux' else docs/'native-profiles/windows'
            require(sha256(base/'reviewed-contract-freeze.json')==c['freeze_sha256'],
                    'previously audited host freeze changed')
            for name,digest in load(base/'reviewed-contract-freeze.json')['all_package_inputs'].items():
                require(sha256(packet_file(base/'contracts',name,1024**2))==digest,'previous host payload changed')
    immutable_json(docs/'native-authoring-review.json',dict(run=args.run,cells=cells,unique_scenarios=20,
        normal=8,edge=12,source_faults_selected=False,candidate_version=candidate['version'],final_archive_credit=0))
    print('Independently verified and curated both native Rclone twenty-case freezes before source fault selection.')


if __name__=='__main__':main()
