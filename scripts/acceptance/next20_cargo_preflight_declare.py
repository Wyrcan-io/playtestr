"""Declare a bounded first native Linux source-build/profile preflight."""
import json

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'cargo-generate';faults=RAW/'cargo-generate/source-fault-development/v1/summary.json'
    if json.loads(faults.read_text())['actual_source_faults']!=3:raise ValueError('finish declared local source faults before native transfer')
    immutable_json(package/'native-linux-preflight-declaration.json',dict(schema_version=1,status='declared-before-native-dispatch',
        source_pin=json.loads((package/'source-review.json').read_text())['pin'],
        canonical_test_freeze_sha256=sha256(package/'development-test-freeze.json'),fault_declaration_sha256=sha256(package/'fault-declaration.json'),
        candidate_freeze_sha256=sha256(DOC/'replacement-candidate-freeze-native-exit-v1.json'),candidate_series='native-exit-v1',
        host='ubuntu-24.04',architecture='linux-amd64',standard_hosted=True,target_jobs=1,maximum_parallel_target_jobs=1,
        job_minutes_ceiling=35,estimated_minutes=12,automatic_harness_job_minutes_ceiling_total=15,
        compiler='Read-only installed stable native Rust; actual rustc/cargo paths, verbose version and hashes recorded. No toolchain download or global installation.',
        dependencies='Same checksum-locked Windows+Linux registry closure; reconstruct actual unpacked files from locked archives and match canonical licenses/all reviewed hook bytes before offline build.',
        build='Normal default-feature locked offline release CLI; two jobs; no LTO/debug/incremental. Compiler command and actual binary preserved.',
        scenarios=20,normal=8,edge=12,ordinary_final_credit=0,calibration_credit=0,project_credit=0,
        profile='Executable relocation, Linux /dev/null Git config and declared cancellation130; all fixture, saved-state and snapshot bytes unchanged. Exact paths/statuses remain to be proven by actual native execution.',
        scope='Development preflight before the complete native series. Preserve its exact compiled binary/provenance and all first outcomes. Hosted source tree is ephemeral and not credited as checked source/runtime deletion. Failed/partial preflight does not qualify a final native cell.',
        publication=False))
    print('Declared Linux-only native preflight:20 cases,35-minute job ceiling, zero final/admission credit')


if __name__=='__main__':main()
