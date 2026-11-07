"""Run baseline, corrupted, and restored calibration for three real Skim faults."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import uuid

from adversarial_process import execute
from next20_check import RAW, ROOT, NextCampaign
from next20_candidate import executable
from next20_rust_fetch import environment, short_owned_path
from readiness_build_plop import usage
from readiness_evidence import immutable_json, sha256


async def build(command, source, target, env, label):
    task = asyncio.create_task(execute(command, 'skim', label, cwd=source, env=env,
        timeout=1800, output_cap=2*1024*1024, campaign=NextCampaign(phase='final-archive')))
    samples = []
    try:
        while not task.done():
            current = await asyncio.to_thread(usage, RAW)
            samples.append(current)
            if current > 3*1024**3:
                raise RuntimeError('Skim final fault build exceeded the 3 GiB raw ceiling')
            await asyncio.sleep(2)
        result = await task
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    return result, samples


def case_record(label):
    matches = []
    evidence = RAW / 'active/skim/case-evidence'
    for path in evidence.glob('*/finished.json'):
        row = json.loads(path.read_text(encoding='utf-8'))
        if row.get('label') == label:
            matches.append((path, row))
    if len(matches) != 1:
        raise ValueError(f'{label}: expected exactly one immutable finished event')
    return matches[0]


async def run_case(host, candidate, contract, label, expected_pass, expected_target_sha,
                   expected_failure_category=None):
    target = RAW / 'active/skim'
    command = [sys.executable, '-B', 'scripts/acceptance/next20_playtestr_case.py',
        '--project', 'skim', '--label', label, '--candidate-series', 'native-exit-v1',
        '--target-binary', (target/'bin/sk.exe').relative_to(ROOT).as_posix(),
        '--', contract.relative_to(ROOT).as_posix()]
    result = subprocess.run(command, cwd=ROOT, check=False, timeout=360,
        capture_output=True, text=True, encoding='utf-8', errors='replace', env=os.environ.copy())
    path, finished = case_record(label)
    report = finished.get('report') or {}
    row = (report.get('results') or [{}])[0]
    steps = row.get('steps', [])
    event = json.loads((RAW/'events'/f"{finished.get('runner_attempt_id')}-finished.json").read_text(encoding='utf-8'))
    observed = dict(label=label, process_exit=result.returncode,
        finished_path=path.relative_to(ROOT).as_posix(), finished_sha256=sha256(path),
        report_sha256=finished.get('report_sha256'), status=finished.get('status'),
        runner_candidate_series=finished.get('runner_candidate_series'),
        runner_candidate_sha256=finished.get('runner_candidate_sha256'),
        expected_runner_sha256=sha256(candidate), target_binary_sha256=finished.get('target_binary_sha256'),
        expected_target_sha256=expected_target_sha, target_exit=(row.get('target') or {}).get('exit_code'),
        failure=(row.get('failure') or {}), step_statuses=[step.get('status') for step in steps],
        workspace_cleaned=(row.get('workspace') or {}).get('cleaned'),
        target_cleanup_confirmed=(row.get('cleanup') or {}).get('confirmed_exited'),
        harness_cleanup=event.get('harness_cleanup'), cleanup_errors=event.get('cleanup_errors', []),
        console=finished.get('console'), stderr=result.stderr[-8192:])
    if observed['runner_candidate_series'] != 'native-exit-v1' or observed['runner_candidate_sha256'] != sha256(candidate):
        raise ValueError(label+': exact rc.6 runner identity mismatch')
    if observed['target_binary_sha256'] != expected_target_sha:
        raise ValueError(label+': target build identity mismatch')
    if observed['workspace_cleaned'] is not True or observed['target_cleanup_confirmed'] is not True or observed['cleanup_errors']:
        raise ValueError(label+': incomplete target/process/workspace cleanup')
    if expected_pass:
        if (result.returncode != 0 or observed['status'] != 'completed' or
                row.get('status') != 'passed' or not steps or any(step.get('status') != 'passed' for step in steps)):
            raise ValueError(label+': baseline/restored control did not positively pass')
    else:
        if (result.returncode == 0 or observed['status'] != 'failed' or row.get('status') != 'failed' or
                not any(step.get('status') == 'failed' for step in steps)):
            raise ValueError(label+': mutated source escaped the unchanged public contract')
        if observed['failure'].get('category') != expected_failure_category:
            raise ValueError(label+': mutation failed for an unexpected reason; expected '+
                             repr(expected_failure_category)+', observed '+
                             repr(observed['failure'].get('category')))
    return observed


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['linux', 'windows'], required=True)
    parser.add_argument('--candidate-series', choices=['native-exit-v1'], required=True)
    args = parser.parse_args()
    host = {'Windows':'windows', 'Linux':'linux'}.get(platform.system())
    if host != args.host:
        raise ValueError('fault calibration must run on its declared native host')
    package = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass/skim'
    target = RAW / 'active/skim'
    source = target / 'src'
    build_path = target / 'build.json'
    build_record = json.loads(build_path.read_text(encoding='utf-8'))
    candidate = executable(args.candidate_series, host)
    declaration_path = package / 'fault-declaration-final-v1.json'
    declaration = json.loads(declaration_path.read_text(encoding='utf-8'))
    provenance = json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
    if (declaration.get('pin') != build_record.get('pin') or
            declaration.get('source_provenance_sha256') != sha256(package/'source-provenance.json') or
            declaration.get('phases') != ['baseline', 'corrupted', 'restored'] or
            len(declaration.get('faults', [])) != 3):
        raise ValueError('final Skim source-fault declaration differs from reviewed pin/profile')
    original_binary = target / 'bin/sk.exe'
    original_digest = sha256(original_binary)
    if original_digest != build_record['binary_sha256']:
        raise ValueError('original pinned target binary differs from build receipt')
    original_build_bytes = build_path.read_bytes()
    backup_binary = target / 'fault-calibration-original-sk.exe'
    backup_build = target / 'fault-calibration-original-build.json'
    if backup_binary.exists() or backup_build.exists():
        raise ValueError('preserve existing fault-calibration backup; no overwrite')
    backup_binary.write_bytes(original_binary.read_bytes())
    backup_build.write_bytes(original_build_bytes)

    env = environment(target)
    compiler = Path(build_record['compiler_path'])
    cargo = Path(build_record['cargo_path'])
    if sha256(compiler) != build_record['compiler_sha256'] or sha256(cargo) != build_record['cargo_sha256']:
        raise ValueError('pinned Rust compiler/cargo changed after target build')
    env.update(RUSTC=str(compiler), RUSTDOC=str(compiler.with_name('rustdoc.exe' if host == 'windows' else 'rustdoc')),
        CARGO_NET_OFFLINE='true', SOURCE_DATE_EPOCH='1793030400',
        CARGO_HOME=str(target/'cargo-home'), CARGO_TARGET_DIR=str(target/'cargo-target'))
    env['PATH'] = str(compiler.parent) + os.pathsep + env['PATH']
    if host == 'windows':
        for key in ('CARGO_HOME','CARGO_TARGET_DIR','TEMP','TMP','TMPDIR'):
            env[key] = short_owned_path(env[key])
    command = [cargo,'build','--release','--locked','--offline','--target',build_record['native_triple'],
        '--no-default-features','--features','cli,frizbee','--bin','sk']
    originals = {}
    for fault in declaration['faults']:
        path = source/fault['source']
        data = path.read_bytes()
        expected = provenance['files'].get(fault['source'])
        text = data.decode('utf-8')
        if sha256(path) != expected or text.count(fault['old']) != fault['expected_anchor_count']:
            raise ValueError(fault['id']+': source provenance/anchor differs before fault series')
        originals[fault['source']] = data
    calibration_root = RAW/'skim'/'fault-calibrations-native-exit-v1'/host
    calibration_root.mkdir(parents=True, exist_ok=False)
    calibrated = []
    faults = declaration['faults']
    try:
        for fault in faults:
            source_path = source / fault['source']
            original = originals[fault['source']]
            text = original.decode('utf-8')
            if text.count(fault['old']) != fault['expected_anchor_count']:
                raise ValueError(fault['id']+': mutation anchor count differs')
            mutated = text.replace(fault['old'], fault['new']).encode('utf-8')
            if mutated == original:
                raise ValueError(fault['id']+': empty mutation')
            stem = fault['id'].lower()
            contract = package/fault['contract']
            base = await run_case(host, candidate, contract, f'skim-final-fault-{stem}-baseline', True, original_digest)
            start = dict(schema_version=1, project='skim', host=host, fault=fault['id'],
                source_path=fault['source'], original_source_sha256=sha256(source_path),
                mutated_source_sha256=__import__('hashlib').sha256(mutated).hexdigest(),
                candidate_sha256=sha256(candidate), case=fault['case'], contract=contract.relative_to(ROOT).as_posix(),
                contract_sha256=sha256(contract), started_before_mutation=True, baseline=base)
            immutable_json(calibration_root/(stem+'-started.json'), start)
            source_path.write_bytes(mutated)
            if sha256(source_path) != start['mutated_source_sha256']:
                raise ValueError(fault['id']+': mutation write differs')
            mutant_build, mutant_samples = await build(command, source, target, env, 'final-mutant-build-'+stem)
            built = target/'cargo-target'/build_record['native_triple']/'release'/('sk.exe' if host=='windows' else 'sk')
            if not built.is_file():
                raise ValueError(fault['id']+': native mutant build omitted target')
            mutant_digest = sha256(built)
            if mutant_digest == original_digest:
                raise ValueError(fault['id']+': source mutation did not change executable bytes')
            shutil.copyfile(built, original_binary)
            mutant_record = dict(build_record, binary_sha256=mutant_digest, build_attempt=mutant_build['id'],
                source_mutation=fault['id'], source_mutant_sha256=start['mutated_source_sha256'],
                mutation_command=command)
            build_path.write_text(json.dumps(mutant_record, indent=2)+'\n', encoding='utf-8')
            corrupted = await run_case(host, candidate, contract,
                f'skim-final-fault-{stem}-corrupted', False, mutant_digest,
                fault['expected_failure_category'])
            source_path.write_bytes(original)
            if sha256(source_path) != provenance['files'][fault['source']]:
                raise ValueError(fault['id']+': source restoration failed')
            restored_build, restored_samples = await build(command, source, target, env, 'final-restored-build-'+stem)
            restored_built = target/'cargo-target'/build_record['native_triple']/'release'/('sk.exe' if host=='windows' else 'sk')
            if not restored_built.is_file() or sha256(restored_built) != original_digest:
                raise ValueError(fault['id']+': restored target did not rebuild byte-identically')
            shutil.copyfile(backup_binary, original_binary)
            build_path.write_bytes(original_build_bytes)
            restored = await run_case(host, candidate, contract, f'skim-final-fault-{stem}-restored', True, original_digest)
            result = dict(fault=fault['id'], phases={'baseline':base,'corrupted':corrupted,'restored':restored},
                source_original_sha256=start['original_source_sha256'], source_mutant_sha256=start['mutated_source_sha256'],
                mutant_binary_sha256=mutant_digest, mutant_build_attempt=mutant_build['id'],
                restored_build_attempt=restored_build['id'], restored_binary_sha256=sha256(restored_built),
                mutant_build_storage_samples=mutant_samples, restored_build_storage_samples=restored_samples,
                source_restored=True, detected=True)
            immutable_json(calibration_root/(stem+'-finished.json'), result)
            calibrated.append(result)
            print('Calibrated', fault['id'], 'baseline/corrupted/restored on', host, flush=True)
    finally:
        for name, original in originals.items():
            (source/name).write_bytes(original)
        if backup_binary.is_file() and backup_build.is_file():
            shutil.copyfile(backup_binary, original_binary)
            build_path.write_bytes(original_build_bytes)
    if len(calibrated) != 3 or sha256(original_binary) != original_digest:
        raise ValueError('final Skim target/source restoration or fault count failed')
    check = subprocess.run([sys.executable,'-B','scripts/acceptance/next20_skim_source_verify.py','--verify-only'],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    if check.returncode:
        raise RuntimeError('restored final Skim source differs from pin: '+check.stdout+check.stderr)
    backup_binary.unlink()
    backup_build.unlink()
    out = calibration_root/'summary.json'
    immutable_json(out, dict(schema_version=1,project='skim',host=host,candidate_series='native-exit-v1',
        candidate_sha256=sha256(candidate),source_pin=build_record['pin'],fault_declaration_sha256=sha256(declaration_path),
        distinct_faults=3,phases=9,baseline_passes=3,mutations_detected=3,restored_recovery_passes=3,
        source_restored=True,target_binary_restored=True,observations=calibrated,
        post_run_source_verification=check.stdout.strip(),project_admissions=0))
    print('Skim final source-fault matrix: 3/3 detected; 9/9 phases; exact source and target restored.')


if __name__ == '__main__':
    asyncio.run(main())
