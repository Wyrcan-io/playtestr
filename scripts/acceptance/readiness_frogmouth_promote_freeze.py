"""Preserve the insufficient first freeze before promoting reviewed revision two."""
import shutil

from readiness_evidence import ROOT,immutable_json,sha256
from readiness_new_control_matrix import read_json as load
from readiness_frogmouth_verify_first_use import require


def check(profile):
    freeze=load(profile/'reviewed-contract-freeze.json')
    require(len(freeze['contracts'])==20,'incomplete twenty-case freeze')
    actual={p.relative_to(profile/'contracts').as_posix():sha256(p) for p in (profile/'contracts').rglob('*') if p.is_file()}
    require(actual==freeze['all_package_inputs'],'freeze payload coverage or bytes changed')
    return freeze


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/frogmouth'
    revised=docs/'freezes/revision-2';review=load(revised/'native-authoring-review.json')
    require(review['run']=='39102351210','wrong strengthened native review')
    for profile in [docs,docs/'native-profiles/windows',revised,revised/'native-profiles/windows']:check(profile)
    history=docs/'freezes/revision-1';history.mkdir(exist_ok=False)
    for name in ['contracts','native-profiles']:shutil.copytree(docs/name,history/name)
    for name in ['reviewed-contract-freeze.json','native-authoring-review.json','fault-selection.json','source-fault-review.json']:
        shutil.copyfile(docs/name,history/name)
    check(history);check(history/'native-profiles/windows')
    for name in ['contracts','native-profiles']:shutil.copytree(revised/name,docs/name,dirs_exist_ok=True)
    for name in ['reviewed-contract-freeze.json','native-authoring-review.json']:shutil.copyfile(revised/name,docs/name)
    check(docs);check(docs/'native-profiles/windows')
    immutable_json(docs/'current-freeze.json',dict(revision=2,native_run='39102351210',independent_review='4ba70e99103f4a228f8941a5579a2cc6',
        previous_freeze_sha256=sha256(history/'reviewed-contract-freeze.json'),current_freeze_sha256=sha256(docs/'reviewed-contract-freeze.json'),
        historical_copy='freezes/revision-1',reviewed_copy='freezes/revision-2',reason='Replace help/About-only cases with bookmark revisit and history-clear cancellation/confirmation. Preserve old contracts/results; no Frogmouth admission yet.',
        original_heldout='No qualifying fresh source fault selected before this revised freeze. Prior F03 selected but never executed and gets zero revised-freeze heldout credit.'))
    print('Preserved original native freeze; promoted independently verified meaningful twenty-case revision two.')


if __name__=='__main__':main()
