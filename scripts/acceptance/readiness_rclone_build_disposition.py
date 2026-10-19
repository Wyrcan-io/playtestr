"""Preserve the first cold-build failure before a bounded cached resume."""
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    attempt = 'b1476e1455bb42b897b9400b706bb754'
    failure = load(RAW/'events'/(attempt+'-finished.json'))
    if failure['category'] != 'harness_timeout' or failure['cleanup_errors']:
        raise RuntimeError('first cold-build disposition differs from actual outcome')
    target = RAW/'active/rclone'
    diagnostic = load(target/'small-dependency-diagnostic.json')
    storage = load(target/'build-storage-d3df118c90874c9784f2f361a4d9587b.json')
    dependency = target/'gopath/pkg/mod/github.com/unknwon/goconfig@v1.0.0'
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone/first-build-disposition.json',
        dict(first_failed_attempt=attempt, outer_failed_attempt='8faac0a2987048b2bffd1b11e001f5c5',
             outcome=failure, observed_max_active_bytes=max(storage['observed_active_bytes']),
             diagnostic=diagnostic,
             cause='Undetermined cold dependency setup timeout; no compiler errors were emitted before the limit.',
             resume='One bounded cached resume, same 780-second command deadline and unchanged original source/locks/SDK/build flags.',
             counters='Not a completed target build, first-use attempt or passing qualification.',
             dependency_review=dict(module='github.com/unknwon/goconfig', version='v1.0.0',
                 locked_sum=diagnostic['checksum'],
                 files={name:sha256(dependency/name) for name in ['conf.go','write.go','LICENSE']},
                 findings='SaveConfigData uses spaced equals and a blank line between sections; LineBreak is CRLF on Windows and LF elsewhere. No Rclone override found.',
                 first_use_change='Declare native exact expected bytes before any public Rclone recording; no existing expectation updated.')))
    print('First cold-build failure and pre-capture native newline disposition retained.')


if __name__ == '__main__':
    main()
