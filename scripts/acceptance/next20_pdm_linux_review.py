"""Independently inspect the actual first PDM Linux packet and declare a correction."""
import hashlib
import argparse
import json
import posixpath
import tarfile

from next20_check import DOC, RAW
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',choices=['40865561435','40867193964'],default='40865561435');args=parser.parse_args()
    run=args.run;second=run=='40867193964';package=DOC/'pdm'
    packet=RAW/'native'/run/'next20-pdm-linux-preflight';scope='artifacts/'+RAW.name+'/'
    contracts=packet/'pdm/host-contracts';declaration=json.loads((contracts/'scenarios.json').read_text())
    frozen=json.loads((contracts/'development-test-freeze.json').read_text())
    for name,digest in frozen['inputs'].items():
        if sha256(contracts/name)!=digest:raise ValueError('native frozen input changed')
    summaries=list((packet/'pdm/development').glob('*/summary.json'))
    if len(summaries)!=1:raise ValueError('one first native development series required')
    summary=json.loads(summaries[0].read_text())
    if summary['declaration_sha256']!=sha256(contracts/'scenarios.json'):raise ValueError('wrong native declaration')
    retained=packet/'pdm/retained-source';acquisition=json.loads((retained/'acquisition.json').read_text())
    provenance=json.loads((package/'source-provenance.json').read_text())
    if acquisition['source_files']!=provenance['files']:raise ValueError('native primary sources differ')
    primary={}
    with tarfile.open(retained/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if member.isfile():
                name=member.name.split('/',1)[1]
                if name in primary:raise ValueError('duplicate source archive file')
                primary[name]=hashlib.sha256(archive.extractfile(member).read()).hexdigest()
    if primary!=provenance['files']:raise ValueError('actual retained source archive differs')
    runtime=json.loads((retained/'runtime.json').read_text())
    owner=json.loads((retained/'task-owned.json').read_text())
    profile=json.loads((package/'native-profile-v2.json').read_text()) if second else {'case_profiles':{}}
    if second and frozen.get('explicit_profile_sha256')!=sha256(package/'native-profile-v2.json'):raise ValueError('second native profile not bound')
    generated=json.loads((packet/'pdm/native-generated-source.json').read_text())['generated_files']
    source_expected={**primary,**{n:r['sha256'] for n,r in generated.items()}}
    for name,row in generated.items():
        if sha256(retained/'generated-source'/name)!=row['sha256']:raise ValueError('generated native source bytes missing')
    install=json.loads((packet/'candidate-native-exit-v1/linux/installed.json').read_text())
    expected_candidate=next(r for r in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if r['host']=='linux')
    if any(install[k]!=expected_candidate[k] for k in ['archive_sha256','binary_sha256']):raise ValueError('wrong executed archive')
    observations=[]
    for case,row in zip(declaration['cases'],summary['results'],strict=True):
        if case['id']!=row['case']:raise ValueError('native case order/count differs')
        report=packet/row['report'].removeprefix(scope)
        if sha256(report)!=row['report_sha256'] or sha256(contracts/case['spec'])!=case['spec_sha256']:raise ValueError('report/contract digest differs')
        from next20_python_host_profile import wizard_profile
        expected=wizard_profile(json.loads((package/case['spec']).read_text()),dict(case,**profile['case_profiles'].get(case['id'],{})),runtime['python'],'linux')
        expected['command'][0]=posixpath.relpath(runtime['python'],owner['workspace']+'/'+scope+'pdm/host-contracts')
        if json.loads((contracts/case['spec']).read_text())!=expected:raise ValueError('executed native spec differs from explicit reviewed profile')
        actual=json.loads(report.read_text())['results'][0]
        if actual['invocation_id']!=row['invocation'] or actual['status']!=row['status']:raise ValueError('different invocation/status')
        if not actual['cleanup']['confirmed_exited'] or not actual['workspace']['cleaned']:raise ValueError('native cleanup incomplete')
        for step in actual['steps']:
            if 'state' in step and (step['state']['invocation_id']!=actual['invocation_id'] or step['state']['workspace_id']!=actual['workspace']['id']):
                raise ValueError('cross-invocation state')
        events={kind:json.loads((packet/'events'/(row['attempt']+'-'+kind+'.json')).read_text()) for kind in ['started','identified','launched','finished']}
        if any(e['phase']!='development' or e['project']!='pdm' for e in events.values()):raise ValueError('wrong project/phase')
        if events['started']['ci_run_id']!=run or events['finished']['cleanup_errors'] or events['finished']['harness_cleanup']!='harness_process_reaped':raise ValueError('provider/harness lifecycle differs')
        identity=events['identified']['identity'];manifest=packet/identity['manifest']
        if sha256(manifest)!=identity['sha256']:raise ValueError('prelaunch identity differs')
        combined=json.loads(manifest.read_text());target_ref=combined['target_catalog'];target_path=packet/target_ref['manifest']
        if sha256(target_path)!=target_ref['sha256']:raise ValueError('target catalog differs')
        target_files=json.loads(target_path.read_text())['files']
        actual_sources={n.removeprefix(scope+'active/pdm/src/'):d for n,d in target_files.items() if n.startswith(scope+'active/pdm/src/')}
        if actual_sources!=source_expected or target_files.get(scope+'active/pdm/runtime.json')!=sha256(retained/'runtime.json'):raise ValueError('actual launch source/runtime differs')
        base_ref=combined['base'];base_path=packet/base_ref['manifest']
        if sha256(base_path)!=base_ref['sha256']:raise ValueError('base launch catalog differs')
        files=json.loads(base_path.read_text())['files']
        if files.get(scope+'candidate-native-exit-v1/linux/playtestr')!=install['binary_sha256'] or files.get(scope+'pdm/host-contracts/'+case['spec'])!=case['spec_sha256']:
            raise ValueError('actual runner/spec differs')
        if actual['status']=='passed':
            if any(s['status']!='passed' for s in actual['steps']):raise ValueError('nonpositive passing steps')
        else:
            screen=packet/actual['evidence']['screen_path'].removeprefix(scope)
            if not screen.is_file():raise ValueError('original failed screen missing')
        observations.append(dict(case=case['id'],status=actual['status'],category=actual.get('failure',{}).get('category'),
            report_sha256=sha256(report),attempt=row['attempt'],source_files=len(actual_sources),target_cleanup=True,workspace_cleanup=True))
    failures=[] if second else [('N01','unexpected_exit'),('N05','state_assertion_failure')]
    if len(observations)!=20 or [(r['case'],r['category']) for r in observations if r['status']!='passed']!=failures:
        raise ValueError('native outcome differs from declared window')
    removed=json.loads((retained/'removed.json').read_text());inventory=json.loads((retained/'cleanup-inventory.json').read_text())
    if not removed['removed'] or removed['cleanup_inventory_sha256']!=sha256(retained/'cleanup-inventory.json') or inventory['actual_reports_with_confirmed_cleanup']!=20:
        raise ValueError('native source/runtime removal incomplete')
    immutable_json(package/('linux-second-development-readback.json' if second else 'linux-first-development-readback.json'),dict(schema_version=1,run=run,
        source_revision='d1d24adeec20f7a66c798bed7747de06353fadf6' if second else '422a943f1330dab06d1e07fba5a97eaf4b403ab1',
        passed=20-len(failures),failed=len(failures),observations=observations,source_blobs_verified=len(primary),native_generated_files=len(generated),
        actual_summary_sha256=sha256(summaries[0]),runtime_sha256=sha256(retained/'runtime.json'),
        source_runtime_removed=True,qualification_credit=0,project_admissions=0))
    if second:
        print('Independently verified all20 positive native reports, exact profile-derived contracts,402source blobs, launch identities and complete native cleanup. No final/admission credit.');return
    immutable_json(package/'native-profile-v2.json',dict(schema_version=1,host='linux',
        native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),canonical_freeze_sha256=sha256(package/'development-test-freeze.json'),
        first_native_readback_sha256=sha256(package/'linux-first-development-readback.json'),
        case_profiles={'N01':dict(readiness_before_step={'3':'Do you want to build this project','4':'License(SPDX name)',
            '5':'Author name','7':'Author email','9':'Python requires'}),'N05':dict(preserve_generated_newlines=['pyproject.toml'])},
        source_proof=dict(parent_workspace_writer='src/pdm/project/toml_file.py: TOMLFile.write preserves the existing detected CRLF line separator with newline=""; do not convert the parent expectation. Newly created child TOML remains LF.',
            files={n:provenance['files'][n] for n in ['src/pdm/project/toml_file.py','src/pdm/project/workspace.py']}),
        scope='Add positive prompt readiness before original inputs, preserving every original action and oracle/snapshot. Parent workspace text preserves fixture CRLF on both platforms; only child generated text changes. No source patch, sleeps or output normalization.',
        next_dispatch_budget=dict(target_jobs=1,standard_hosted=True,estimated_minutes=6,job_ceiling_minutes=30,
            automatic_harness_jobs=3,harness_job_ceiling_minutes=5,harness_max_parallel=2),project_admissions=0))
    print('Independently verified actual18/2, original screens,402source blobs,all20 launch identities/cleanups and native removal; declared additive profile2.')


if __name__=='__main__':main()
