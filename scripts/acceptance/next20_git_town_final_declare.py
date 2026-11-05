"""Freeze the finite Git Town exact-candidate native series without launching targets."""
import json

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def main():
    package = DOC / 'git-town'
    catalog_path = package / 'scenario-catalog-v3.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    scenarios = catalog['scenarios']
    if (len(scenarios) != 20 or sum(row['class'] == 'normal' for row in scenarios) != 8 or
            sum(row['class'] == 'edge' for row in scenarios) != 12):
        raise ValueError('Git Town source-development catalog is not the frozen 8/12, 20-case matrix')
    cases = []
    inputs = {}
    for row in scenarios:
        spec = package / row['spec']
        if sha256(spec) != row['spec_sha256']:
            raise ValueError('Git Town catalog spec changed: ' + row['spec'])
        cases.append(dict(id=row['id'], spec=row['spec'], spec_sha256=row['spec_sha256'],
                          canonical_sha256=row['spec_sha256']))
        inputs[row['spec']] = row['spec_sha256']
    fixture = package / 'fixtures' / 'branch-repo'
    if fixture.is_symlink():
        raise ValueError('Git Town canonical fixture is a link')
    seed = fixture / 'README.md'
    if not seed.is_file() or seed.is_symlink() or seed.read_bytes() != b'Synthetic Git Town repository.\n':
        raise ValueError('Git Town reviewed synthetic fixture seed differs')
    recipe = package / 'source-fixture-recipe-v1.json'
    immutable_json(recipe, dict(schema_version=1, project='git-town',
        source_pin='8d039892574d4852e1843020c31d423234042e78', initial_branch='main',
        secondary_branch='feat-blue', remote_count=0, seed_path='fixtures/branch-repo/README.md',
        seed_sha256=sha256(seed), source='next20_git_town_fixture.py',
        fixture_policy='Host generates its own synthetic Git metadata, then freezes exact runtime fixture bytes in the host contract manifest.'))
    inputs['fixtures/branch-repo/README.md'] = sha256(seed)
    inputs['source-fixture-recipe-v1.json'] = sha256(recipe)
    scenarios_path = package / 'scenarios.json'
    immutable_json(scenarios_path, dict(schema_version=1, project='git-town',
        source_catalog='scenario-catalog-v3.json', source_catalog_sha256=sha256(catalog_path),
        cases=cases))
    inputs['scenarios.json'] = sha256(scenarios_path)
    directories = ['fixtures/branch-repo']
    positive = dict(source_development_run='41947116665', independent_audit_run='41949100190',
        source_pin='8d039892574d4852e1843020c31d423234042e78', source_files=4533,
        passed_scenarios_per_host=20, source_fault_phases_per_host=9)
    immutable_json(package / 'development-test-freeze.json', dict(schema_version=1,
        project='git-town', status='frozen-for-private-candidate-series',
        inputs=dict(sorted(inputs.items())), directories=sorted(directories),
        scenarios_sha256=sha256(scenarios_path), scenario_catalog_sha256=sha256(catalog_path),
        fixture_manifest_sha256=sha256(recipe),
        positive_development_summary=positive, final_ordinary_credit=0))
    immutable_json(package / 'native-runtime-lock.json', dict(schema_version=1,
        project='git-town', repository='git-town/git-town', pin='8d039892574d4852e1843020c31d423234042e78',
        expected_version='Git Town 24.1.0', go_version='go1.27.0',
        build='go build -mod=vendor -trimpath -buildvcs=false',
        dependency_mode='Vendored pinned Go workspace; GOPROXY=off; GOSUMDB=off; GOTOOLCHAIN=local',
        source_provenance_sha256=sha256(package / 'source-provenance.json'),
        compiled_payload='single native Git Town executable; dynamic library dependencies excluded from runtime claim'))
    inherited_batches = [
        dict(id=0, name='ordinary-cold-1', runtime='new verified owned binary copy; first logical use'),
        dict(id=1, name='ordinary-warm-1', runtime='reuse exact binary copy from batch 0'),
        dict(id=2, name='ordinary-cold-2', runtime='second independently verified owned binary copy'),
        dict(id=3, name='ordinary-warm-2', runtime='reuse exact binary copy from batch 2'),
        dict(id=4, name='viewport', change='width +10 and height +2; frozen state bytes retained'),
        dict(id=5, name='spaced-unicode-path', change='contracts relocated under a relative path with spaces and Unicode'),
        dict(id=6, name='ordinary-input-readiness', change='same frozen supported actions and positive checkpoints'),
        dict(id=7, name='segmented-printable-input', change='printable input sent in three-codepoint groups'),
        dict(id=8, name='bounded-contention-1', change='first bounded owned CPU and memory contention window'),
        dict(id=9, name='bounded-contention-2', change='second independent bounded contention window'),
        dict(id=10, name='highest-risk-small-completion', change='N01 viewport height 12; all other contracts unchanged'),
        dict(id=11, name='highest-risk-startup-boundary', change='2000 ms declared startup boundary; ordinary budgets unchanged')]
    freeze_candidate = DOC / 'replacement-candidate-freeze-native-exit-v1.json'
    faults = package / 'fault-declaration-v4.json'
    harness_paths = [
        '.github/workflows/runner-readiness-next20-git-town-final.yml',
        'scripts/acceptance/next20_git_town_case.py',
        'scripts/acceptance/next20_git_town_faults.py',
        'scripts/acceptance/next20_git_town_fixture.py',
        'scripts/acceptance/next20_git_town_final_contracts.py',
        'scripts/acceptance/next20_git_town_final_series.py',
        'scripts/acceptance/next20_git_town_prepare.py',
        'scripts/acceptance/test_next20_git_town_faults.py',
        'scripts/acceptance/test_git_town_artifact_audit.py',
        'scripts/acceptance/test_next20_target_cleanup.py',
        'scripts/acceptance/next20_jrnl_final.py',
        'scripts/acceptance/next20_candidate.py',
        'scripts/acceptance/next20_candidate_install.py',
        'scripts/acceptance/next20_check.py',
        'scripts/acceptance/adversarial_process.py',
        'scripts/acceptance/readiness_evidence.py',
        'scripts/acceptance/next20_target_cleanup.py',
        'scripts/acceptance/next20_target_process_proof.ps1',
        'scripts/acceptance/next20_remove_target.ps1',
        'scripts/acceptance/next20_batch_snapshots.py',
        'scripts/acceptance/next20_python_runtime.py',
    ]
    harness_hashes = {name: sha256(ROOT / name) for name in harness_paths}
    declaration = dict(schema_version=1, project='git-town', revision=1,
        hosts=['linux', 'windows'], candidate='v0.4.0-rc.6', candidate_series='native-exit-v1',
        candidate_freeze_sha256=sha256(freeze_candidate),
        candidate_provider_runs={'linux': '40424475362', 'windows': '40425810038'},
        canonical_test_freeze_sha256=sha256(package / 'development-test-freeze.json'),
        native_runtime_lock_sha256=sha256(package / 'native-runtime-lock.json'),
        source_pin='8d039892574d4852e1843020c31d423234042e78',
        source_provenance_sha256=sha256(package / 'source-provenance.json'),
        scenario_catalog_sha256=sha256(catalog_path), fault_declaration_sha256=sha256(faults),
        independent_source_development_audit='retention-readback-v14.json',
        independent_source_development_audit_sha256=sha256(package / 'retention-readback-v14.json'),
        harness_files=harness_hashes,
        batches=inherited_batches, scenarios_per_cell=20, normal=8, edge=12,
        repetitions_per_cell=12, ordinary_required=480, real_source_faults=3,
        required_three_phase_calibrations=18, calibration_required=18,
        startup_timeout_ms_by_host={'linux': 2000, 'windows': 2000},
        cold_scope='Two newly materialized and hash-verified target executable copies followed by paired reuse; no claim of OS page-cache eviction.',
        failure_policy='No per-case retry. Any failed report, timeout, exit, cleanup, hash or series completeness check invalidates the host cell; retain attempts and require a declared replacement.',
        original_failures='Preserve all v1/v2 hosted startup and Unicode failures plus the v3 Linux PTY bridge failure; catalog v3/source development then passed and was independently audited. A native local Windows exact-candidate preflight was refused before target launch because the deep workspace path returned Access is denied; standard hosted Windows is the declared final host.',
        transfer_scope='Pinned source and three faults already exposed on Linux and Windows; final-candidate observations remain separately required.',
        retention=dict(per_project_cap_bytes=64*1024*1024, source_payload_retained_once=True,
                       native_binary_payload_policy='Retain exact original candidate reference and byte hash; never duplicate full provider archives.'),
        execution_budget=dict(hosted_jobs=2, max_parallel=2, job_ceiling_minutes=60,
                              total_job_minute_ceiling=120, paid_runner_budget_changes=0),
        project_admissions=0,
        scope='Exact v0.4.0-rc.6 native-exit-v1 final execution only. Independent report/fault/source/runtime audit, old-project requalification, retention and confirmed cleanup remain required before admission.')
    declaration_path = package / 'final-series-declaration-native-exit-v1.json'
    immutable_json(declaration_path, declaration)
    print('Declared Git Town exact rc.6 series: 12 batches x 20 cases per host, 480 executions and 18 calibrations per host; zero admission credit.')


if __name__ == '__main__':
    main()
