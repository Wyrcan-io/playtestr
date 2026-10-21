"""Declare exact reviewed Frogmouth profiles and final archive schedules."""
import argparse
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',type=int,choices=[1,2],default=1);args=parser.parse_args()
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/frogmouth';segmented={}
    for host in ['linux','windows']:
        profile=docs if host=='linux' else docs/'native-profiles/windows'
        frozen=load(profile/'reviewed-contract-freeze.json');require_count=len(frozen['contracts'])
        if require_count!=20:raise RuntimeError('twenty reviewed native contracts required')
        for name,digest in frozen['all_package_inputs'].items():
            if sha256(profile/'contracts'/name)!=digest:raise RuntimeError('reviewed native input changed')
        segmented[host]={}
        for name in frozen['contracts']:
            value=load(profile/'contracts'/name)
            segmented[host][name]=[i for i,s in enumerate(value['steps'],1) if set(s)=={'text'} and len(s['text'])>1
                and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
    declaration=load(docs/'final-series-declaration.json') if args.revision==2 else load(docs.parent/'edit/final-series-declaration.json')
    declaration.pop('target_restore_identity',None)
    declaration.update(project='frogmouth',segmented_text_steps_by_host=segmented,
        prior_project_boundary='Edit final native twelve-batch series running; six earlier final series independently verified and retained.',
        scope='Exact existing rc.5 archives; twelve fresh executions per twenty unchanged reviewed native Frogmouth contracts per host. Printable address/prompt responses only segmented; control bytes remain whole, all source-preservation/screen/state oracles and deadlines unchanged. Actual fresh F01/F02/F04 source fault replicas, exact restoration, full independent native audit and cleanup required.')
    peak=max(record['bytes'] for path in (RAW/'frogmouth').glob('retained-native-v*/index.json')
        for name,record in load(path,maximum=4*1024**2)['files'].items() if '/identities/' in name)
    declaration['identity_catalogs']=dict(enabled=True,scopes=['core','target'],historical_max_manifest_bytes=peak,
        unshared_240_identity_forecast_bytes=peak*240,project_cap_bytes=64*1024**2,
        mode='Fresh rehash of actual source/runtime/selected inputs before every launch, with complete self-contained content-addressed file maps. No hash caching, missing dictionary or limit increase.')
    declaration['fault_selection']=dict(revision=2,selection_sha256=sha256(docs/'fault-selection-revision-2.json'),
        review_sha256=sha256(docs/'source-fault-review-revision-2.json'),ids=['F01','F02','F04'],original_heldout=False,
        scope='Fresh selection replicas; original historical F03 miss and later original F04 consumption remain retained, never relabeled as untouched holdout.')
    declaration_file='final-series-declaration-v2.json' if args.revision==2 else 'final-series-declaration.json'
    if args.revision==2:
        declaration.update(revision=2,superseded_run='39680492184',
            replacement_reason='The first workflow exported the target venv to GITHUB_PATH, which can resolve later validation helpers into that owned target runtime and make Windows CIM ownership checks see the helper itself. Native own-PID Git Bash probe7201dc204b6e4bd08b02d2a254a5ab70 confirmed interpreter-directory visibility. Cancel/preserve the first partial series; keep workflow helpers on installed bootstrap Python and pass the target runtime only in explicit public target environments. No oracle, input grouping, product deadline or frozen runner change.',
            helper_runtime_policy='Target-only setup --no-path-export; each ordinary/fault invocation already uses its explicit owned target environment.',
            prior_project_boundary='Seven previous final project series independently verified and retained. Original Frogmouth partial series remains unqualified and retained separately.')
    immutable_json(docs/declaration_file,declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-final-edit.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Edit','Frogmouth').replace('edit','frogmouth')
    workflow=workflow.replace('Prepare pinned Rust editor with reviewed owned dependencies and unchanged host profile',
        'Prepare pinned local Markdown viewer with reviewed owned Python dependencies and unchanged host profiles')
    workflow=workflow.replace('Prepare pinned Rust frogmouthor with reviewed owned dependencies and unchanged host profile',
        'Prepare pinned local Markdown viewer with reviewed owned Python dependencies and unchanged host profiles')
    workflow=workflow.replace('readiness_frogmouth_faults.py --package artifacts/runner-readiness-ten-project-pass/frogmouth/host-contracts',
        'readiness_frogmouth_faults.py --series migration-v2 --selection fresh')
    if args.revision==2:
        workflow=workflow.replace('readiness_frogmouth_native_prepare.py --target-only','readiness_frogmouth_native_prepare.py --target-only --no-path-export')
        workflow=workflow.replace('readiness_final_fff.py --project frogmouth','readiness_final_fff.py --project frogmouth --declaration '+declaration_file)
    (ROOT/'.github/workflows/runner-readiness-final-frogmouth.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Declared exact reviewed Frogmouth archive series and fresh source-fault replicas; no execution credit.')


if __name__=='__main__':main()
