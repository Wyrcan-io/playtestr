"""Audit the real Windows startup miss, then declare only its full replacement."""
import argparse
import json

from next20_check import RAW, ROOT, DOC
from next20_packet_archive import archive_path,verify
from next20_verify_jrnl import json_payloads,require
from readiness_evidence import immutable_json,sha256


def audit():
    root=RAW/'yo/retained-native-v4';index=json.loads((root/'index.json').read_text())
    require(index['compression']=='tar.xz' and index['runs']==['40305371634'] and sha256(archive_path(root,index))==index['archive_sha256'],'wrong partial Windows packet')
    verify(archive_path(root,index),index['files']);data=json_payloads(root,index)
    prefix='native/40305371634/next20-yo-Windows/'
    provider=data['native/40305371634/run-metadata.json']
    require(provider['headSha']=='f0addebb2cdb8082072022b7b99a9fec47cb2641' and provider['conclusion']=='failure','partial Windows provider identity differs')
    jobs=[j for j in provider['jobs'] if 'windows-2025' in j['name']]
    require(len(jobs)==1 and jobs[0]['conclusion']=='failure','partial Windows job differs')
    steps={s['name']:s['conclusion'] for s in jobs[0]['steps']}
    require(all(steps[f'Final fresh-state batch {i+1} of twelve']=='success' for i in range(11)) and steps['Final fresh-state batch 12 of twelve']=='failure','partial Windows batch boundary differs')
    require(steps['Checked Windows source and runtime removal']==steps['Canonical registry source duplicate reference']=='success','partial Windows native cleanup/source closure incomplete')
    reports={n:v for n,v in data.items() if n.startswith(prefix+'yo/final-series/') and n.endswith('.report.json')}
    require(len(reports)==221,'partial Windows original report denominator differs')
    invocations=set();passed=0
    for report in reports.values():
        require(report['runner_version']=='v0.4.0-rc.5' and report['os']=='windows' and report['report_version']==3 and len(report['results'])==1,'wrong partial native report')
        row=report['results'][0]
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations and row['workspace']['cleaned'] and row['cleanup']['confirmed_exited'],'duplicate or unclean partial Windows report')
        invocations.add(row['invocation_id'])
        if row['status']=='passed':require(all(s['status']=='passed' for s in row['steps']),'nonpositive partial passed report');passed+=1
    failed=reports[prefix+'yo/final-series/11/N01.report.json']['results'][0]
    contract=data[prefix+'yo/final-series/11/contracts/normal-project.json']
    require(passed==220 and failed['status']=='failed' and failed['failure']['category']=='assertion_timeout' and 'waiting for first output' in failed['failure']['message'],'actual startup failure differs')
    require(contract['startup_timeout_ms']==2000 and all(s['status']=='not_run' for s in failed['steps']) and failed['cleanup']['forced'],'startup failure reached actions or was not bounded/cleaned')
    predecessor=reports[prefix+'yo/final-series/10/N01.report.json']['results'][0]
    require(predecessor['status']=='passed' and predecessor['steps'][0]['duration_ms']>2000,'prior actual readiness evidence does not substantiate short variant miss')
    immutable_json(root/'startup-audit.json',dict(schema_version=1,run='40305371634',host='windows',
        index_sha256=sha256(root/'index.json'),archive_sha256=index['archive_sha256'],compression='tar.xz',
        actual_reports=221,passed=220,failed=1,confirmed_individual_cleanups=221,
        failed_report_sha256=index['files'][prefix+'yo/final-series/11/N01.report.json']['sha256'],
        predecessor_ready_ms=predecessor['steps'][0]['duration_ms'],failed_duration_ms=failed['duration_ms'],
        native_source_runtime_removed=True,qualification_credit=0,calibration_credit=0,
        scope='Accurate bounded failure of self-imposed2s startup variant, before any action. Ordinary step/run budgets and runner executable unchanged. This Windows cell is incomplete; retain all220passes and failure without qualification.'))
    print('Audited partial Windows cell:220passes+one accurate2s startup failure; all221cleanups confirmed, source/runtime removed; zero qualification.')


def declare():
    package=DOC/'yo';current=package/'final-series-declaration.json';previous=json.loads(current.read_text())
    require(previous['revision']==2,'preserve existing startup replacement declaration')
    root=RAW/'yo/retained-native-v4';failure=json.loads((root/'startup-audit.json').read_text())
    require(json.loads((root/'expanded-removed.json').read_text(encoding='utf-8-sig'))['all_expanded_removed'],'partial Windows expansion must be checked-removed first')
    immutable_json(package/'final-series-declaration-v2.json',previous)
    require(sha256(package/'final-series-declaration-v2.json')==sha256(current),'original revision2 bytes differ')
    immutable_json(package/'windows-startup-disposition.json',dict(failure,previous_declaration_sha256=sha256(current),
        replacement='Full fresh Windows12-batch series with predeclared5000ms startup variant. Linux completed240ordinary+10calibrations and is carried by exact source/run/declaration; no repeat of its passing cell.',
        unchanged='All87canonicalinputs, file/screen oracles, normal10000ms step and120000ms run limits, targetsourcepin and exact runner archives. No production deadline or runner change.',
        limitation='Two-second startup did not hold on this actual hosted Windows run; do not claim that boundary.'))
    replacement=dict(previous,revision=3,retained_generations=dict(linux=3,windows=5),
        authoring='Public first3invocations/16controls; separate JavaScript+snapshot technical3/19. Prepared familiar operator, no human beginner measurement. Earlier copied narrative totals were incorrect; original yo measurement receipts are unchanged.',
        startup_timeout_ms_by_host=dict(linux=2000,windows=5000),
        accepted_prior_cells=dict(linux=dict(run='40305371634',source_revision='f0addebb2cdb8082072022b7b99a9fec47cb2641',
            declaration_file='final-series-declaration-v2.json',declaration_sha256=sha256(current),generation=3)),
        replacement_reason='Windows-only full replacement after accurate optional2s startup-variant failure; accepted Linux cell preserved exactly. No partial Windows report reused for qualification.',
        evidence_encoding='Existingv1/v2/v3 gzip archives unchanged. Partialv4 and freshv5 use explicitly recorded self-contained tar.xz with the same logical payload/hash contract and bounded codec memory/stream. Local records use their separately verified bounded XZ packet.')
    replacement['retention_plan']='Retain rejectedv1/v2, accepted Linuxv3, partial Windowsv4, fresh Windowsv5, exact local XZ records and mandatory once-retained canonical source; all-generation64MiB gate remains.'
    replacement['batches'][-1]=dict(replacement['batches'][-1],change='Explicit startup limit: Linux2000ms in accepted prior cell, Windows5000ms in complete fresh replacement. Ordinary10s step/120s run limits unchanged.')
    replacement['dispatch_budget']=dict(replacement['dispatch_budget'],standard_jobs=1,
        max_simultaneous_target_jobs=1,total_job_minute_ceiling=65,estimated_minutes=dict(windows=35),
        carried_linux_new_jobs=0)
    current.write_text(json.dumps(replacement,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    source=ROOT/'.github/workflows/runner-readiness-next20-yo.yml';workflow=source.read_text()
    linux='''          - os: ubuntu-24.04
            host: linux
            target: linux-amd64
            archive_target: linux_amd64
            extension: tar.gz
'''
    require(workflow.count(linux)==1,'reviewed original native matrix changed')
    workflow=workflow.replace(linux,'').replace('Next twenty yo exact archive series','Next twenty yo Windows startup replacement')
    workflow=workflow.replace('runner-readiness-next20-yo.yml','runner-readiness-next20-yo-windows.yml').replace('group: playtestr-next20-yo','group: playtestr-next20-yo-windows').replace('max-parallel: 2','max-parallel: 1')
    destination=source.with_name('runner-readiness-next20-yo-windows.yml')
    require(not destination.exists(),'preserve existing Windows replacement workflow')
    destination.write_text(workflow,encoding='utf-8',newline='\n')
    print('Declared complete Windows-only revision3; exact successful Linux cell carried, all87canonical inputs unchanged.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['audit','declare']);args=parser.parse_args()
    audit() if args.operation=='audit' else declare()
