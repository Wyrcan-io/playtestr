"""Read-only re-audit of retained original matrix; write only the new campaign."""
import hashlib
import json
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256
from readiness_final_matrix_audit import build_model, validate


def main():
    old = ROOT/'docs/validation/runner-readiness-ten-project-pass'
    freeze = json.loads((old/'migration-candidate-freeze.json').read_text())
    original = json.loads((old/'final-matrix-audit.json').read_text())
    model = build_model()
    counts = validate(model, freeze)
    data=(json.dumps(model,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
    digest=hashlib.sha256(data).hexdigest()
    if digest != original['actual_model_sha256']:
        raise ValueError('retained matrix differs from original audited actual model')
    narrative = json.loads((old/'closing-document-audit-v2.json').read_text())
    # This receipt names its own historical revision rather than demanding
    # current planning prose match a pre-campaign document forever.
    historical_revision='46d01dfb3671fd18b73f15261069daa994e9afb8'
    documents=[]
    for name,expected in narrative['files'].items():
        blob=subprocess.check_output(['git','show',historical_revision+':'+name])
        encodings={'git-blob':blob,'windows-checkout-crlf':blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')}
        matched=[mode for mode,data in encodings.items() if hashlib.sha256(data).hexdigest()==expected]
        if not matched:
            raise ValueError('historical narrative blob mismatch: '+name)
        documents.append(dict(path=name,historical_sha256=expected,
                              historical_rendering=matched[0],
                              current_sha256=sha256(ROOT/name)))
    destination=RAW/'baseline'/('carry-forward-'+uuid.uuid4().hex+'.json')
    immutable_json(destination,dict(schema_version=1,status='qualified-unchanged-rc.5',
        actual_model_sha256=digest,original_audit_sha256=sha256(old/'final-matrix-audit.json'),
        candidate_freeze_sha256=sha256(old/'migration-candidate-freeze.json'),
        historical_narrative_revision=historical_revision,documents=documents,
        **counts,new_project_credit=0,condition='Invalidated by changed production/build/archive inputs.'))
    print(json.dumps(dict(receipt=destination.relative_to(ROOT).as_posix(),**counts),indent=2))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
