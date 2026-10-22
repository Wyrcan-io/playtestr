"""Declare the existing reviewed Papis native profiles and four real fault replicas."""
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/papis';segmented={}
    for host in ['linux','windows']:
        profile=docs if host=='linux' else docs/'native-profiles/windows';frozen=load(profile/'reviewed-contract-freeze.json')
        if len(frozen['contracts'])!=20:raise RuntimeError('twenty reviewed native contracts required')
        for name,digest in frozen['all_package_inputs'].items():
            if sha256(profile/'contracts'/name)!=digest:raise RuntimeError('reviewed native input changed')
        segmented[host]={}
        for name in frozen['contracts']:
            value=load(profile/'contracts'/name)
            segmented[host][name]=[i for i,s in enumerate(value['steps'],1) if set(s)=={'text'} and len(s['text'])>1
                and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
    declaration=load(docs.parent/'frogmouth/final-series-declaration-v2.json')
    for key in ['superseded_run','replacement_reason']:declaration.pop(key,None)
    declaration.update(project='papis',revision=1,segmented_text_steps_by_host=segmented,
        prior_project_boundary='Corrected Frogmouth final series running after the preserved original cancelled helper-profile series; seven earlier final series independently verified.',
        scope='Exact existing rc.5 archives; twelve fresh executions per twenty unchanged reviewed native Papis contracts per host. Printable picker/filename responses only segmented; controls, all exact file/directory/screen oracles and deadlines unchanged. Four real F01/F02/F03/F04 editable source fault replicas, exact restoration, independent native audit and checked cleanup required.')
    peak=max(record['bytes'] for path in (RAW/'papis').glob('retained-native-v*/index.json')
        for name,record in load(path,maximum=4*1024**2)['files'].items() if '/identities/' in name)
    declaration['identity_catalogs']=dict(enabled=True,scopes=['core','target'],historical_max_manifest_bytes=peak,
        unshared_240_identity_forecast_bytes=peak*240,project_cap_bytes=64*1024**2,
        mode='Fresh rehash of actual source/runtime/selected inputs before every launch; self-contained complete content-addressed maps, no hash caching or limit increase.')
    ids=[f['id'] for f in load(docs/'fault-selection-revision-2.json')['faults']]
    if ids!=['F01','F02','F03','F04']:raise RuntimeError('reviewed four-fault selection changed')
    declaration['fault_selection']=dict(revision=2,ids=ids,original_heldout=False,
        selection_sha256=sha256(docs/'fault-selection-revision-2.json'),review_sha256=sha256(docs/'source-fault-review-revision-2.json'),
        public_calibration_per_host=12,public_calibration_total=24,
        scope='All four reviewed fault replicas; historical first miss/original F04 consumption remain retained and are not relabeled as untouched holdout.')
    immutable_json(docs/'final-series-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-final-frogmouth.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Frogmouth','Papis').replace('frogmouth','papis')
    workflow=workflow.replace('Prepare pinned local Markdown viewer with reviewed owned Python dependencies and unchanged host profiles',
        'Prepare pinned local bibliography picker with reviewed owned Python dependencies and unchanged host profiles')
    workflow=workflow.replace('readiness_final_fff.py --project papis --declaration final-series-declaration-v2.json',
        'readiness_final_fff.py --project papis --declaration final-series-declaration.json')
    workflow=workflow.replace('Three actual source faults with exact restoration on the final archive',
        'Four actual source faults with exact restoration on the final archive')
    (ROOT/'.github/workflows/runner-readiness-final-papis.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Declared reviewed Papis archive series and four actual source fault replicas; no execution credit.')


if __name__=='__main__':main()
