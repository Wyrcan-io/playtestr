"""Apply only the proven config-writer blank-line normalization before freeze."""
import base64
import json

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'hatch';root=RAW/'hatch/config-byte-revision-v2';root.mkdir(parents=True,exist_ok=False)
    observed=RAW/'hatch/config-diagnosis-v1/observed.json';proof=json.loads(observed.read_text())
    original=package/'n08.json';scenarios=package/'scenarios.json';spec=json.loads(original.read_text());declaration=json.loads(scenarios.read_text())
    state=spec['steps'][7]['state'];expected=base64.b64decode(state['bytes_base64']);actual=bytes.fromhex(proof['actual_hex'])
    if (not proof['complete_semantics_equal'] or not proof['original_unchanged'] or expected.hex()!=proof['expected_hex'] or
        expected.count(b'\r\n[terminal.styles]')!=1 or expected.replace(b'\r\n[terminal.styles]',b'\r\n\r\n[terminal.styles]')!=actual):
        raise ValueError('refuse anything beyond independently diagnosed one-blank-line normalization')
    (root/'n08-before.json').write_bytes(original.read_bytes());(root/'scenarios-before.json').write_bytes(scenarios.read_bytes())
    before=sha256(original);before_declaration=sha256(scenarios)
    state['bytes_base64']=base64.b64encode(actual).decode()
    original.write_text(json.dumps(spec,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    next(r for r in declaration['cases'] if r['id']=='N08')['spec_sha256']=sha256(original)
    declaration['development_revision']=2;declaration['reviewed_revision']='config-writer-byte-revision-v2.json'
    scenarios.write_text(json.dumps(declaration,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'config-writer-byte-revision-v2.json',dict(schema_version=1,case='N08',diagnostic_sha256=sha256(observed),
        original_spec_sha256=before,current_spec_sha256=sha256(original),original_declaration_sha256=before_declaration,
        current_declaration_sha256=sha256(scenarios),actual_complete_config=proof['actual_complete_config'],
        original_complete_config=proof['expected_complete_config'],semantics_unchanged=True,
        change='One CRLF blank line before [terminal.styles], produced when tomlkit serializes the nested template tables followed by terminal styles. All intended values, actions, other assertions, saved author name and exact exit are unchanged.',
        original_failed_report='artifacts/runner-readiness-next-twenty-project-pass/hatch/development/063806a0a4454213afa82ec56e53424c/N08.report.json',
        review_source_sha256=sha256(RAW/'active/hatch/src/src/hatch/config/utils.py'),
        product_source_changed=False,source_faults_selected=0,final_ordinary_credit=0))
    print('Revised only one independently diagnosed N08 formatting byte sequence; original failure and declaration retained.')


if __name__=='__main__':main()
