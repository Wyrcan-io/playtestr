"""Declare a finite two-host Hatch final window after actual positive development."""
import json

from next20_check import DOC,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'hatch';contracts=RAW/'hatch/host-contracts'
    windows=[p for p in (RAW/'hatch/development').glob('*/summary.json')
        if (v:=json.loads(p.read_text()))['passed']==20 and v['failed']==0 and v['declaration_sha256']==sha256(contracts/'scenarios.json')]
    if len(windows)!=1:raise ValueError('one positive exact Windows host-profile series required')
    linux=package/'linux-development-readback.json';actual=json.loads(linux.read_text())
    if len(actual['observations'])!=20 or not actual['source_runtime_removed'] or actual['actual_dependency_wheels']!=48:raise ValueError('complete independent Linux development readback required')
    journeys=list((RAW/'hatch').glob('maintenance-*/journey.json'))
    if len(journeys)!=1 or not json.loads(journeys[0].read_text())['source_restored']:raise ValueError('completed restored public maintenance journey required')
    inherited=json.loads((DOC/'jrnl/final-series-declaration.json').read_text())
    immutable_json(package/'final-series-declaration-native-exit-v1.json',dict(schema_version=1,project='hatch',revision=1,
        hosts=['windows','linux'],candidate='v0.4.0-rc.6',candidate_series='native-exit-v1',
        candidate_freeze_sha256=sha256(DOC/'replacement-candidate-freeze-native-exit-v1.json'),
        canonical_test_freeze_sha256=sha256(package/'development-test-freeze.json'),native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),
        windows_profile_sha256=sha256(package/'windows-profile-v1.json'),positive_windows_development_sha256=sha256(windows[0]),
        positive_linux_readback_sha256=sha256(linux),fault_declaration_sha256=sha256(package/'fault-declaration.json'),
        maintenance_journey=journeys[0].relative_to(ROOT).as_posix(),maintenance_journey_sha256=sha256(journeys[0]),
        batches=inherited['batches'],scenarios_per_cell=20,normal=8,edge=12,repetitions_per_cell=12,ordinary_required=480,
        real_source_faults=3,required_three_phase_calibrations=18,calibration_required=18,startup_timeout_ms_by_host={'windows':2000,'linux':2000},
        original_failures='Initial sparse-init independent state review failed; separate supported existing-table route passed. Additional generation first omitted new subcommand interactive flag, corrected separately. First Windows20-case development19/1 exact config formatting; one proven blank line corrected before fresh20/0/freeze. All original inputs/consoles/reports/frames and source revisions retained; closing all-attempt audit still required.',
        authoring='Original cumulative5 shell invocations/28 controls misses20-control target; repaired3/14 engineering route remains separate. Additional library route2/20 and public maintenance passed. No beginner/human timing claim.',
        excluded_behavior='Sparse missing project/version tables unsupported at this pinned source/runtime; empty-license CLI/flat template early return not qualified. Declared generation uses exact reviewed Apache cache with headers false, no year substitution or runtime network.',
        transfer_scope='All source, failures and mutations already exposed; no untouched target/native/human claim.',
        cold_scope='Two fresh hash-verified owned runtime copies followed by paired reuse; no OS-cache eviction, machine cold-start or isolated/full-SDK retention claim.',
        failure_policy=inherited['failure_policy'],project_admissions=0,
        execution_budget=dict(linux_standard_hosted_jobs=1,linux_job_ceiling_minutes=45,linux_final_command_ceiling_seconds=1200,
            windows_local_command_ceiling_seconds=1200,estimated_linux_target_minutes=10,estimated_windows_minutes=18,
            automatic_harness_push_jobs=3,harness_job_ceiling_minutes=5,harness_max_parallel=2),
        retention=dict(mandatory_native_development_generation=1,native_development_archive_sha256=sha256(RAW/'hatch/retained-native-v1/packets.tar.gz'),
            project_cap_bytes=64*1024**2,final_linux_policy='Direct bounded provider ZIP to exact-reference packet using mandatory standalone native1; never expand final beside retained dependencies.',
            windows_policy='Retain unique Windows payloads and primary metadata; byte-identical shared wheel/source payloads require explicit verified canonical-native references before local cleanup.'),
        scope='Finite exact final execution declaration only. Actual complete per-cell reports/source/runtime/evidence readback, false-green controls, storage and confirmed cleanup remain required before admission.'))
    print('Declared two fresh240+9 final cells,12 finite batches each,strict2s boundary and no per-case retries; zero admission credit.')


if __name__=='__main__':main()
