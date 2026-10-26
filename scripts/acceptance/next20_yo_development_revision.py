"""Preserve all first yo inputs and correct two observed diagnostic anchors."""
import json
import shutil

from next20_check import DOC, RAW
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'yo'
    declaration=json.loads((package/'scenarios.json').read_text())
    if declaration['development_revision']!=1:raise ValueError('First revision already preserved')
    series=[]
    for path in (RAW/'yo/development').glob('*/summary.json'):
        data=json.loads(path.read_text())
        if data['declaration_sha256']==sha256(package/'scenarios.json'):
            series.append((path,data))
    if len(series)!=1 or series[0][1]['passed']!=18 or series[0][1]['failed']!=2:
        raise ValueError('Require exact complete first18/2 outcome')
    retained=RAW/'yo/development-inputs-v1'
    retained.mkdir()
    inputs={}
    for path in package.rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(package)
        if path.suffix not in ('.json','.txt','.js','.md'):continue
        dest=retained/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,dest)
        if sha256(dest)!=sha256(path):raise ValueError('First inputs changed during preservation')
        inputs[rel.as_posix()]=sha256(dest)
    immutable_json(retained/'preserved.json',dict(schema_version=1,files=inputs,
        first_series=series[0][0].relative_to(RAW).as_posix(),
        original_declaration_sha256=sha256(package/'scenarios.json')))
    replacements={'E11':('ENOTDIR','is not a directory'),
                  'E12':('Unexpected','Could not parse JSON in file:')}
    for case in declaration['cases']:
        if case['id'] not in replacements:continue
        path=package/case['spec'];spec=json.loads(path.read_text())
        before,after=replacements[case['id']]
        steps=[step for step in spec['steps'] if step.get('expect')==before]
        if len(steps)!=1:raise ValueError('Unexpected original diagnostic contract')
        steps[0]['expect']=after
        path.write_text(json.dumps(spec,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        case['spec_sha256']=sha256(path)
    declaration['development_revision']=2
    (package/'scenarios.json').write_text(json.dumps(declaration,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'development-revision.json',dict(schema_version=1,revision=2,
        first_declaration_sha256=inputs['scenarios.json'],preserved_inputs_sha256=sha256(retained/'preserved.json'),
        changes=replacements,reason='Actual native diagnostics use mem-fs wording and current Node JSON parser wording; exact expected exits and saved-state predicates unchanged.',
        source_changed=False,public_exports_changed=False,final_ordinary_credit=0))
    print('Preserved complete first18/2 series and every original spec/fixture/screen; revised two observed diagnostic anchors only.')


if __name__=='__main__':main()
