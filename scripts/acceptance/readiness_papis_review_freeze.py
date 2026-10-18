"""Review actual native Papis authoring packets before publishing any freeze."""
import argparse
import base64
import json
from pathlib import Path
import shutil

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load
from readiness_papis_cases import rows, plan_hash
from readiness_papis_verify_first_use import PIN, ARCHIVE, require


def declared_steps(controls):
    steps=[]
    for control in controls:
        action,_,value=control.partition(' ')
        if action=='/screen':continue
        if action=='/text':steps.append(dict(text=json.loads(value)))
        elif action=='/exit':steps.append(dict(exit=int(value)))
        elif action=='/resize':
            width,height=map(int,value.split());steps.append(dict(resize=dict(width=width,height=height)))
        elif action=='/redraw':steps.append(dict(wait_for_redraw=True))
        else:steps.append({{'/expect':'expect','/absent':'expect_not','/key':'key','/snapshot':'snapshot'}[action]:value})
    return steps


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--source-revision',default='3d50d81aae8f1d24f7a718e6e05b39069697b1a6');args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native run')
    source=args.source_revision;require(len(source)==40 and all(c in '0123456789abcdef' for c in source),'invalid source revision')
    run=RAW/'native'/args.run;metadata=load(run/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2 and all(j['conclusion']=='success' for j in metadata['jobs']),'native freeze jobs incomplete or failed')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/papis';source_review=load(docs/'source-review.json');cells=[]
    for host in ['Linux','Windows']:
        packet=run/('playtestr-'+host);ledger=object.__new__(Campaign);ledger.raw=packet;attempts=ledger.attempts()
        runner=load(packet/'papis-native-runner.json');retained=packet/'papis/retained-source';build=load(retained/'build.json')
        freeze=load(packet/'papis/reviewed-contract-freeze.json');package=packet/'papis/contracts'
        require(runner['source_revision']==source and runner['candidate_sha256']==runner['copied_sha256']==freeze['runner_sha256'],'wrong actual frozen runner')
        require(build['pin']==PIN and load(retained/'verified-index.json')['archive_sha256']==ARCHIVE,'wrong acquired source')
        require(freeze['target_build_sha256']==sha256(retained/'build.json'),'changed target build')
        require(freeze['normal_scenarios']==8 and freeze['edge_scenarios']==12 and set(freeze['contracts'])=={r['id']+'.json' for r in rows()},'wrong declared breadth')
        for name,digest in freeze['all_package_inputs'].items():require(sha256(package/name)==digest,'actual frozen input changed or missing')

        def witness(identity):
            events=attempts[identity];finished=events['finished']
            require('launched' in events and events['started']['expected_exit']==0 and finished['category']=='passed' and finished['exit_code']==0,'command lacks actual successful launch/outcome')
            require(finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'],'command cleanup unconfirmed')
            ref=events['identified']['identity'];manifest=packet_file(packet,ref['manifest'],1024**2)
            require(sha256(manifest)==ref['sha256'],'prelaunch identity changed')
            console=packet_file(packet,events['started']['project']+'/'+identity+'/console.log',4*1024**2)
            require(sha256(console)==finished['console_sha256'],'actual command output changed')
            return load(manifest)['files']

        def result_ok(result):
            require(result['status']=='passed' and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'scenario result or cleanup incomplete')
            for step in result['steps']:
                if 'state' in step:require(step['state']['invocation_id']==result['invocation_id'] and step['state']['workspace_id']==result['workspace']['id'],'cross-execution state')

        for row in rows(host.lower()):
            approvals=[]
            for path in (packet/'papis/authoring'/row['id']).glob('*/approved.json'):
                if load(path)['plan_sha256']==plan_hash(row):approvals.append(path)
            require(len(approvals)==1,'missing or ambiguous native approved current plan')
            approval_path=approvals[0];approval=load(approval_path);spec=approval_path.parent/'spec.json';contract=load(spec)
            require(sha256(spec)==approval['spec_sha256'],'public export changed')
            require(contract['steps'][:len(declared_steps(row['actions']))]==declared_steps(row['actions']),'public actions differ from declared workflow')
            require(len(contract['steps'])==len(declared_steps(row['actions']))+len(row['expected'])+len(row['missing'])+len(row['entry_sets']),'unexpected extra public steps')
            states={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps'] if s.get('state',{}).get('kind')=='file'}
            require(states==row['expected'],'independent native exact-byte oracle differs')
            require({s['state']['path'] for s in contract['steps'] if s.get('state',{}).get('kind')=='absent'}==set(row['missing']),'absence oracle differs')
            entries={s['state']['path']:sorted(s['state']['entries']) for s in contract['steps'] if s.get('state',{}).get('kind')=='entries'}
            require(entries==row['entry_sets'],'independent nested entry sets differ')
            for name,value in row['files'].items():require((spec.parent/'fixture'/name).read_bytes()==value,'actual seeded fixture differs')
            for identity in [approval['capture'],approval['ordinary']]:
                inputs=witness(identity);suffix='.exe' if host=='Windows' else ''
                require(inputs['artifacts/runner-readiness-ten-project-pass/bin/playtestr'+suffix]==runner['copied_sha256'],'actual runner differs')
                for name,digest in source_review['reviewed_inputs'].items():
                    if name.endswith('.py') or name=='pyproject.toml':require(inputs['artifacts/runner-readiness-ten-project-pass/active/papis/src/'+name]==digest,'actual editable source differs')
                for name in row['files']:
                    path=spec.parent/'fixture'/name;relative=path.relative_to(packet).as_posix()
                    require(inputs['artifacts/runner-readiness-ten-project-pass/'+relative]==sha256(path),'prelaunch fixture not bound')
            ordinary=spec.parent/'ordinary-results.json'
            require(sha256(ordinary)==approval['report_sha256'],'changed ordinary report');result_ok(load(ordinary)['results'][0])
            native=load(package/(row['id']+'.json'))
            require(native['steps']==contract['steps'] and native['command']==contract['command'] and native['env']==contract['env'],'assembly changed public actions, command or environment')
            require(native['command']==['papis','--config','config.ini','--lib','library','--np','1','--color','no','--set','exporter-csv-keys',"['title','year']",*row['args']],'unreviewed target command')
            require(native['env']==dict(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',TERM='xterm-256color'),'unreviewed environment')
            if row['snapshot']:
                snapshot=next(s['snapshot'] for s in native['steps'] if 'snapshot' in s)
                screen=(package/'snapshots'/snapshot).read_text(encoding='utf-8-sig')
                require(screen.count('|Beta Book')==1 and screen.count('2/2  F1:help')==1 and ' Alpha Book' in screen,'independent nondefault selection screenshot differs')
        witness(freeze['ordinary_parent'])
        reports=list((packet/'papis/suites').glob('*/results.json'));require(len(reports)==1,'ambiguous full-suite report')
        report=load(reports[0]);require(sha256(reports[0])==freeze['ordinary_report_sha256'],'frozen full report changed')
        require(report['runner_version']=='source-'+source and report['summary']==dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'full ordinary suite incomplete')
        require({Path(r['spec_path'].replace('\\','/')).name for r in report['results']}==set(freeze['contracts']),'full selection differs')
        suites=[identity for identity,events in attempts.items() if events['started']['label']=='public-recorded-suite'];require(len(suites)==1,'ambiguous ordinary suite witness')
        inputs=witness(suites[0])
        for name,digest in freeze['all_package_inputs'].items():require(inputs['artifacts/runner-readiness-ten-project-pass/papis/contracts/'+name]==digest,'actual suite payload not bound')
        for result in report['results']:result_ok(result)
        removed=load(retained/'removed.json');require(removed['removed'] and removed['source_archive_sha256']==ARCHIVE,'source removal unconfirmed')
        cells.append(dict(host=host,freeze_sha256=sha256(packet/'papis/reviewed-contract-freeze.json'),report_sha256=sha256(reports[0]),runner_sha256=runner['copied_sha256']))
    require(not (docs/'contracts').exists() and not (docs/'reviewed-contract-freeze.json').exists(),'curated native freeze already published')
    shutil.copytree(run/'playtestr-Linux/papis/contracts',docs/'contracts')
    shutil.copyfile(run/'playtestr-Linux/papis/reviewed-contract-freeze.json',docs/'reviewed-contract-freeze.json')
    windows=docs/'native-profiles/windows';windows.mkdir(parents=True)
    shutil.copytree(run/'playtestr-Windows/papis/contracts',windows/'contracts')
    shutil.copyfile(run/'playtestr-Windows/papis/reviewed-contract-freeze.json',windows/'reviewed-contract-freeze.json')
    immutable_json(docs/'native-authoring-review.json',dict(run=args.run,cells=cells,source_revision=source,
        public_contract_freeze_sha256=sha256(docs/'reviewed-contract-freeze.json'),fault_selection='None selected before independent native freeze review.',development_admission=False,final_archive_credit=False))
    print('Independently reviewed both native Papis twenty-case freezes before source fault selection.')


if __name__=='__main__':main()
