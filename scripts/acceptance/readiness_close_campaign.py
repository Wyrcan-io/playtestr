"""Close only the first runner batch after independently audited engineering gates."""
import argparse
import json
import subprocess

from readiness_closing_old_audit import DOC
from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import canonical_hashes, read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--harness-run',required=True);args=parser.parse_args()
    frozen=load(DOC/'migration-candidate-freeze.json');matrix=load(DOC/'final-matrix-audit.json')
    status=load(DOC/'final-series-status.json');old=load(DOC/'closing-old-archive-audit.json')
    require(frozen['source_revision']=='129b7a45c0006be550f798ce52c2fbbfd327e515' and frozen['version']=='v0.4.0-rc.5','unexpected candidate')
    for cell in frozen['cells']:require(sha256(ROOT/cell['archive_local_only'])==cell['archive_sha256'],'frozen native archive bytes changed')
    subprocess.run(['git','diff','--exit-code',frozen['source_revision'],'--','*.go','go.mod','go.sum'],cwd=ROOT,check=True,timeout=60)
    require((matrix['projects'],matrix['ordinary_executions'],matrix['calibration_executions'],matrix['native_cells'])==(10,4800,186,20)
        and len(matrix['controls'])==11 and all(c['refused'] for c in matrix['controls'])
        and matrix['candidate_freeze_sha256']==sha256(DOC/'migration-candidate-freeze.json')
        and matrix['actual_model_sha256']==sha256(RAW/'final-matrix-audit/actual-model.json'),'new matrix or challenged actual model differs')
    require((status['verified_series_projects'],status['verified_series_cells'],status['verified_ordinary_executions'],status['verified_calibration_executions'])==(10,20,4800,186),
        'incomplete final series')
    require((old['projects_verified'],old['canonical_scenarios'],old['primary_executions'],old['calibration_executions'],old['native_cells'])==(10,130,274,63,21),
        'old migration boundary incomplete')
    require(load(DOC/'all-old-attempt-accounting.json')['counts']==dict(ordinary=565,calibration=108,**{'prelaunch-invalid':3}),
        'all-old attempted denominator differs')
    core=load(DOC/'native-core-129b7a4.json');require(core['verified_success'] and core['source_revision']==frozen['source_revision']
        and set(core['native_hosts'])=={'linux','macos','windows'},'native source/race gate incomplete')
    previous=load(DOC/'old-control-matrix-revision-3.json');new=load(DOC/'new-control-development-evidence-revision-13.json')
    require(previous['count']==88 and previous['whole_controls_with_passing_applicable_evidence']==87
        and new['distinct_whole_controls']==33 and len({c['id'] for c in new['controls']})==33,'whole control scope differs')
    for control in new['controls']:require(control['current_source_sha256'] in canonical_hashes(ROOT/control['source']),
        'new whole control source changed: '+control['id'])
    for control in previous['controls']:require(control['current_canonical_source_sha256'] in canonical_hashes(ROOT/control['source']),
        'historical whole control source changed: '+control['id'])
    control_archives=[]
    for generation,host in enumerate(['linux','macos','windows'],1):
        receipt=load(DOC/('archive-controls-verified-'+host+'.json'))
        candidate=next(c for c in frozen['cells'] if c['host']==('darwin' if host=='macos' else host))
        require(receipt['observed']==35 and len({r['case'] for r in receipt['controls']})==35
            and receipt['runner_sha256']==candidate['binary_sha256'] and receipt['archive_sha256']==candidate['archive_sha256'],
            'exact public archive controls incomplete')
        folder=RAW/'product-controls'/('retained-native-v'+str(generation));index=load(folder/'index.json',maximum=4*1024**2)
        checked=load(folder/'verified.json');removed=load(folder/'expanded-removed.json')
        require(sha256(folder/'index.json')==checked['index_sha256']==removed['index_sha256']
            and sha256(folder/'packets.tar.gz')==index['archive_sha256']==checked['archive_sha256']==removed['archive_sha256']
            and removed['all_expanded_removed'] and any(r['sha256']==receipt['actual_results_sha256'] for r in index['files'].values()),
            'actual public control retention/removal changed')
        verify(folder/'packets.tar.gz',index['files'])
        control_archives.append(dict(host=host,index_sha256=sha256(folder/'index.json'),archive_sha256=index['archive_sha256']))
    for host in ['ubuntu-24.04','macos-15','windows-2025']:
        value=load(DOC/('closing-harness-'+host+'.json'))
        require(value['run']==args.harness_run and len(value['checks'])==2
            and next(c for c in value['checks'] if c['label']=='native-harness-controls')['tests_discovered']==64,
            'closing native harness gate incomplete')
    fresh=load(DOC/'fresh-checkout-verification.json');supplement=load(DOC/'fresh-public-closing.json')
    require(fresh['removed'] and supplement['removed'] and supplement['public_only'] and fresh['public_files']>2600
        and supplement['public_files']>=fresh['public_files'],'actual fresh checkout gate incomplete')
    for label in ['go-test','go-vet','demo-build','public-examples']:
        call=next(c for c in fresh['calls'] if c['label']==label);end=load(RAW/'events'/(call['attempt']+'-finished.json'))
        require(end['exit_code']==0 and end['category']=='passed' and not end['cleanup_errors'],'fresh source check did not pass')
    journal=load(DOC/'all-command-accounting.json')
    require(sha256(ROOT/journal['command_inventory_local_only'])==journal['command_inventory_sha256'],
        'actual command journal inventory changed')
    for unfinished in journal['incomplete_commands']:
        require(unfinished['label']=='closing-deduplicated-command-journal','unresolved current command envelope')
        end=load(RAW/'events'/(unfinished['id']+'-finished.json'))
        require(end['category']=='passed' and end['exit_code']==0,'journal audit did not complete after its observation')
    archive_files=['windows-migration-v2.json','linux-migration-v2.json','darwin-migration-v2.json',
        'windows-portable-uninstall.json','linux-portable-uninstall.json','darwin-portable-uninstall.json',
        'linux-process-offline.json','delivered-ci-verification.json']
    for name in archive_files:load(DOC/'archive-experience'/name)
    for host in ['windows','linux','darwin']:
        journey=load(DOC/'archive-experience'/(host+'-migration-v2.json'))
        candidate=next(c for c in frozen['cells'] if c['host']==host)
        require(journey['actual_commands']==19 and len(journey['cells'])==8 and journey['source_free_execution']
            and journey['current_archive_sha256']==candidate['archive_sha256']
            and journey['current_binary_sha256']==candidate['binary_sha256'],'native archive journey differs from candidate')
    for name in ['r3-batch-observations.json','r3-e11-batch-observations.json']:
        observations=load(DOC/'fff'/name);require(observations['observed']==observations['passed']==150
            and observations['failed']==0,'bounded FFF disposition missing')
    documents=load(DOC/'closing-document-audit.json')
    for name,digest in documents['files'].items():require(sha256(ROOT/name)==digest,'narrative changed after document audit: '+name)
    storage=load(DOC/'closing-storage.json')
    require(not storage['active_projects'] and all(storage[k]<=storage['caps'][k] for k in ['raw_bytes','retained_bytes','curated_bytes'])
        and all(p['bytes']<=p['cap_bytes'] for p in storage['projects']),'closing ownership/storage gate incomplete')
    lint=ROOT/'.tools/actionlint/actionlint.exe'
    subprocess.run([lint,*sorted((ROOT/'.github/workflows').glob('runner-readiness*.yml'))],cwd=ROOT,check=True,timeout=60)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True,timeout=60)
    subjects=['migration-candidate-freeze.json','final-matrix-audit.json','closing-old-archive-audit.json','all-old-attempt-accounting.json',
        'native-core-129b7a4.json','old-control-matrix-revision-3.json','new-control-development-evidence-revision-13.json',
        'all-command-accounting.json','fresh-checkout-verification.json','fresh-public-closing.json','shell-cache-ownership-verification.json',
        'closing-document-audit.json','closing-storage.json','control-applicability.md','final-report.md','limitations.md','usability-assessment.md','human-study.md']
    subjects += ['archive-controls-verified-'+h+'.json' for h in ['linux','macos','windows']]
    subjects += ['closing-harness-'+h+'.json' for h in ['ubuntu-24.04','macos-15','windows-2025']]
    subjects += ['archive-experience/'+name for name in archive_files]
    receipt=dict(status='engineering batch complete within recorded boundary',source_revision=frozen['source_revision'],version=frozen['version'],
        final_archive_qualified_projects=10,final_runner_admissions=10,runner_program_target=100,paid_launch_admissions=0,
        new_projects=[p['project'] for p in status['projects']],old_projects_migrated=10,old_migration_new_project_credit=0,
        final_canonical_scenarios=200,final_ordinary_executions=4800,final_calibration_executions=186,real_target_faults=31,native_cells=20,
        old_canonical_scenarios=130,old_primary_executions=274,old_calibration_executions=63,old_native_cells=21,
        public_archive_control_reexecutions=105,historical_whole_controls=88,applicable_historical_passes=87,new_whole_controls=33,
        human_participants=0,human_usability='unmeasured',published=False,stable_release_qualified=False,paid_integration_started=False,
        remaining_runner_projects=90,harness_run=args.harness_run,subjects={n:sha256(DOC/n) for n in subjects},control_retention=control_archives,
        scope='First ten new independently maintained projects under expanded deterministic runner contract. Old migrations, host copies, repetitions, harness checks and bounded R3 investigations do not inflate breadth. Historical unexplained failures and exclusions remain explicit residual risks, not causal repairs. Source-only internal controls remain source-only. Entire 100-project R4/final R5, human beginner readiness, public publication and commercial launch remain separate open gates.')
    current=load(DOC/'campaign-admission.json');require(current['status']=='pending closing validation','campaign already closed or unexpected admission record')
    immutable_json(RAW/'campaign-admission-verified.json',receipt)
    (DOC/'campaign-admission.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    status.update(final_archive_qualified_projects=10,final_runner_admissions=10,paid_launch_admissions=0,
        closing_admission_sha256=sha256(DOC/'campaign-admission.json'),scope='Ten series plus closing engineering gates verified. Immutable earlier receipts retain their original intermediate zero overall credit; closing admission supplies current scoped credit. Original unqualified series remain counted separately.')
    (DOC/'final-series-status.json').write_text(json.dumps(status,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Closed scoped engineering batch:10 new runner admissions/100; old migrations10; human0; paid0; unpublished.')


if __name__=='__main__':main()
