"""Admit only the independently verified, retained and removed fff dev package."""
import argparse
import json
import shutil

from readiness_compact_native import verify
from readiness_fff_verify_native import SOURCE,require
from readiness_evidence import RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_observations,read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--core-run',required=True);args=parser.parse_args()
    require(args.core_run.isascii() and args.core_run.isdecimal(),'invalid core run')
    metadata=load(RAW/'native'/args.core_run/'run-metadata.json')
    require(metadata['headSha']==SOURCE and metadata['conclusion']=='success' and metadata['status']=='completed','core source not qualified')
    require(len(metadata['jobs'])==3 and all(j['conclusion']=='success' for j in metadata['jobs']),'incomplete native core')
    controls=packet_observations(args.core_run)
    for host in ['linux','macos']:
        selected=[r for r in controls if r['host']==host and
            ('github.com/Wyrcan-io/playtestr/internal/runner','TestPrimaryReplyBlockedWriterStopsWithinCleanup') in r['whole'] and
            ('github.com/Wyrcan-io/playtestr/internal/runner','TestPrimaryReplyRealPTYStartupAndExactExit') in r['whole'] and
            ('github.com/Wyrcan-io/playtestr/internal/runner','TestPrimaryReplyFloodPreservesOutputLimit') in r['whole'] and
            ('github.com/Wyrcan-io/playtestr/internal/runner','TestPrimaryReplyTransportErrorIsPreservedWithRealTarget') in r['whole']]
        require(len(selected)>=2,'actual ordinary/race Unix reply controls missing')
    project=RAW/'fff';docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/fff'
    require(not (RAW/'active/fff').exists(),'local active editor remains')
    removal=project/'retained-source/removed.json';removed=load(removal)
    canonical=load(docs/'source-review.json')['archive_sha256']
    require(removed['removed'] and removed['owned_relative_path']=='active/fff' and removed['source_archive_sha256']==canonical,'local removal incomplete')
    require(sha256(removal.parent/'source.tar.gz')==canonical,'local canonical source archive differs')
    source_index=load(removal.parent/'verified-index.json')
    for name in source_index['selected_restore']:
        require(sha256(removal.parent/'selected-restore'/name)==source_index['files'][name]['sha256'],'local source restore changed')
    native=load(project/'native-development-verification.json')
    require(native['runner_source']==SOURCE and len(native['cells'])==2,'wrong native source/cells')
    retained=project/'retained-native-v1';index=load(retained/'index.json',4*1024**2);verified=load(retained/'verified.json')
    require(sha256(retained/'index.json')==verified['index_sha256'] and sha256(retained/'packets.tar.gz')==index['archive_sha256']==verified['archive_sha256'],'native retained identity changed')
    require(len(index['files'])<=40000 and index['expanded_bytes']<=128*1024**2,'retained index coverage bound')
    verify(retained/'packets.tar.gz',index['files'])
    expanded=load(retained/'expanded-removed.json')
    require(expanded['all_expanded_removed'] and expanded['archive_sha256']==index['archive_sha256'],'expanded packets not removed')
    require(set(expanded['removed_runs'])==set(index['runs']) and all(not (RAW/'native'/r).exists() for r in index['runs']),'expanded copies remain')
    for cell in native['cells']:
        prefix='native/'+cell['run']+'/'+cell['host']+'/'
        require(any(name.startswith(prefix+'fff/suites/') and name.endswith('/results.json') and record['sha256']==cell['report_sha256'] for name,record in index['files'].items()),'verified report absent from retained packet')
        for key in ['source_fault_summary_sha256','maintenance_sha256','cleanup_receipt_sha256']:
            require(any(name.startswith(prefix) and row['sha256']==cell[key] for name,row in index['files'].items()),'verified cell payload missing')
    originals=list((docs/'original-source-faults').glob('summary.json'));require(len(originals)==1,'original fault batch ambiguous')
    faults=load(originals[0]);require(len(faults['faults'])==3 and [r['id'] for r in faults['faults'] if r['held_out']]==['F03'],'original heldout coverage mismatch')
    selection=load(originals[0].parent/'selected-faults.json')
    require(selection['frozen_contract_sha256']==sha256(docs/'reviewed-contract-freeze.json'),'original fault selection does not bind the reviewed freeze')
    require(all(r['restored_exact'] for r in faults['faults']),'missing original restoration')
    observed=sum(p.stat().st_size for p in project.rglob('*') if p.is_file())
    require(observed<64*1024**2,'project retained evidence cap exceeded')
    record=dict(schema_version=1,project='dylanaraps/fff',pin='6f2dc6f3a003d24e8b3fd48b046241b486022ad5',
        status='development-admitted',normal_scenarios=8,edge_scenarios=12,real_faults=3,cells=native['cells'],
        runner_source=SOURCE,core_run=args.core_run,core_metadata_sha256=sha256(RAW/'native'/args.core_run/'run-metadata.json'),
        native_verification_sha256=sha256(project/'native-development-verification.json'),
        first_use_sha256=sha256(docs/'first-use-native-39065486885.json'),reviewed_freeze_sha256=sha256(docs/'reviewed-contract-freeze.json'),
        original_fault_summary_sha256=sha256(originals[0]),local_source_removal_receipt_sha256=sha256(removal),
        native_packet_archive_sha256=index['archive_sha256'],native_packet_index_sha256=sha256(retained/'index.json'),
        all_native_payloads_verified=verified['members_verified'],selected_native_restores=verified['selected_restore_verified'],
        observed_project_retained_bytes=observed,native_packet_reference='Local-only artifacts/runner-readiness-ten-project-pass/fff/retained-native-v1/',
        archive_qualified=False,final_runner_admissions=0,human_usability='unmeasured',
        holdout='Only Linux F03 in 39070554085 is original, selected after committed twenty-contract freeze fc3dacd; macOS and later repetitions are replicas.',
        limitations='Agent/source familiarity and warm prerequisites; human usability unmeasured. Local Windows source was never built or run. All final archive gates remain open.')
    candidate_path=docs.parent/'candidates.json';candidates=load(candidate_path)
    require(candidates['project_admissions']==candidates['development_admissions']==5,'unexpected admission counter; do not double count')
    original_bytes=candidate_path.read_bytes()
    candidate=next(r for r in candidates['rows'] if r['repository']=='dylanaraps/fff')
    candidate.update(status='development-admitted',qualified_hosts=['linux-amd64','macos-arm64'],
        qualification='Twenty cases per native host, actual interpreted source faults/restorations, maintenance and checked retention/removal at runner '+SOURCE[:7]+', run 39070554085. Final archives pending.')
    candidates['project_admissions']=candidates['development_admissions']=6
    require(load(removal.parent/'source-only.json')['native_local_runtime_attempted'] is False,'unexpected local Windows runtime claim')
    require(sha256(docs/'native-development-verification.json')==sha256(project/'native-development-verification.json'),'curated native verification differs')
    original_prefix='native/39070554085/playtestr-Linux/fff/faults/'
    require(any(name.startswith(original_prefix) and name.endswith('/summary.json') and value['sha256']==sha256(originals[0]) for name,value in index['files'].items()),'original heldout summary absent from verified archive')
    immutable_json(docs/'development-admission.json',record)
    data=(json.dumps(candidates,indent=2,ensure_ascii=True)+'\n').encode()
    if b'\r\n' in original_bytes:data=data.replace(b'\n',b'\r\n')
    candidate_path.write_bytes(data)
    print('fff development package admitted: six projects/twelve native cells; final archive credit remains zero.')


if __name__=='__main__':main()
