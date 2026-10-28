"""Freeze the complete Linux third window after actual editing-byte diagnosis."""
import hashlib
import json
from next20_check import DOC
from next20_cargo_readiness_review import add_edit_readiness
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'cargo-generate';trace_path=package/'native-linux-backspace-trace-v1.json';trace=json.loads(trace_path.read_text())
    if trace['run']!='40753955125' or trace['diagnostic_observations']!=2:raise ValueError('actual Backspace diagnostic proof required')
    prior=package/'native-linux-readiness-profile-v3.json';review=json.loads(prior.read_text());locale=json.loads((package/'native-linux-profile-review-v2.json').read_text())['native_environment']
    canonical=package/'e02.json';native=add_edit_readiness(json.loads(canonical.read_text()))
    native['command'][0]='../../active/cargo-generate/bin/cargo-generate';native['env'].update(GIT_CONFIG_GLOBAL='/dev/null',**locale)
    digest=hashlib.sha256((json.dumps(native,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()).hexdigest()
    review_path=package/'native-linux-readiness-profile-v4.json'
    immutable_json(review_path,dict(review,revision=4,cases=['N01','E02'],prior_readiness_review_sha256=sha256(prior),backspace_trace_sha256=sha256(trace_path),
        edit_case=dict(case='E02',canonical_spec_sha256=sha256(canonical),actual_native_spec_sha256=digest,added_checks=5),
        chunk_readiness=True,
        scope='N01 retains prior2 checks and identical snapshot. E02 adds5 checks around typing/editing/submitting, preserving Backspace, original resize, every original action and all reviewed saved bytes. Segmented variant adds partial-input consumption expects derived from explicit full-input expects. No sleeps, input-mode overrides, core/source changes or assertion removal.'))
    base_path=package/'final-series-declaration-native-exit-v1.json';base=json.loads(base_path.read_text())
    immutable_json(package/'final-linux-replacement-declaration-native-exit-v1-v3.json',dict(schema_version=1,host='linux',window=3,
        base_final_declaration_sha256=sha256(base_path),native_readiness_review_sha256=sha256(review_path),
        previous_rejected_runs=['40477083665','40746186639'],last_rejection_sha256=sha256(package/'native-linux-second-final-rejection.json'),
        diagnostic_run='40753955125',diagnostic_sha256=sha256(trace_path),candidate_freeze_sha256=base['candidate_freeze_sha256'],
        canonical_test_freeze_sha256=base['canonical_test_freeze_sha256'],fault_declaration_sha256=base['fault_declaration_sha256'],
        actual_native_N01_sha256=review['actual_native_N01_sha256'],expected_native_contracts={'normal-project.json':review['actual_native_N01_sha256'],'e02.json':digest},
        chunk_readiness=True,ordinary_required=240,calibration_required=9,repetitions=12,per_case_retries=0,
        execution_budget=dict(original_linux_minutes_ceiling=60,prior_native_actual_seconds=598,conservative_prior_minutes=13,
            replacement_job_minutes_ceiling=43,combined_conservative_minutes=56,estimated_replacement_minutes=14,maximum_target_jobs=1,automatic_push_harness_minutes_ceiling=15),
        scope='Fresh complete Linux12-batch window and all9 calibrations. No49/1 or20/1 partial transfer. All original oracles/cases retained; Windows240/9 exact unchanged archive/contracts/runtime stays separate pending complete admission.'))
    print('Declared Linux window3/profile4: original actions/oracles intact; fresh240/9, positive editing/segmented-input consumption checkpoints')


if __name__=='__main__':main()
