"""Freeze existing native Edit profile and final exact-archive schedules."""
import json
import shutil

from readiness_edit_profiles import native_profile
from readiness_evidence import ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/edit';source=docs/'contracts'
    frozen=load(docs/'reviewed-contract-freeze.json');segmented={}
    for host in ['linux','windows']:
        profile=docs/'final-native-profiles'/host;profile.mkdir(parents=True)
        package=profile/'contracts';shutil.copytree(source,package)
        for name in frozen['contracts']:
            if host=='linux':
                value=native_profile(load(source/name),name,False)
                (package/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
        inputs={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
        immutable_json(profile/'reviewed-contract-freeze.json',dict(contracts={n:inputs[n] for n in frozen['contracts']},all_package_inputs=inputs))
        segmented[host]={}
        for name in frozen['contracts']:
            value=load(package/name)
            segmented[host][name]=[i for i,s in enumerate(value['steps'],1) if set(s)=={'text'} and len(s['text'])>1
                and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
    immutable_json(docs/'final-native-profiles/review.json',dict(
        profile_algorithm_sha256=sha256(ROOT/'scripts/acceptance/readiness_edit_profiles.py'),
        scope='Existing source-reviewed SystemDrive inheritance and N02 Unix final-LF policy. Every other original screen/file oracle, input control, viewport and deadline preserved. Segment printable insertion/prompt responses only; complete newline/control-containing text actions retained.'))
    declaration=load(docs.parent/'rubygems/final-series-declaration.json')
    declaration.update(project='edit',segmented_text_steps_by_host=segmented,
        prior_project_boundary='Bundler final Linux job succeeded; Windows batches underway. Five earlier final series independently verified and retained.',
        scope='Exact existing rc.5 archives; twelve fresh executions per twenty reviewed native Edit cases per host. Only printable text segmentation; all controls, snapshots, expected saved bytes and product deadlines unchanged. Three actual rebuilt Rust/resource faults, exact restoration, independent audit and cleanup required.')
    declaration['identity_catalogs'].update(historical_max_manifest_bytes=56073,unshared_240_identity_forecast_bytes=13457520,
        prior_retained_project_bytes=10130242)
    declaration['target_restore_identity']=dict(
        prior_native_evidence='Qualified development run39146177966: all three Linux rebuilt restores reproduced baseline target executable bytes; all three Windows rebuilt restores had different executable hashes.',
        policy='Restore exact pinned source bytes, rebuild normally using the same recorded compiler/flags and run unchanged contracts against the actual rebuilt executable. Bind every mutation/restoration source and executable hash; do not substitute an earlier executable or claim Windows target build byte reproducibility. The exact frozen Playtestr archive executable remains unchanged throughout.')
    immutable_json(docs/'final-series-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-final-rubygems.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Bundler','Edit').replace('rubygems','edit')
    workflow=workflow.replace('Prepare pinned Ruby target with reviewed native runtime and unchanged host profile',
        'Prepare pinned Rust editor with reviewed owned dependencies and unchanged host profile')
    (ROOT/'.github/workflows/runner-readiness-final-edit.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Frozen reviewed Edit native profiles and exact archive schedule; no execution credit.')


if __name__=='__main__':main()
