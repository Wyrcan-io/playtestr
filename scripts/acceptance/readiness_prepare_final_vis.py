"""Freeze the already reviewed native Vis locale profiles and archive schedule."""
import json
import shutil

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/vis'
    frozen=load(docs/'reviewed-contract-freeze.json');segmented={}
    for name,digest in frozen['all_package_inputs'].items():
        if sha256(docs/'contracts'/name)!=digest:raise RuntimeError('reviewed native input changed')
    for host in ['linux','macos']:
        profile=docs/'final-native-profiles'/host;profile.mkdir(parents=True)
        package=profile/'contracts';shutil.copytree(docs/'contracts',package)
        segmented[host]={}
        for name in frozen['contracts']:
            value=load(package/name)
            if value['env']!={'LC_ALL':'C.UTF-8','TERM':'xterm-256color'}:raise RuntimeError('unexpected frozen locale')
            if host=='macos':
                value['env']['LC_ALL']='en_US.UTF-8'
                (package/name).write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
            # Retain complete normal-mode key groups and command lines. Split only
            # explicit insertion text following a positive INSERT observation.
            segmented[host][name]=[i for i,s in enumerate(value['steps'],1) if set(s)=={'text'} and len(s['text'])>1
                and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])
                and i>1 and value['steps'][i-2].get('expect')=='INSERT']
        inputs={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
        immutable_json(profile/'reviewed-contract-freeze.json',dict(contracts={n:inputs[n] for n in frozen['contracts']},all_package_inputs=inputs))
    declaration=load(docs.parent/'poetry/final-series-declaration.json')
    declaration.update(project='vis',segmented_text_steps_by_host=segmented,
        prior_project_boundary='Eight final series independently verified; Papis final native series dispatched as run39735220618. Vis acquisition/execution remains sequential after Papis qualification.',
        scope='Exact existing rc.5 archives; twelve fresh executions per twenty unchanged reviewed native Vis contracts per host. Existing macOS en_US.UTF-8 locale adaptation only. Segment insertion text only after positive INSERT; preserve modal key groups and command lines. Three real rebuilt C source faults, exact restoration, independent audit and checked cleanup required.')
    peak=max(r['bytes'] for path in (RAW/'vis').glob('retained-native-v*/index.json')
        for n,r in load(path,maximum=4*1024**2)['files'].items() if '/identities/' in n)
    declaration['identity_catalogs']=dict(enabled=True,scopes=['core','target'],historical_max_manifest_bytes=peak,
        unshared_240_identity_forecast_bytes=peak*240,project_cap_bytes=64*1024**2,
        mode='Fresh rehash of complete selected C/header/configuration inputs, actual target and installed compiler/make before each launch; complete content-addressed maps, no hash caching or limit increase.')
    declaration['fault_selection']=dict(ids=['F01','F02','F03'],original_heldout=False,
        selection_sha256=sha256(docs/'fault-selection.json'),public_calibration_per_host=9,
        scope='Replicas of three reviewed actual C source faults; original heldout remains separately retained.')
    immutable_json(docs/'final-series-declaration.json',declaration)
    immutable_json(docs/'final-native-profiles/review.json',dict(
        existing_algorithm_sha256=sha256(ROOT/'scripts/acceptance/readiness_vis_native_contracts.py'),
        scope='Existing source-reviewed macOS locale substitution only; all screen and saved-byte oracles, inputs, viewports and deadlines unchanged. Insertion-only segmentation keeps modal command groups complete.'))
    workflow=(ROOT/'.github/workflows/runner-readiness-final-poetry.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Poetry','Vis').replace('poetry','vis')
    workflow=workflow.replace('Prepare pinned Python target with reviewed owned venv and unchanged POSIX profile',
        'Prepare pinned C editor with reviewed native build and unchanged locale profiles')
    (ROOT/'.github/workflows/runner-readiness-final-vis.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Prepared reviewed Vis native profiles and exact archive schedule; no execution credit.')


if __name__=='__main__':main()
