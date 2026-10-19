"""Declare measured native fixture/retention corrections before fresh execution."""
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    run=RAW/'native/39275956482'
    metadata=load(run/'run-metadata.json')
    if metadata['conclusion']!='failure' or len(metadata['jobs'])!=2:
        raise RuntimeError('original two-host outcome differs')
    source=RAW/'active/rclone/src'
    cover=source/'graphics/cover.jpg'
    local=source/'backend/local/local.go'
    alias=source/'backend/alias/alias.go'
    if not 8*1024**2<cover.stat().st_size<=16*1024**2:
        raise RuntimeError('observed source member mismatch')
    failures={}
    for name in ['f0d0d87d4b00430fbd952530301572d2','b1476e1455bb42b897b9400b706bb754']:
        row=load(RAW/'events'/(name+'-finished.json'))
        if row['category']!='harness_timeout' or row['cleanup_errors']:
            raise RuntimeError('local setup timeout cleanup differs')
        failures[name]=row
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone/native-retry-disposition.json',
        dict(original_run='39275956482', original_metadata_sha256=sha256(run/'run-metadata.json'),
             local_build_timeouts=failures,
             local_disposition='No further local build retry planned. Two bounded setup attempts failed; exact same pinned full CLI built natively in 185.1537s Linux and 197.828s Windows. No successful local Rclone runtime claimed.',
             windows_route=dict(failed_capture='f510dccb7d03482d89ac4638ce34ccab',
                 observed='First six controls pass; expected advanced prompt times out; replay/export correctly refuse unresolved failures.',
                 source_sha256=sha256(local),
                 explanation='Source-based inference: local nounc is a basic option only on Windows, so the Linux local-backend prompt sequence is incomplete there.',
                 correction='Use the reviewed alias backend with remote=. for the portable first route; it configures a synthetic local path, has one required remote prompt and no advanced prompt.',
                 alias_source_sha256=sha256(alias),
                 alias_review='Registration declares one required remote option and no Config hook. NewFs is not invoked by configuration; no network service or credentials.',
                 requested_controls_before_retry=20, shell_commands_before_retry=2,
                 corrected_route_controls=20, projected_cumulative_controls=40, projected_cumulative_shell_commands=5,
                 engineering_control_target='Missed cumulatively; the original failed attempt is not erased. Human usability remains unmeasured.'),
             retention=dict(failed_windows_attempt='b0c26c61d672418c85373f86a7ec4a6a',
                 file='graphics/cover.jpg', bytes=cover.stat().st_size, sha256=sha256(cover),
                 correction='Use the already-declared 16 MiB Rclone acquisition member limit for retention too; other projects and 64 MiB expanded-source cap unchanged.'),
             linux_route='Original local-config route reached reviewed ordinary success in three commands/twenty controls, but job cleanup failed; no native cell admission.',
             retry='Fresh two-host run, original artifacts retained, unchanged exact runner archives/Go source. Build receipts copied before public route/cleanup.',
             final_archive_credit=0, development_admission=False))
    print('Original native failures and pre-execution correction/budget disposition retained.')


if __name__ == '__main__':
    main()
