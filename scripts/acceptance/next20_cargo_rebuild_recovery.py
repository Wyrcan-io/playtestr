"""Execute the declared Cargo normal-rebuild supplement without ordinary reruns."""
import asyncio
import argparse
import json
import os
import shutil
import sys

from adversarial_process import execute
from next20_check import DOC, RAW, ROOT, NextCampaign, owned_environment
from readiness_evidence import immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--window',type=int,choices=[1,2],default=1);args=parser.parse_args()
    host = 'windows' if os.name == 'nt' else 'linux'
    if args.window!=1 and host!='windows':raise ValueError('replacement window is Windows-only')
    package = DOC / 'cargo-generate'
    declaration_path = package / 'rebuild-recovery-declaration-v1.json'
    declaration = json.loads(declaration_path.read_text())
    target = RAW / 'active/cargo-generate'
    build = json.loads((target / 'build.json').read_text())
    if build['binary_sha256'] != declaration['original_baseline'][host] or declaration['gate_sha256'] != sha256(package / 'restoration-rebuild-gate.json'):
        raise ValueError('original baseline or proof-correction declaration differs; investigate before calibration')
    contracts = RAW / 'cargo-generate/host-contracts-rebuild-v1'
    if host == 'linux':
        if contracts.exists():
            raise ValueError('preserve original correction contract attempt')
        shutil.copytree(RAW / 'cargo-generate/host-contracts', contracts)
    profile = json.loads((contracts / 'scenarios.json').read_text())
    if profile['native_binary_sha256'] != build['binary_sha256']:
        raise ValueError('correction contract baseline differs')
    if args.window==2:
        replacement=package/'rebuild-recovery-replacement-declaration-v2.json';changed=json.loads(replacement.read_text())
        if changed['preparation_receipt_sha256']!=sha256(RAW/'cargo-generate/rebuild-preparation-v1/compiled.json'):raise ValueError('replacement preparation binding differs')
    suffix='v'+str(args.window)
    plan = RAW / ('cargo-generate/rebuild-recovery-execution-plan-'+suffix+'.json')
    immutable_json(plan, dict(schema_version=1, host=host, declaration_sha256=sha256(declaration_path),
        binary_retention_declaration_sha256=sha256(package / 'rebuild-binary-retention-declaration-v1.json'),
        actual_baseline_sha256=build['binary_sha256'], build_sha256=sha256(target / 'build.json'),
        runtime_sha256=sha256(target / 'runtime.json'), host_profile_sha256=sha256(contracts / 'scenarios.json'),
        **(dict(replacement_declaration_sha256=sha256(replacement),preparation_receipt_sha256=changed['preparation_receipt_sha256']) if args.window==2 else {}),
        ordinary_credit=0, expected_calibrations=9, expected_normal_restoration_rebuilds=3, project_admissions=0))
    result = await execute([sys.executable, '-B', ROOT / 'scripts/acceptance/next20_cargo_faults.py', '--native-final', '--normal-rebuild-window', '--normal-rebuild-window-number',str(args.window)],
        'cargo-generate', 'fresh-normal-restored-rust-source-rebuild-triples', cwd=ROOT,
        env=owned_environment(), timeout=1100, campaign=NextCampaign(phase='final-archive'))
    path = RAW / ('cargo-generate/source-fault-rebuild-recovery-'+suffix+'/summary.json')
    summary = json.loads(path.read_text())
    if summary['normal_restoration_rebuilds'] != 3 or summary['new_compiles'] != 6 or summary['final_native_calibration_executions'] != 9:
        raise ValueError('normal restored-source rebuild phases incomplete')
    if not all(row['normal_rebuild_recovery_executed'] for row in summary['observations']):
        raise ValueError('copied-image recovery cannot qualify as normal rebuild')
    immutable_json(RAW / ('cargo-generate/rebuild-recovery-summary-'+suffix+'.json'), dict(schema_version=1, host=host, window=args.window,
        plan_sha256=sha256(plan), execution_wrapper=result['id'], fault_summary=path.relative_to(RAW).as_posix(),
        fault_summary_sha256=sha256(path), calibrations=9, normal_restoration_rebuilds=3,
        original_ordinary_unchanged=True, ordinary_credit=0, project_admissions=0,
        scope='Fresh exposed normal-rebuild supplement only; actual compiler/image/report/retention/cleanup audits remain required.'))
    print('Executed9fresh Cargo calibration phases and3normal restored-source rebuilds on', host)


if __name__ == '__main__':
    asyncio.run(main())
