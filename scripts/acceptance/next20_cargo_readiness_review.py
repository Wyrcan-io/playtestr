"""Declare additive native input checkpoints after preserved syscall diagnosis."""
import copy
import hashlib
import json

from next20_check import DOC
from readiness_evidence import immutable_json,sha256


INSERTIONS={'synthetic-notes':'Project Name: synthetic-notes','Ada':'Project owner: Ada'}


def add_readiness(value):
    result=copy.deepcopy(value);steps=[];seen=[]
    for number,step in enumerate(value['steps']):
        steps.append(copy.deepcopy(step))
        if set(step)=={'text'} and step['text'] in INSERTIONS:
            if number+1>=len(value['steps']) or value['steps'][number+1]!={'key':'Enter'}:raise ValueError('readiness insertion no longer precedes Enter')
            seen.append(step['text']);steps.append(dict(expect=INSERTIONS[step['text']]))
    if seen!=list(INSERTIONS):raise ValueError('canonical N01 readiness anchors changed or duplicated')
    result['steps']=steps;return result


def add_edit_readiness(value):
    result=copy.deepcopy(value);steps=[];seen=[]
    for number,step in enumerate(value['steps']):
        steps.append(copy.deepcopy(step))
        if step==dict(text='synthetic-notes'):
            if value['steps'][number+1]!=dict(key='Enter'):raise ValueError('E02 name Enter anchor changed')
            steps.append(dict(expect='Project Name: synthetic-notes'));seen.append('name')
        elif step==dict(text='Adx'):
            if value['steps'][number+1]!=dict(key='Backspace'):raise ValueError('E02 edit anchor changed')
            steps.append(dict(expect='Project owner: Adx'));seen.append('typed')
        elif step==dict(key='Backspace'):
            if number==0 or value['steps'][number-1]!=dict(text='Adx') or value['steps'][number+1]!=dict(text='a'):raise ValueError('E02 Backspace transition changed')
            steps.extend([dict(expect_not='Project owner: Adx'),dict(expect='Project owner: Ad')]);seen.append('erased')
        elif step==dict(text='a'):
            if value['steps'][number+1]!=dict(key='Enter'):raise ValueError('E02 corrected-value Enter changed')
            steps.append(dict(expect='Project owner: Ada'));seen.append('corrected')
    if seen!=['name','typed','erased','corrected']:raise ValueError('E02 input readiness anchors missing or duplicated')
    result['steps']=steps;return result


def main():
    package=DOC/'cargo-generate';trace_path=package/'native-linux-input-echo-trace-v1.json';trace=json.loads(trace_path.read_text())
    if trace['run']!='40744103927' or len(trace['causal_sequence'])!=6:raise ValueError('actual diagnosed trace proof required')
    base_profile=package/'native-linux-profile-review-v2.json';old=json.loads(base_profile.read_text())
    canonical_path=package/'normal-project.json';value=json.loads(canonical_path.read_text())
    native=add_readiness(value);native['command'][0]='../../active/cargo-generate/bin/cargo-generate'
    native['env'].update(GIT_CONFIG_GLOBAL='/dev/null',**old['native_environment'])
    native_hash=hashlib.sha256((json.dumps(native,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()).hexdigest()
    review_path=package/'native-linux-readiness-profile-v3.json'
    immutable_json(review_path,dict(schema_version=1,revision=3,host='linux',case='N01',canonical_spec_sha256=sha256(canonical_path),
        base_native_profile_review_sha256=sha256(base_profile),input_echo_trace_sha256=sha256(trace_path),
        actual_native_N01_sha256=native_hash,insertions=INSERTIONS,native_snapshot_sha256=old['native_snapshot_sha256'],
        scope='Two additive rendered full-input expects, each immediately before its existing Enter. Same key/text values, exact six selected snapshot rows/bytes, fixtures, saved-state assertions and budgets. No sleeps, input-mode overrides, target/source/product changes, filtering or assertion removal. Original canonical/Windows contract unchanged.',
        evidence_boundary='Upstream per-key termios restoration and actual echoed CRLF proven in retained trace; checkpoints address observed input consumption. No claim of zero timing failures or fresh holdout exposure.'))
    declaration=package/'final-series-declaration-native-exit-v1.json';base=json.loads(declaration.read_text())
    immutable_json(package/'final-linux-replacement-declaration-native-exit-v1-v2.json',dict(schema_version=1,host='linux',window=2,
        base_final_declaration_sha256=sha256(declaration),native_readiness_review_sha256=sha256(review_path),
        original_rejected_run='40477083665',original_rejection_sha256=sha256(package/'native-linux-first-final-rejection.json'),
        diagnostic_run='40744103927',diagnostic_sha256=sha256(trace_path),candidate_freeze_sha256=base['candidate_freeze_sha256'],
        canonical_test_freeze_sha256=base['canonical_test_freeze_sha256'],fault_declaration_sha256=base['fault_declaration_sha256'],
        actual_native_N01_sha256=native_hash,ordinary_required=240,calibration_required=9,repetitions=12,per_case_retries=0,
        execution_budget=dict(original_linux_minutes_ceiling=60,first_final_actual_seconds=277,raw_diagnostic_actual_seconds=15,
            candidate_trace_actual_seconds=14,conservative_prior_minutes=7,replacement_job_minutes_ceiling=49,
            combined_conservative_ceiling_minutes=56,estimated_replacement_minutes=14,maximum_target_jobs=1,automatic_push_harness_minutes_ceiling=15),
        scope='Complete fresh Linux12-batch window plus all9 fresh final calibrations. Rejected20/1 window and diagnostics transfer no repetition credit. Windows original240/9 remains exact unchanged candidate/contracts/runtime evidence, pending full admission.'))
    print('Declared Linux window2/profile3: exact unchanged snapshot, two positive full-input checkpoints; all240/9 must freshly execute')


if __name__=='__main__':main()
