"""Verify first-batch subjects and exact archives without expanding old evidence."""
import json
import platform
import shutil
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
from next20_check import DOC, RAW, ROOT, NAME
from readiness_evidence import immutable_json, sha256
from readiness_storage import measure


def main():
    baseline_doc = ROOT/'docs/validation/runner-readiness-ten-project-pass'
    baseline_raw = ROOT/'artifacts/runner-readiness-ten-project-pass'
    closing = baseline_doc/'campaign-admission.json'
    admission = json.loads(closing.read_text(encoding='utf-8'))
    subjects = []
    for relative, expected in admission['subjects'].items():
        path = (baseline_doc/relative).resolve(strict=True)
        path.relative_to(ROOT)
        actual = sha256(path)
        if actual != expected:
            raise ValueError('baseline subject mismatch: '+relative)
        subjects.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=actual))
    mirror = baseline_raw/'campaign-admission-verified.json'
    if closing.read_bytes() != mirror.read_bytes():
        raise ValueError('closing admission mirror mismatch')
    freeze = json.loads((baseline_doc/'migration-candidate-freeze.json').read_text())
    archives = []
    for row in freeze['cells']:
        path = (ROOT/row['archive_local_only']).resolve(strict=True)
        path.relative_to(baseline_raw.resolve())
        if sha256(path) != row['archive_sha256']:
            raise ValueError('candidate archive mismatch')
        archives.append(dict(path=path.relative_to(ROOT).as_posix(),
                             sha256=row['archive_sha256'], host=row['host'],
                             binary_sha256=row['binary_sha256']))
    diff = subprocess.check_output(['git', 'diff', freeze['source_revision'], '--',
                                    'internal', 'cmd', 'go.mod', 'go.sum'])
    if diff:
        raise ValueError('production/build source changed; inspect before carry-forward')
    branch = subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    if branch != 'work/p0-p2-implementation':
        raise ValueError('unexpected branch')
    record = dict(schema_version=1,campaign=NAME,client_date='2026-10-22',
        head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        branch=branch,status=subprocess.check_output(['git','status','--short'],text=True),
        admission_sha256=sha256(closing),subjects=subjects,archives=archives,
        production_source_unchanged=True,production_source=freeze['source_revision'],
        historical_admissions=admission['final_runner_admissions'],
        current_candidate_carry_forward='pending retained payload audit',
        old_storage=measure(baseline_raw),new_storage=measure(RAW),
        tools={name:shutil.which(name) for name in ['python','git','gh','go','node','cargo','ruby']},
        native_host=dict(system=platform.system(),machine=platform.machine()),
        new_project_admissions=0,human_participants=0,paid_admissions=0)
    destination = RAW/'baseline'/(uuid.uuid4().hex+'.json')
    immutable_json(destination,record)
    print(json.dumps(dict(receipt=destination.relative_to(ROOT).as_posix(),
        subjects_verified=len(subjects),archives_verified=len(archives),
        historical_admissions=10,current_carry_forward='payload audit pending',
        old_bytes=record['old_storage']['total_bytes']),indent=2))


if __name__ == '__main__':
    main()
