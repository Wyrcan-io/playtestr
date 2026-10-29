"""Declare the finite two-cell final protocol after actual positive development."""
import json
from next20_check import DOC, RAW
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'pdm';contracts=RAW/'pdm/host-contracts'
    matches=[p for p in (RAW/'pdm/development').glob('*/summary.json')
        if (v:=json.loads(p.read_text()))['declaration_sha256']==sha256(contracts/'scenarios.json') and v['passed']==20 and v['failed']==0]
    if len(matches)!=1:raise ValueError('one positive current Windows profile series required')
    linux=json.loads((package/'linux-second-development-readback.json').read_text())
    if linux['passed']!=20 or linux['failed']:raise ValueError('positive independent Linux readback required')
    inherited=json.loads((DOC/'jrnl/final-series-declaration.json').read_text())
    immutable_json(package/'final-series-declaration-native-exit-v1.json',dict(schema_version=1,project='pdm',revision=1,
        hosts=['windows','linux'],candidate='v0.4.0-rc.6',candidate_series='native-exit-v1',
        candidate_freeze_sha256=sha256(DOC/'replacement-candidate-freeze-native-exit-v1.json'),
        canonical_test_freeze_sha256=sha256(package/'development-test-freeze.json'),
        native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),
        windows_profile_sha256=sha256(package/'windows-profile-v1.json'),linux_profile_sha256=sha256(package/'native-profile-v2.json'),
        positive_windows_development_sha256=sha256(matches[0]),positive_linux_readback_sha256=sha256(package/'linux-second-development-readback.json'),
        fault_declaration_sha256=sha256(package/'fault-declaration.json'),batches=inherited['batches'],
        scenarios_per_cell=20,normal=8,edge=12,repetitions_per_cell=12,ordinary_required=480,
        real_source_faults=3,required_three_phase_calibrations=18,calibration_required=18,
        historical_evidence_retention_complete=False,historical_screen_gap_disposition_sha256=sha256(package/'development-evidence-retention-disposition.json'),
        excluded_target_behavior='Explicit recursive README overwrite failed upstream; revised supported N08 preserves the existing README without overwrite. No overwrite pass claim.',
        transfer_scope='Source, original failures and all mutations already exposed; no untouched/human claim. Original reports are not reruns.',
        cold_scope='Two newly copied, hash-verified owned Python runtimes, each followed by warm reuse; no OS-cache or physical-machine cold-start claim.',
        failure_policy=inherited['failure_policy'],project_admissions=0,
        scope='Collect exact final-cell evidence independently of the unresolved historical-screen retention gate. This declaration neither admits PDM nor waives a missing original frame.',
        storage_forecast=dict(current_retained_approx_bytes=32000000,additional_linux_packet_ceiling_bytes=16000000,
            local_retention_forecast_bytes=16000000,project_cap_bytes=67108864,
            policy='Measure before cleanup retention; compact shared exact payloads before any cap breach, never delete required first-failure evidence.'),
        execution_budget=dict(linux_standard_hosted_jobs=1,linux_job_ceiling_minutes=40,estimated_linux_minutes=6,
            windows_local_command_ceiling_seconds=1200,estimated_windows_minutes=12,
            automatic_harness_jobs=3,harness_job_ceiling_minutes=5,harness_max_parallel=2,maximum_target_hosts=2)))
    print('Declared480 required ordinary and18 fresh calibrations across2cells; actual final credit remains0; historical gap open.')


if __name__=='__main__':main()
