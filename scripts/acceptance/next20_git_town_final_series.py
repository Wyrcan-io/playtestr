"""Execute a complete exact-archive Git Town final cell without retries."""
import asyncio
import hashlib
import json
import platform
import sys

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign, owned_environment
from next20_jrnl_final import main as final_batch
from next20_git_town_final_contracts import validate_scenario_alias
from readiness_evidence import immutable_json, sha256


def harness_sha(path):
    """Hash text harness bytes with CRLF/LF checkout differences normalized."""
    data = path.read_bytes()
    if path.suffix.lower() in {'.py', '.ps1', '.yml', '.yaml'}:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


async def main():
    package = DOC / 'git-town'
    target = RAW / 'active' / 'git-town'
    contracts = RAW / 'git-town' / 'host-contracts'
    host = {'Windows': 'windows', 'Linux': 'linux'}[platform.system()]
    declaration_path = package / 'final-series-declaration-native-exit-v31.json'
    declaration = json.loads(declaration_path.read_text(encoding='utf-8'))
    freeze_path = package / 'development-test-freeze-native-exit-v6.json'
    frozen = json.loads((contracts / 'development-test-freeze.json').read_text(encoding='utf-8'))
    build = json.loads((target / 'build.json').read_text(encoding='utf-8'))
    acquisition = json.loads((target / 'acquisition.json').read_text(encoding='utf-8'))
    runtime = json.loads((target / 'runtime.json').read_text(encoding='utf-8'))
    installed = json.loads((target / 'installed-inventory.json').read_text(encoding='utf-8'))
    native_lock = package / 'native-runtime-lock.json'
    scenario_catalog = package / 'scenario-catalog-v8.json'
    fault_declaration = package / 'fault-declaration-v9.json'
    candidate = executable('native-exit-v1', host)
    source_archive = target / 'source.tar.gz'
    if (acquisition.get('source_archive_method') !=
            'deterministic gzip/PAX archive generated from the verified pinned Git checkout' or
            sha256(source_archive) != acquisition.get('source_archive_sha256') or
            source_archive.stat().st_size != acquisition.get('source_archive_bytes')):
        raise ValueError('final Git Town source archive differs from its verified pinned checkout')
    for name, digest in declaration['harness_files'].items():
        if harness_sha(ROOT / name) != digest:
            raise ValueError('Git Town final harness changed after its declaration: ' + name)
    if (declaration['scenario_catalog'] != scenario_catalog.name or
            declaration['scenario_catalog_sha256'] != sha256(scenario_catalog) or
            declaration['fault_declaration_sha256'] != sha256(fault_declaration) or
            declaration['canonical_test_freeze_sha256'] != sha256(freeze_path) or
            declaration['native_runtime_lock_sha256'] != sha256(native_lock) or
            declaration['candidate_freeze_sha256'] != sha256(DOC / 'replacement-candidate-freeze-native-exit-v1.json') or
            frozen['canonical_freeze_sha256'] != sha256(freeze_path) or
            declaration['hosts'] != ['linux', 'windows'] or host not in declaration['hosts'] or
            declaration['ordinary_required'] != 480 or declaration['calibration_required'] != 18 or
            len(declaration['batches']) != 12):
        raise ValueError('actual Git Town final declaration/freeze/candidate differs')
    for name, digest in frozen['inputs'].items():
        if sha256(contracts / name) != digest:
            raise ValueError('final host input changed: ' + name)
    scenario_alias = contracts / 'scenarios.json'
    validate_scenario_alias('scenarios-native-exit-v6.json', scenario_alias, frozen['inputs'])
    for name, digest in build['compiled_files'].items():
        if sha256((target / 'bin' / name)) != digest:
            raise ValueError('native target runtime differs from its source build receipt: ' + name)
    plan = RAW / 'git-town' / 'final-execution-plan.json'
    immutable_json(plan, dict(schema_version=1, host=host,
        declaration_sha256=sha256(declaration_path), candidate_series='native-exit-v1',
        candidate_sha256=sha256(candidate), candidate_archive_sha256=json.loads(
            (candidate.parent / 'installed.json').read_text(encoding='utf-8'))['archive_sha256'],
        runtime_sha256=sha256(target / 'runtime.json'), build_sha256=sha256(target / 'build.json'),
        source_archive_sha256=acquisition['source_archive_sha256'],
        installed_inventory_sha256=sha256(target / 'installed-inventory.json'),
        host_freeze_sha256=sha256(contracts / 'development-test-freeze.json'),
        expected_ordinary=240, expected_calibrations=9, project_admissions=0))
    for batch in range(12):
        await final_batch('git-town', batch=batch, candidate_series='native-exit-v1',
                          startup_timeout_ms_by_host=declaration['startup_timeout_ms_by_host'],
                          declaration_path_override=declaration_path)
        print('Completed fresh final Git Town batch', batch + 1, 'of 12;', host, flush=True)
    env = owned_environment()
    env['READINESS_EVIDENCE_PHASE'] = 'final-archive'
    calibration = await execute([sys.executable, '-B', ROOT / 'scripts/acceptance/next20_git_town_faults.py',
        '--host', host, '--final', '--candidate-series', 'native-exit-v1'],
        'git-town', 'final-git-town-three-real-source-faults', cwd=ROOT, env=env,
        timeout=1200, campaign=NextCampaign(phase='final-archive'))
    fault_path = package / f'fault-matrix-{host}-final-v1.json'
    faults = json.loads(fault_path.read_text(encoding='utf-8'))
    if faults.get('candidate_runner_sha256') != sha256(candidate) or faults.get('phase') != 'final-archive':
        raise ValueError('final Git Town fault phases did not use the exact candidate')
    if faults['totals'] != dict(distinct_faults=3, phases=9, baseline_passes=3,
                                mutations_detected=3, restored_recovery_passes=3):
        raise ValueError('wrong final Git Town fault calibration denominator')
    provenance = json.loads((package / 'source-provenance.json').read_text(encoding='utf-8'))['files']
    for name, digest in provenance.items():
        if sha256(target / 'src' / name) != digest:
            raise ValueError('final Git Town source was not restored exactly: ' + name)
    for name, digest in build['compiled_files'].items():
        if sha256(target / 'bin' / name) != digest:
            raise ValueError('final Git Town executable was not restored exactly: ' + name)
    summaries = [RAW / 'git-town' / 'final-series-native-exit-v1' / str(i) / 'summary.json'
                 for i in range(12)]
    immutable_json(RAW / 'git-town' / 'final-execution-summary.json', dict(
        schema_version=1, host=host, plan_sha256=sha256(plan),
        declaration_sha256=sha256(declaration_path),
        batches={path.relative_to(RAW).as_posix(): sha256(path) for path in summaries},
        ordinary_executions=240, calibrations=9, calibration_wrapper=calibration['id'],
        fault_summary=fault_path.relative_to(ROOT).as_posix(), fault_summary_sha256=sha256(fault_path),
        primary_source_restored=True, target_executable_restored=True,
        candidate_series='native-exit-v1', candidate_sha256=sha256(candidate),
        project_admissions=0,
        scope='Finite final execution only; independent reports, fault, source/runtime, storage and cleanup audit remains required.'))
    print('Executed 240 candidate ordinary cases and 9 fresh source-fault calibrations on', host,
          'with exact source/executable restoration; no admission.')


if __name__ == '__main__':
    asyncio.run(main())
