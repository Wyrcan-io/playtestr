"""Execute the predeclared whole Hatch final cell without per-case retries."""
import asyncio
import json
import platform
import sys

from adversarial_process import execute
from next20_check import DOC,RAW,ROOT,NextCampaign,owned_environment
from next20_jrnl_final import main as final_batch
from readiness_evidence import immutable_json,sha256


async def main():
    package=DOC/'hatch';target=RAW/'active/hatch';contracts=RAW/'hatch/host-contracts';host={'Windows':'windows','Linux':'linux'}[platform.system()]
    path=package/'final-series-declaration-native-exit-v1.json';declaration=json.loads(path.read_text());frozen=json.loads((contracts/'development-test-freeze.json').read_text())
    if (declaration['canonical_test_freeze_sha256']!=sha256(package/'development-test-freeze.json') or
        declaration['native_runtime_lock_sha256']!=sha256(package/'native-runtime-lock.json') or
        frozen['canonical_freeze_sha256']!=sha256(package/'development-test-freeze.json')):raise ValueError('actual final profile/freeze differs')
    if host=='windows' and frozen.get('explicit_profile_sha256')!=declaration['windows_profile_sha256']:raise ValueError('wrong actual Windows application profile')
    for name,digest in frozen['inputs'].items():
        if sha256(contracts/name)!=digest:raise ValueError('final host input changed')
    plan=RAW/'hatch/final-execution-plan.json'
    immutable_json(plan,dict(schema_version=1,host=host,declaration_sha256=sha256(path),runtime_sha256=sha256(target/'runtime.json'),
        build_sha256=sha256(target/'build.json'),host_freeze_sha256=sha256(contracts/'development-test-freeze.json'),expected_ordinary=240,expected_calibrations=9,project_admissions=0))
    for batch in range(12):
        await final_batch('hatch',batch=batch,candidate_series='native-exit-v1')
        print('Completed fresh final Hatch batch',batch+1,'of12;',host,flush=True)
    before=set((RAW/'hatch/faults').glob('*/summary.json'));env=owned_environment();env['READINESS_EVIDENCE_PHASE']='final-archive'
    calibration=await execute([sys.executable,'-B',ROOT/'scripts/acceptance/next20_python_faults.py','hatch','--candidate-series','native-exit-v1','--package',contracts],
        'hatch','final-hatch-three-real-source-faults',cwd=ROOT,env=env,timeout=600,campaign=NextCampaign(phase='final-archive'))
    after=set((RAW/'hatch/faults').glob('*/summary.json'))-before
    if len(after)!=1:raise ValueError('one new final source-fault series required')
    fault_path=after.pop();faults=json.loads(fault_path.read_text())
    if faults['calibrations']!=9 or faults['real_faults']!=3 or faults['phase']!='final-archive':raise ValueError('wrong final calibration denominator/phase')
    primary=json.loads((package/'source-provenance.json').read_text())['files']
    for name,digest in primary.items():
        if sha256(target/'src'/name)!=digest:raise ValueError('final source not restored exactly')
    summaries=[RAW/'hatch/final-series-native-exit-v1'/str(i)/'summary.json' for i in range(12)]
    immutable_json(RAW/'hatch/final-execution-summary.json',dict(schema_version=1,host=host,plan_sha256=sha256(plan),declaration_sha256=sha256(path),
        batches={p.relative_to(RAW).as_posix():sha256(p) for p in summaries},ordinary_executions=240,calibrations=9,
        calibration_wrapper=calibration['id'],fault_summary=fault_path.relative_to(RAW).as_posix(),fault_summary_sha256=sha256(fault_path),
        primary_source_restored=True,project_admissions=0,scope='Complete execution only; independent all-report/prelaunch/source/runtime audit and retained evidence/cleanup required before admission.'))
    print('Executed240 ordinary and9 fresh calibrations on',host,'with exact source restoration; no admission.')


if __name__=='__main__':asyncio.run(main())
