"""Execute a predeclared fresh final PDM cell without per-case retries."""
import asyncio
import json
import os
import platform
import sys

from adversarial_process import execute
from next20_check import DOC, RAW, ROOT, NextCampaign, owned_environment
from next20_jrnl_final import main as final_batch
from readiness_evidence import immutable_json, sha256


async def main():
    package=DOC/'pdm';target=RAW/'active/pdm';host={'Windows':'windows','Linux':'linux'}[platform.system()]
    path=package/'final-series-declaration-native-exit-v1.json';declaration=json.loads(path.read_text())
    contracts=RAW/'pdm/host-contracts';frozen=json.loads((contracts/'development-test-freeze.json').read_text())
    profile=package/('windows-profile-v1.json' if host=='windows' else 'native-profile-v2.json')
    if (declaration['canonical_test_freeze_sha256']!=sha256(package/'development-test-freeze.json') or
            declaration[host+'_profile_sha256']!=sha256(profile) or frozen.get('explicit_profile_sha256')!=sha256(profile)):
        raise ValueError('final host profile is not the declared exact input')
    for name,digest in frozen['inputs'].items():
        if sha256(contracts/name)!=digest:raise ValueError('native input changed before final series')
    plan=RAW/'pdm/final-execution-plan.json'
    immutable_json(plan,dict(schema_version=1,host=host,declaration_sha256=sha256(path),runtime_sha256=sha256(target/'runtime.json'),
        build_sha256=sha256(target/'build.json'),native_freeze_sha256=sha256(contracts/'development-test-freeze.json'),
        expected_ordinary=240,expected_calibrations=9,project_admissions=0))
    for batch in range(12):
        await final_batch('pdm',batch=batch,candidate_series='native-exit-v1')
        print('Completed fresh final batch',batch+1,'of12;',host,flush=True)
    before=set((RAW/'pdm/faults').glob('*/summary.json'))
    env=owned_environment();env['READINESS_EVIDENCE_PHASE']='final-archive'
    calibration=await execute([sys.executable,'-B',ROOT/'scripts/acceptance/next20_python_faults.py','pdm',
        '--candidate-series','native-exit-v1','--package',contracts],'pdm','final-pdm-three-real-source-faults',
        cwd=ROOT,env=env,timeout=600,campaign=NextCampaign(phase='final-archive'))
    after=set((RAW/'pdm/faults').glob('*/summary.json'))-before
    if len(after)!=1:raise ValueError('exactly one fresh complete source-fault series required')
    fault_path=after.pop();faults=json.loads(fault_path.read_text())
    if faults['calibrations']!=9 or faults['real_faults']!=3 or faults['phase']!='final-archive':raise ValueError('wrong fresh source-fault phase/count')
    primary=json.loads((package/'source-provenance.json').read_text())['files']
    for name,digest in primary.items():
        if sha256(target/'src'/name)!=digest:raise ValueError('final source restoration differs')
    summaries=[RAW/'pdm/final-series-native-exit-v1'/str(i)/'summary.json' for i in range(12)]
    immutable_json(RAW/'pdm/final-execution-summary.json',dict(schema_version=1,host=host,
        plan_sha256=sha256(plan),declaration_sha256=sha256(path),
        batches={p.relative_to(RAW).as_posix():sha256(p) for p in summaries},ordinary_executions=240,
        calibrations=9,calibration_wrapper=calibration['id'],fault_summary=fault_path.relative_to(RAW).as_posix(),
        fault_summary_sha256=sha256(fault_path),primary_source_restored=True,historical_screen_gap_open=True,
        project_admissions=0,scope='Complete cell execution only; independent report/identity audit,retention and checked source/runtime removal remain required.'))
    print('Executed240 ordinary and9 fresh calibrations on',host,'with exact source restoration; no project admission.')


if __name__=='__main__':asyncio.run(main())
