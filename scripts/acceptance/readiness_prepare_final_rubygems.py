"""Freeze existing reviewed Bundler host semantics before final execution."""
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_rubygems_profiles import main as profiles


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rubygems'
    names=load(docs/'reviewed-contract-freeze.json')['contracts'];segmented={}
    for host in ['linux','windows']:
        profile=docs/'final-native-profiles'/host;profile.mkdir(parents=True)
        package=profile/'contracts'
        profiles(package,windows=host=='windows',installed_ruby_executable='/usr/bin/ruby3.2' if host=='linux' else None)
        inputs={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
        immutable_json(profile/'reviewed-contract-freeze.json',dict(contracts={n:inputs[n] for n in names},all_package_inputs=inputs,
            empty_directories=['build-fixture/dist']))
        segmented[host]={}
        for name in names:
            value=load(package/name)
            segmented[host][name]=[i for i,s in enumerate(value['steps'],1) if set(s)=={'text'} and len(s['text'])>1
                and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
    immutable_json(docs/'final-native-profiles/review.json',dict(
        installed_linux_ruby='/usr/bin/ruby3.2',
        prior_native_path_evidence='Every retained Linux runtime in generations1..5, including qualified requalification39146033898, resolves the same read-only /usr/bin/ruby3.2. Fresh native runtime must match frozen actual command or refuse before final launch.',
        scope='Existing explicit native Ruby platform, SystemDrive, LF/YAML, no-color and complete artifact oracles from readiness_rubygems_profiles.py. Recreate original reviewed empty build-fixture/dist after checkout; no new expectation from target output. Printable prompt response segmentation only.'))
    declaration=load(docs.parent/'poetry/final-series-declaration.json')
    declaration.update(project='rubygems',hosts=['linux-amd64','windows-amd64'],segmented_text_steps_by_host=segmented,
        prior_project_boundary='Poetry final Linux ordinary/fault/cleanup job succeeded; macOS final series underway. Four earlier final series independently verified.',
        scope='Exact existing rc.5 archives; twelve fresh executions per twenty reviewed native Bundler cases per host. All state/artifact/screen oracles and deadlines unchanged; printable responses only segmented. Actual source faults, exact restoration, native audit and cleanup required.')
    peak=max(record['bytes'] for path in (RAW/'rubygems').glob('retained-native-v*/index.json')
        for name,record in load(path,maximum=4*1024**2)['files'].items() if '/identities/' in name)
    declaration['identity_catalogs']=dict(enabled=True,scopes=['core','target'],historical_max_manifest_bytes=peak,
        unshared_240_identity_forecast_bytes=peak*240,prior_retained_project_bytes=46598368,project_cap_bytes=67108864,
        mode='Every actual input is rehashed before launch. Intern complete content-addressed core/target file maps; each actual event retains self-contained catalog references. Changes produce fresh catalogs; no hash caching or cap increase.')
    immutable_json(docs/'final-series-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-final-rclone.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Rclone','Bundler').replace('rclone','rubygems')
    workflow=workflow.replace('readiness_rubygems_native_prepare.py\n','readiness_rubygems_native_prepare.py --target-only\n')
    workflow=workflow.replace('readiness_rubygems_faults.py --series migration-v2',
        'readiness_rubygems_faults.py --package artifacts/runner-readiness-ten-project-pass/rubygems/host-contracts')
    workflow=workflow.replace('Prepare pinned Go target with reviewed owned SDK/dependencies',
        'Prepare pinned Ruby target with reviewed native runtime and unchanged host profile')
    (ROOT/'.github/workflows/runner-readiness-final-rubygems.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Frozen Bundler native contracts and final archive schedule; no execution credit.')


if __name__=='__main__':main()
