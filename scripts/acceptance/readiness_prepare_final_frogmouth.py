"""Declare exact reviewed Frogmouth profiles and final archive schedules."""
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
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
    declaration=load(docs.parent/'edit/final-series-declaration.json');declaration.pop('target_restore_identity',None)
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
    immutable_json(docs/'final-series-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-final-edit.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Edit','Frogmouth').replace('edit','frogmouth')
    workflow=workflow.replace('Prepare pinned Rust editor with reviewed owned dependencies and unchanged host profile',
        'Prepare pinned local Markdown viewer with reviewed owned Python dependencies and unchanged host profiles')
    workflow=workflow.replace('Prepare pinned Rust frogmouthor with reviewed owned dependencies and unchanged host profile',
        'Prepare pinned local Markdown viewer with reviewed owned Python dependencies and unchanged host profiles')
    workflow=workflow.replace('readiness_frogmouth_faults.py --package artifacts/runner-readiness-ten-project-pass/frogmouth/host-contracts',
        'readiness_frogmouth_faults.py --series migration-v2 --selection fresh')
    (ROOT/'.github/workflows/runner-readiness-final-frogmouth.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Declared exact reviewed Frogmouth archive series and fresh source-fault replicas; no execution credit.')


if __name__=='__main__':main()
