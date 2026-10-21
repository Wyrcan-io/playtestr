"""Freeze the already reviewed POSIX Plop profile before final execution."""
import json
import shutil

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_plop_cases import cases


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/plop'
    profile=docs/'final-native-profile';profile.mkdir()
    package=profile/'contracts';package.mkdir()
    for name in ['fixture','snapshots']:shutil.copytree(docs/name,package/name)
    changes=[];segmented={}
    for identity,filename,generator,_ in cases():
        value=load(docs/filename)
        args=['--no-progress']+([] if generator in {None,'artifact'} else ['--plopfile','extended.cjs'])+([generator] if generator else [])
        value['command']=['plop',*args]
        if identity=='E04':next(s for s in value['steps'] if 'exit' in s)['exit']=130
        if identity=='E05':value['steps']=[s for s in value['steps'] if not s.get('wait_for_redraw')]
        (package/filename).write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
        # Each selected field is a printable prompt response; control keys remain whole.
        segmented[filename]=[i for i,s in enumerate(value['steps'],1) if set(s)=={'text'} and len(s['text'])>1
            and all(ord(c)>=32 and ord(c)!=127 for c in s['text'])]
        changes.append(dict(id=identity,spec=filename,original_sha256=sha256(docs/filename),native_sha256=sha256(package/filename)))
    (package/'snapshots/normal-artifact.txt').write_bytes('? Artifact name alpha\n\u2714  ++ /out/alpha.txt\n'.encode())
    inputs={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
    immutable_json(profile/'reviewed-contract-freeze.json',dict(contracts={name:inputs[name] for _,name,_,_ in cases()},all_package_inputs=inputs))
    immutable_json(profile/'review.json',dict(contracts=changes,
        scope='Same explicit POSIX argv/SIGINT130/no-unsolicited-Inquirer-redraw/path-separator snapshot transformations in readiness_plop_profiles.py, already exercised by native development run39104247971. No new oracle, deadline or viewport changes. Windows resize remains unqualified.',
        segmented_text_steps=segmented))
    retained=RAW/'plop/retained-source';index=load(retained/'verified-index.json');acquired=load(retained/'acquisition.json')
    if sha256(retained/'source.tar.gz')!=acquired['archive_sha256'] or index['archive_sha256']!=acquired['archive_sha256']:
        raise RuntimeError('canonical reviewed source archive changed')
    immutable_json(docs/'source-review.json',dict(project='plopjs/plop',pin=acquired['pin'],license='MIT',
        archive_sha256=acquired['archive_sha256'],reviewed_inputs={n:r['sha256'] for n,r in index['files'].items()},
        policy='Existing reviewed pinned Plop workspace, immutable Yarn install with scripts disabled; no global installation. Canonical retained source/member hashes preserved.'))
    declaration=load(docs.parent/'fff/final-series-declaration-v2.json')
    for key in ['replacement_reason','superseded_run']:declaration.pop(key,None)
    declaration['revision']=1
    declaration.update(project='plop',segmented_text_steps_by_host={'linux':segmented,'macos':segmented},
        prior_project_boundary='FFF, Hygen and Rclone final native series independently verified and retained; overall final admissions remain separate.',
        scope='Exact existing rc.5 archives; twelve fresh executions per twenty reviewed POSIX cases per host. Only printable response fields may be segmented; key/control groups, all file/screen oracles and deadlines unchanged. Full source fault/restoration, independent audit and checked cleanup gates required.')
    immutable_json(docs/'final-series-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-final-hygen.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Hygen','Plop').replace('hygen','plop')
    workflow=workflow.replace('  READINESS_IDENTITY_CATALOG_PROJECT: plop\n','')
    workflow=workflow.replace('--declaration final-series-declaration-v2.json','--declaration final-series-declaration.json')
    workflow=workflow.replace('--series migration-v2\n','--package artifacts/runner-readiness-ten-project-pass/plop/host-contracts\n')
    workflow=workflow.replace('Prepare pinned tracked JavaScript target with reviewed production dependencies and unchanged native contracts',
        'Prepare pinned JavaScript target with immutable reviewed Yarn workspace and unchanged POSIX profile')
    workflow=workflow.replace('--timeout 600 -- python3 scripts/acceptance/readiness_plop_native_prepare.py',
        '--timeout 1200 -- python3 scripts/acceptance/readiness_plop_native_prepare.py')
    workflow=workflow.replace('plop-runtime-baseline.json','plop-node-baseline.json')
    (ROOT/'.github/workflows/runner-readiness-final-plop.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Frozen existing reviewed POSIX Plop contracts, source catalog and final declaration; no execution credit.')


if __name__=='__main__':main()
