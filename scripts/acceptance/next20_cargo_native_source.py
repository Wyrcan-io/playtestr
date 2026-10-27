"""Verify the fresh native acquisition against all pinned canonical source bytes."""
import json

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def main():
    target=RAW/'active/cargo-generate';package=DOC/'cargo-generate'
    if (target/'build.json').exists() or (target/'runtime.json').exists():raise ValueError('fresh source readback must precede every build and target execution')
    expected=json.loads((package/'source-provenance.json').read_text())
    owner=json.loads((target/'task-owned.json').read_text())
    actual={p.relative_to(target/'src').as_posix():sha256(p) for p in (target/'src').rglob('*') if p.is_file()}
    if actual!=expected['files'] or owner['pin']!=expected['pin']:raise ValueError('native source differs from the exact canonical upstream pin')
    review=package/'source-review.json';reviewed=json.loads(review.read_text())
    if any(actual.get(n)!=h for n,h in reviewed['reviewed_inputs'].items()):raise ValueError('native reviewed source inputs differ')
    immutable_json(target/'native-source-readback.json',dict(schema_version=1,pin=owner['pin'],files=len(actual),
        canonical_provenance_sha256=sha256(package/'source-provenance.json'),canonical_review_sha256=sha256(review),
        scope='Fresh archive acquired without hooks; every extracted source file matches the primary-Git-bound canonical content. No build or target execution yet.'))
    print('Fresh native source matches every pinned upstream file:',len(actual))


if __name__=='__main__':main()
