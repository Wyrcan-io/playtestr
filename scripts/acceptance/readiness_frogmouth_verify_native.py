"""Independently verify frozen Frogmouth native executions, faults and maintenance."""
import argparse
import base64
from pathlib import Path
import shutil

from readiness_evidence import RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_file,read_json as load
from readiness_papis_verify_native import verifier,result_ok
from readiness_frogmouth_first_use import ADDRESS_FOCUS_BORDER,SOURCE,fixture_files
from readiness_frogmouth_verify_first_use import PIN,ARCHIVE,require

def verify_faults(packet,docs,profile,runtime,build,runner_sha,host,witness,original):
    summaries=list((packet/'frogmouth/faults').glob('*/summary.json'));require(len(summaries)==1,'ambiguous source fault batch')
    summary=summaries[0];data=load(summary);faults=data['faults']
    require(len(faults)==3 and {r['id'] for r in faults}=={'F01','F02','F04'} and data['runner_sha256']==runner_sha,'fault coverage/runner differs')
    require(data['interpreter_sha256']==runtime['python_sha256'],'fault interpreter differs')
    selected=load(docs/'fault-selection-revision-2.json');review={r['id']:r for r in load(docs/'source-fault-review-revision-2.json')['faults']}
    actual_selection=load(summary.parent/'selected-faults.json')
    require(actual_selection['frozen_contract_sha256']==sha256(docs/'reviewed-contract-freeze.json') and actual_selection['native_freeze_sha256']==sha256(profile/'reviewed-contract-freeze.json'),'faults belong to another freeze')
    require(actual_selection['original_heldout']==original and actual_selection['selection_revision']==2,'original selection reused, missing or wrong revision')
    runner_key='artifacts/runner-readiness-ten-project-pass/bin/playtestr'+('.exe' if host=='Windows' else '')
    interpreter='artifacts/runner-readiness-ten-project-pass/active/frogmouth/venv/'+('Scripts/python.exe' if host=='Windows' else 'bin/python')
    launcher='artifacts/runner-readiness-ten-project-pass/active/frogmouth/'+build['launcher_relative_path']
    for fault in faults:
        declaration=next(r for r in selected['faults'] if r['id']==fault['id'])
        require(all(fault[k]==declaration[k] for k in ['path','spec','before','after','category']),'actual source fault differs from declaration')
        require(all(fault[k]==review[fault['id']][k] for k in ['path','original_source_sha256','mutated_source_sha256']),'complete source byte mutation differs')
        require(fault['held_out']==bool(original and fault['id']=='F04') and fault['restored_exact'],'heldout reuse or restoration absent')
        source='artifacts/runner-readiness-ten-project-pass/active/frogmouth/src/'+fault['path']
        for phase,expected,digest,key in [('baseline',0,fault['original_source_sha256'],'baseline_attempt'),('mutated',1,fault['mutated_source_sha256'],'mutation_attempt'),('restored',0,fault['original_source_sha256'],'restored_attempt')]:
            inputs=witness(fault[key],expected)
            require(inputs[source]==digest and inputs[runner_key]==runner_sha and inputs[interpreter]==runtime['python_sha256'] and inputs[launcher]==build['launcher_sha256'],'actual source/runner/runtime/launcher differs')
            require(inputs['artifacts/runner-readiness-ten-project-pass/frogmouth/host-contracts/'+fault['spec']]==sha256(profile/'contracts'/fault['spec']),'frozen fault contract not bound')
            report=load(summary.parent/(fault['id']+'-'+phase+'.json'));require(report['runner_version']=='source-'+SOURCE,'fault runner source differs')
            result=report['results'][0];result_ok(result,'failed' if expected else 'passed')
            if expected:require(result['failure']['category']==fault['category'],'wrong real fault diagnosis')
            if fault['id']=='F04' and phase=='mutated':
                failed=next(i for i,s in enumerate(result['steps']) if s['status']=='failed');prior=result['steps'][:failed]
                require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior},'F03 lacks prior passing screen and exact exit')
                state=result['steps'][failed]['state'];require(state['kind']=='file' and state['path']=='beta.md','wrong saved-state rejection')
                if SOURCE!='f46f2409985af077fd29723ab963d24792eabbbe':
                    reference=result['evidence']['screen_path'].replace('\\','/')
                    prefix='artifacts/runner-readiness-ten-project-pass/'
                    require(reference.startswith(prefix),'unsafe failure screen reference')
                    screen=packet_file(packet,reference.removeprefix(prefix),4*1024**2).read_text(encoding='utf-8-sig')
                    require(screen.count('Beta body independent source.')==1,'R3-11 final useful TUI frame remains missing')
        for phase,digest in [('mutation_validation',fault['mutated_source_sha256']),('restored_validation',fault['original_source_sha256'])]:
            validation=fault[phase]
            require(validation['source_sha256']==digest and validation['interpreter_sha256']==runtime['python_sha256'],'validation source/runtime receipt differs')
            for event in [validation['syntax_attempt'],validation['version_attempt']]:
                inputs=witness(event);require(inputs[source]==digest and inputs[interpreter]==runtime['python_sha256'],'actual syntax/version source/runtime differs')
    return summary


def verify_maintenance(packet,contracts,witness):
    paths=list((packet/'frogmouth').glob('maintenance*/journey.json'));require(len(paths)==1,'ambiguous maintenance batch')
    path=paths[0];journey=load(path);package=path.parent/'package'
    require(len(journey['attempts'])==12 and journey['maintained_spec_sha256']==journey['relocated_spec_sha256'],'maintenance incomplete')
    for row in journey['attempts']:witness(row['id'],1 if row['label'].startswith('intended-') else 0)
    for label,category in [('intended-file-change','state_assertion_failure'),('intended-width-change','snapshot_mismatch')]:
        report=load(path.parent/(label+'.json'));require(report['runner_version']=='source-'+SOURCE,'maintenance runner differs');result=report['results'][0]
        result_ok(result,'failed');require(result['failure']['category']==category,'wrong intended maintenance diagnosis')
    original=load(contracts/'N01.json');updated=load(package/'N01.json')
    index=next(i for i,s in enumerate(original['steps']) if s.get('state',{}).get('path')=='sentinel.bin')
    require(base64.b64decode(updated['steps'][index]['state']['bytes_base64'])==b'reviewed sentinel revision two\x00\r\n','selected bytes differ')
    updated['steps'][index]=original['steps'][index]
    require(updated['width']==104,'unreviewed width change');updated['width']=original['width']
    focus=next(i for i,s in enumerate(original['steps']) if s.get('expect')==ADDRESS_FOCUS_BORDER)
    require(updated['steps'][focus]['expect']=='\u250f'+'\u2501'*102+'\u2513','focus anchor differs from declared new width')
    updated['steps'][focus]=original['steps'][focus];require(updated==original,'maintenance changed unrelated public contract')
    snapshot=next(s['snapshot'] for s in original['steps'] if 'snapshot' in s)
    review=load(path.parent/'selected-screen-review.json')
    require(review['original']==load(contracts/'snapshots'/snapshot) and review['updated']==load(package/'snapshots'/snapshot),'screen review differs from actual baseline bytes')
    require(review['original_width']==100 and review['updated_width']==104 and review['updated']['text'].count('Beta body independent source.')==1,'selected new screen identity differs')
    # Independent review checks content order; the actual public snapshot remains
    # exact, including every structural glyph and space at its declared width.
    content=lambda text:''.join(c for c in text if not c.isspace() and not 0x2500<=ord(c)<=0x259f)
    require(content(review['original']['text'])==content(review['updated']['text']),'width maintenance changed document content')
    suffix=load(package/'rerecorded-suffix.json');expected={**fixture_files(),'sentinel.bin':b'reviewed sentinel revision two\x00\r\n','gamma.md':b'# Gamma guide\n\nGamma corrected suffix destination.\n'}
    actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in suffix['steps'] if s.get('state',{}).get('kind')=='file'}
    require(actual==expected and not any(s.get('text')=='beta.md' for s in suffix['steps']) and sum(s.get('key')=='Enter' for s in suffix['steps'])==1,'wrong-document suffix survived or saved oracle differs')
    entries=next(s['state']['entries'] for s in suffix['steps'] if s.get('state',{}).get('kind')=='entries')
    require(len(entries)==len(expected) and set(entries)==set(expected),'suffix directory set differs')
    require(sha256(package/'N01.json')==journey['maintained_spec_sha256'] and sha256(path.parent/'relocated \u96ea route/N01.json')==journey['relocated_spec_sha256'],'relocation changed maintained bytes')
    require(sha256(path.parent/'generated-workflow.yml')==journey['generated_workflow_sha256'] and journey['generated_workflow_execution'] is False,'workflow preparation identity/claim differs')
    return path


def main():
    global SOURCE
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--source-revision',default=SOURCE);parser.add_argument('--replicas',action='store_true');args=parser.parse_args()
    SOURCE=args.source_revision
    require(len(SOURCE)==40 and all(c in '0123456789abcdef' for c in SOURCE),'invalid runner source revision')
    require(args.run.isascii() and args.run.isdecimal() and len(args.run)<=20,'invalid native run ID')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/frogmouth';run=RAW/'native'/args.run;metadata=load(run/'run-metadata.json')
    series=load(docs/'current-qualification-series.json')
    current=load(docs/'current-source-requalification.json') if args.replicas else series
    require(args.run==current['native_run'],'wrong original/requalification native series')
    require(series['original_heldout']==dict(host='Linux',fault='F04') and series['freeze_commit']=='b393fc1afb8814ac6db6ff40ffc844f15f0816a8','wrong original holdout/freeze binding')
    expected_commit=current['tooling_commit'] if args.replicas else series['declaration_commit']
    require(not args.replicas or current['runner_source']==SOURCE,'wrong requalified runner source')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and metadata['headSha']==expected_commit and len(metadata['jobs'])==2 and all(j['conclusion']=='success' for j in metadata['jobs']),'native qualification failed/incomplete or wrong committed declaration')
    cells=[]
    for host in ['Linux','Windows']:
        packet=run/('playtestr-'+host);attempts,witness=verifier(packet);profile=docs/'native-profiles/windows' if host=='Windows' else docs
        freeze=load(profile/'reviewed-contract-freeze.json');contracts=packet/'frogmouth/host-contracts'
        for name,digest in freeze['all_package_inputs'].items():require(sha256(contracts/name)==digest,'frozen payload changed/missing')
        runner=load(packet/'frogmouth-native-runner.json');require(runner['source_revision']==SOURCE and runner['candidate_sha256']==runner['copied_sha256'],'runner differs')
        retained=packet/'frogmouth/retained-source';runtime=load(retained/'runtime.json');build=load(retained/'build.json')
        require(build['pin']==runtime['source_pin']==PIN,'target pin differs')
        reports=list((packet/'frogmouth/suites').glob('*/results.json'));require(len(reports)==1,'ambiguous ordinary suite')
        report_path=reports[0];report=load(report_path)
        require(report['runner_version']=='source-'+SOURCE and report['summary']==dict(total=20,passed=20,failed=0,cancelled=0,not_run=0),'ordinary twenty-suite incomplete')
        require({Path(r['spec_path'].replace('\\','/')).name for r in report['results']}==set(freeze['contracts']),'suite selection differs')
        suites=[identity for identity,event in attempts.items() if event['started']['label']=='public-recorded-suite'];require(len(suites)==1,'ambiguous suite invocation')
        inputs=witness(suites[0]);suffix='.exe' if host=='Windows' else ''
        require(inputs['artifacts/runner-readiness-ten-project-pass/bin/playtestr'+suffix]==runner['copied_sha256'],'ordinary runner bytes not bound')
        require(inputs['artifacts/runner-readiness-ten-project-pass/active/frogmouth/'+build['launcher_relative_path']]==build['launcher_sha256'],'ordinary launcher not bound')
        require(inputs['artifacts/runner-readiness-ten-project-pass/active/frogmouth/venv/'+('Scripts/python.exe' if host=='Windows' else 'bin/python')]==runtime['python_sha256'],'ordinary interpreter not bound')
        for name,digest in freeze['all_package_inputs'].items():require(inputs['artifacts/runner-readiness-ten-project-pass/frogmouth/host-contracts/'+name]==digest,'ordinary frozen payload not bound')
        for result in report['results']:result_ok(result,'passed')
        summary=verify_faults(packet,docs,profile,runtime,build,runner['copied_sha256'],host,witness,not args.replicas and host=='Linux')
        maintenance=verify_maintenance(packet,contracts,witness)
        removed=load(retained/'removed.json');index=load(retained/'verified-index.json')
        require(removed['removed'] and removed['owned_relative_path']=='active/frogmouth' and removed['source_archive_sha256']==ARCHIVE==index['archive_sha256'],'source cleanup/archive differs')
        for name in index['selected_restore']:require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'selected source restore differs')
        cells.append(dict(host='playtestr-'+host,run=args.run,scenarios=20,runner_sha256=runner['copied_sha256'],report_sha256=sha256(report_path),source_fault_summary_sha256=sha256(summary),maintenance_sha256=sha256(maintenance),cleanup_receipt_sha256=sha256(retained/'removed.json')))
    historical=SOURCE=='f46f2409985af077fd29723ab963d24792eabbbe'
    output='historical-f46f240-verification.json' if historical else 'native-development-verification.json'
    immutable_json(RAW/'frogmouth'/output,dict(runner_source=SOURCE,cells=cells,real_faults=3,original_current_source_heldout=dict(run=series['native_run'],host='Linux',fault='F04'),original_fault_runner_source=series['current_source'],phase='development',evidence_repair_required=historical,final_archive_credit=False))
    if not args.replicas:
        original=list((run/'playtestr-Linux/frogmouth/faults').glob('*/summary.json'))[0]
        destination=docs/'original-source-faults';destination.mkdir(exist_ok=False)
        for name in ['summary.json','selected-faults.json','F01.patch','F02.patch','F04.patch']:shutil.copyfile(original.parent/name,destination/name)
    print('Verified both native suites, three actual source faults/restores, maintenance and cleanup; '+('historical R3-11 blank-screen gap remains unqualified.' if historical else 'final useful failure frames preserved.'))


if __name__=='__main__':main()
