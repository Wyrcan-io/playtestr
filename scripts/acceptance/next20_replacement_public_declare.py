"""Declare unchanged public archive controls on the new exact three-host freeze."""
import json
import hashlib

from next20_check import ROOT,DOC
from readiness_archive_controls import cases,definition_sha256
from readiness_evidence import immutable_json,sha256


def main():
    freeze=DOC/'replacement-candidate-freeze-native-exit-v1.json';value=json.loads(freeze.read_text())
    original=ROOT/'docs/validation/runner-readiness-ten-project-pass/archive-control-declaration.json'
    declaration=json.loads(original.read_text())
    if [(c['id'],definition_sha256(c)) for c in cases()]!=[(c['id'],c['definition_sha256']) for c in declaration['cases']]:raise ValueError('inherited definitions changed')
    if len(value['cells'])!=3 or {r['host'] for r in value['cells']}!={'darwin','linux','windows'}:raise ValueError('incomplete replacement freeze')
    for row in value['cells']:
        if sha256(ROOT/row['archive_local_only'])!=row['archive_sha256']:raise ValueError('frozen archive changed')
    if hashlib.sha256((ROOT/'cmd/fixture/main.go').read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=declaration['fixture_source_lf_sha256']:raise ValueError('synthetic fixture source changed')
    immutable_json(DOC/'replacement-public-controls-declaration.json',dict(schema_version=1,status='declared-before-dispatch',
        candidate_series='native-exit-v1',candidate_freeze_sha256=sha256(freeze),original_definitions_sha256=sha256(original),
        controls_per_host=35,total_reexecutions=105,hosts=['ubuntu-24.04','macos-15','windows-2025'],
        standard_hosted=True,maximum_parallel_jobs=2,job_minutes_ceiling_per_host=20,total_job_minutes_ceiling=60,
        estimate_minutes={'linux':2,'darwin':2,'windows':4},automatic_harness_minutes_ceiling=15,
        dispatch_policy='Wait for the source-matched automatic harness to complete; then dispatch explicit candidate_series=native-exit-v1. No rebuilding Playtestr, publication or paid runners. Retain/audit one host packet at a time.',
        unchanged_control_ids=[c['id'] for c in cases()]+declaration['recorder_controls'],
        synthetic_target='Exact inherited cmd/fixture source, freshly compiled with identified native Go. No external application or whole-control breadth credit.',
        project_credits=0,new_whole_control_credit=0,publication=False))
    print('Declared105 exact replacement-archive public reexecutions with unchanged control definitions.')


if __name__=='__main__':main()
