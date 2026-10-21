"""Freeze already reviewed POSIX Poetry semantics before final native execution."""
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_poetry_profiles import main as profiles


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/poetry';profile=docs/'final-native-profile'
    profile.mkdir();package=profile/'contracts'
    profiles(target=package,windows=False)
    names=load(docs/'reviewed-contract-freeze.json')['contracts']
    inputs={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
    immutable_json(profile/'reviewed-contract-freeze.json',dict(contracts={n:inputs[n] for n in names},all_package_inputs=inputs))
    segmented={}
    for name in names:
        spec=load(package/name)
        segmented[name]=[i for i,s in enumerate(spec['steps'],1) if set(s)=={'text'} and len(s['text'])>1
            and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
    immutable_json(profile/'review.json',dict(segmented_text_steps=segmented,
        archive_oracle_sha256=sha256(ROOT/'scripts/acceptance/readiness_poetry_archive_oracle.py'),
        scope='Existing POSIX null-device, reviewed LF generation and independently specified complete synthetic sdist TAR/gzip oracle from readiness_poetry_profiles.py. This is authoring before target execution; no captured output updates expectations. Actual native profile must match every frozen byte or refuse before series launch. Only printable response fields segmented; controls/oracles/deadlines unchanged.'))
    retained=RAW/'poetry/retained-source';index=load(retained/'verified-index.json');acquired=load(retained/'acquisition.json')
    if sha256(retained/'source.tar.gz')!=acquired['archive_sha256'] or index['archive_sha256']!=acquired['archive_sha256']:
        raise RuntimeError('canonical reviewed Poetry source differs')
    immutable_json(docs/'source-review.json',dict(project='python-poetry/poetry',pin=acquired['pin'],license='MIT',
        archive_sha256=acquired['archive_sha256'],reviewed_inputs={n:r['sha256'] for n,r in index['files'].items()},
        policy='Existing reviewed pinned source; owned venv, wheel-only dependency acquisition, editable reviewed source and no plugins/global install.'))
    declaration=load(docs.parent/'plop/final-series-declaration.json')
    declaration.update(project='poetry',segmented_text_steps_by_host={'linux':segmented,'macos':segmented},
        prior_project_boundary='Plop final native ordinary/fault/cleanup jobs both succeeded; independent evidence audit/retention underway. Three earlier final project series independently verified.',
        scope='Exact existing rc.5 archives; twelve fresh executions per twenty already reviewed POSIX Poetry cases per host. Independent complete sdist oracle frozen before launch. Printable response segmentation preserves control groups, all correctness oracles and product deadlines. Actual faults/restoration, complete audit and checked cleanup required.')
    immutable_json(docs/'final-series-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-final-plop.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Plop','Poetry').replace('plop','poetry')
    workflow=workflow.replace('readiness_cleanup_poetry.py','readiness_cleanup_plop.py')
    workflow=workflow.replace('Prepare pinned JavaScript target with immutable reviewed Yarn workspace and unchanged POSIX profile',
        'Prepare pinned Python target with reviewed owned venv and unchanged POSIX profile')
    workflow=workflow.replace('poetry-node-baseline.json','poetry-runtime-baseline.json')
    (ROOT/'.github/workflows/runner-readiness-final-poetry.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Frozen reviewed Poetry POSIX contracts and exact archive schedule; no execution credit.')


if __name__=='__main__':main()
