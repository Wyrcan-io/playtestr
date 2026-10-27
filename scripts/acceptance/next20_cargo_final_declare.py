"""Freeze the concrete Windows-local/Linux-hosted480-run final native schedule."""
import copy
import json
import platform

from next20_check import RAW,ROOT,DOC
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'cargo-generate';candidate=DOC/'replacement-candidate-freeze-native-exit-v1.json'
    linux=package/'native-linux-preflight-reviewed-audit.json';observed=json.loads(linux.read_text())
    if observed['passed']!=20 or observed['failed']!=0:raise ValueError('complete reviewed Linux20/0 preflight first')
    target=RAW/'active/cargo-generate';build_path=target/'build.json';build=json.loads(build_path.read_text())
    runtime=json.loads((target/'runtime.json').read_text());binary=ROOT/(target/build['binary_relative_path']).relative_to(ROOT)
    if platform.system()!='Windows' or sha256(binary)!=build['binary_sha256'] or runtime['native_sha256']!=build['binary_sha256']:raise ValueError('local Windows source-built runtime changed')
    freeze=package/'development-test-freeze.json';frozen=json.loads(freeze.read_text())
    for name,digest in frozen['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('canonical final contract changed')
    fault_declaration=package/'fault-declaration.json';faults=json.loads(fault_declaration.read_text());variants=[]
    for fault in faults['faults']:
        path=RAW/'cargo-generate/source-fault-development/v1'/(fault['id']+'-compiled.json');row=json.loads(path.read_text())
        if sha256(ROOT/row['binary'])!=row['binary_sha256'] or row['pristine_build_sha256']!=sha256(build_path) or row['compiler_sha256']!=build['compiler_sha256']:raise ValueError('local recorded source variant changed')
        variants.append(dict(fault=fault['id'],compile_receipt=path.relative_to(ROOT).as_posix(),compile_receipt_sha256=sha256(path),
            actual_binary_sha256=row['binary_sha256'],original_compile_attempt=row['compile_attempt']))
    lock=dict(schema_version=1,runtime_kind='native',source_review_sha256=sha256(package/'source-review.json'),
        source_provenance_sha256=sha256(package/'source-provenance.json'),dependency_hook_review_sha256=sha256(package/'dependency-hook-review.json'),
        lock_sha256=json.loads((target/'dependency-fetch-review.json').read_text())['lock_sha256'],
        windows=dict(execution_host=platform.platform(),architecture='amd64',source_build_sha256=sha256(build_path),
            actual_binary_sha256=build['binary_sha256'],compiler_sha256=build['compiler_sha256'],cargo_sha256=build['cargo_sha256'],
            final_calibration='Fresh final-archive baseline/mutated/restored executions using these exact real compiled same-compiler/source variants; no old probe outcome transfer.',variants=variants),
        linux=dict(execution_host='ubuntu-24.04',architecture='amd64',preflight_audit_sha256=sha256(linux),
            native_profile_review_sha256=sha256(package/'native-linux-profile-review-v2.json'),
            build_policy='Fresh exact pinned source and reviewed locked offline ordinary default-feature CLI; actual Rust/Cargo/native C compiler and build hashes recorded per final cell. Recompile the same declared source mutations against that cell baseline toolchain.'),
        source_only_unused_dependencies='Preserve original fetch/review catalogs; runtime/compiler provenance and actual native executables separately audited.',
        cold_scope='Two fresh hash-verified executable-directory copies, each followed by warm reuse. No OS-cache eviction or physical-machine cold-start claim.')
    lock_path=package/'native-runtime-lock-native-exit-v1.json';immutable_json(lock_path,lock)
    batches=copy.deepcopy(json.loads((DOC/'jrnl/final-series-declaration.json').read_text())['batches'])
    for row in batches[:4]:row['runtime']=row['runtime'].replace('venv-pair','app-pair-native-exit-v1')
    immutable_json(package/'final-series-declaration-native-exit-v1.json',dict(schema_version=1,project='cargo-generate',revision=1,
        hosts=['linux','windows'],runtime_kind='native',candidate_series='native-exit-v1',candidate_freeze_sha256=sha256(candidate),
        canonical_test_freeze_sha256=sha256(freeze),native_runtime_lock_sha256=sha256(lock_path),
        fault_declaration_sha256=sha256(fault_declaration),batches=batches,scenarios_per_cell=20,normal=8,edge=12,
        repetitions_per_cell=12,ordinary_required=480,real_source_faults=3,calibration_required=18,
        windows_profile_sha256=sha256(RAW/'cargo-generate/host-contracts/scenarios.json'),
        cold_scope=lock['cold_scope'],transfer_scope='Source, failures, three mutations and platform emoji behavior already exposed. No untouched-source, human beginner or first-attempt claim.',
        failure_policy='No per-case retry. Any failed/partial ordinary batch rejects its affected native series. Preserve it and declare a replacement after diagnosis; do not restart only a failed repetition.',
        execution_budget=dict(windows_native='Available actual local Windows11 amd64, one scenario at a time; exact installed candidate and existing reviewed real source-built target.',
            windows_ordinary_command_ceiling_seconds=1200,windows_calibration_command_ceiling_seconds=600,
            linux_standard_hosted_jobs=1,linux_job_minutes_ceiling=60,estimated_linux_minutes=18,
            linux_acquisition_and_build_ceiling_seconds=1200,maximum_simultaneous_target_hosts=2,
            automatic_harness_minutes_ceiling=15,queue_policy='Inspect at15 queued minutes; one replacement at30 only after termination/completion confirmed. No paid runners or budget changes.'),
        first_linux_preflight='Original19/20 snapshot failure preserved; reviewed exact emoji profile replacement20/0 passed. Neither preflight supplies final repetition or calibration credit.',
        project_admissions=0))
    print('Declared exact480 ordinary native executions and18 new final calibration executions, with concrete local Windows and hosted Linux roles.')


if __name__=='__main__':main()
