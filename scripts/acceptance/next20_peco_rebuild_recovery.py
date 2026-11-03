"""Execute fresh, explicitly exposed normal-rebuild calibration triples."""
import asyncio
import json
import platform
import sys

from adversarial_process import execute
from next20_check import DOC, RAW, ROOT, NextCampaign, owned_environment
from readiness_evidence import immutable_json, sha256


async def main():
    host={'Windows':'windows','Linux':'linux'}[platform.system()];package=DOC/'peco'
    declaration_path=package/'rebuild-recovery-declaration-v1.json';declaration=json.loads(declaration_path.read_text())
    target=RAW/'active/peco';contracts=RAW/'peco'/('host-contracts-rebuild-v1' if host=='windows' else 'host-contracts')
    build=json.loads((target/'build.json').read_text());runtime=json.loads((target/'runtime.json').read_text())
    if declaration['gate_sha256']!=sha256(package/'restoration-rebuild-gate.json') or declaration['canonical_freeze_sha256']!=sha256(package/'development-test-freeze.json'):
        raise ValueError('normal rebuild correction declaration differs')
    expected=declaration['original_baseline'][host]
    if build['actual_target_sha256']!=expected['app_sha256'] or build['binary_sha256']!=expected['capture_sha256'] or build['compiler_sha256']!=expected['compiler_sha256']:
        raise ValueError('actual baseline/prerequisite changed; retain for explicit investigation')
    plan=RAW/'peco/rebuild-recovery-execution-plan-v1.json'
    immutable_json(plan,dict(schema_version=1,host=host,declaration_sha256=sha256(declaration_path),runtime_sha256=sha256(target/'runtime.json'),build_sha256=sha256(target/'build.json'),
        host_freeze_sha256=sha256(contracts/'development-test-freeze.json'),
        **(dict(retained_input_materialization_sha256=sha256(RAW/'peco/rebuild-materialization-complete-v1.json')) if host=='windows' else {}),
        expected_calibrations=9,expected_normal_rebuilds=3,ordinary_credit=0,project_admissions=0))
    before=set((RAW/'peco/faults').glob('*/summary.json'));env=owned_environment();env['READINESS_EVIDENCE_PHASE']='final-archive'
    result=await execute([sys.executable,'-B',ROOT/'scripts/acceptance/next20_go_faults.py','peco','--final','--package',contracts],
        'peco','fresh-normal-rebuild-recovery-three-source-fault-triples',cwd=ROOT,env=env,timeout=900,campaign=NextCampaign(phase='final-archive'))
    after=set((RAW/'peco/faults').glob('*/summary.json'))-before
    if len(after)!=1:raise ValueError('one new normal-rebuild calibration window required')
    summary_path=after.pop();summary=json.loads(summary_path.read_text())
    if summary['calibrations']!=9 or summary['normal_restoration_rebuilds']!=3 or not all(f['normal_rebuild_recovery_executed'] for f in summary['faults']):raise ValueError('normal rebuild recovery incomplete')
    immutable_json(RAW/'peco/rebuild-recovery-summary-v1.json',dict(schema_version=1,host=host,plan_sha256=sha256(plan),declaration_sha256=sha256(declaration_path),
        execution_wrapper=result['id'],fault_summary=summary_path.relative_to(RAW).as_posix(),fault_summary_sha256=sha256(summary_path),calibrations=9,normal_restoration_rebuilds=3,
        actual_rebuilt_images=[dict(fault=f['id'],sha256=f['restored_binary_sha256'],matches_original=f['rebuilt_binary_matches_baseline'],receipt=f['normal_rebuild_receipt'],receipt_sha256=f['normal_rebuild_receipt_sha256']) for f in summary['faults']],
        source_and_ordinary_image_restored_at_end=summary['source_and_binary_restored_exact'],ordinary_credit=0,project_admissions=0,
        scope='Fresh explicitly exposed triples with actual normal rebuilt recovery images. Prior copied-binary recovery phases remain retained,not relabeled as rebuilt. Independent readback,retention and new checked cleanup required before resolving gate.'))
    print('Executed9fresh phases with3actual normal restored-source rebuilds on',host,'; independent correction audit and cleanup still required.')


if __name__=='__main__':asyncio.run(main())
