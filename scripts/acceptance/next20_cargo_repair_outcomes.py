"""Preserve measured first outcomes before correcting native exit/template expectations."""
import base64
import json
import shutil

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'cargo-generate';retained=RAW/'cargo-generate/development-inputs-v2'
    if retained.exists():raise ValueError('preserve original development inputs')
    original={}
    for p in package.rglob('*'):
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise ValueError('linked input')
        if p.is_file():original[p.relative_to(package).as_posix()]=sha256(p)
    if len(original)>4000 or sum(p.stat().st_size for p in package.rglob('*') if p.is_file())>16*1024**2:
        raise ValueError('case retention bound')
    shutil.copytree(package,retained)
    for name,digest in original.items():
        if sha256(retained/name)!=digest:raise ValueError('original input retention differs')
    declaration=package/'scenarios.json';value=json.loads(declaration.read_text());changes=[]
    for case in value['cases']:
        if case['id'] not in {'E03','E04','E12'}:continue
        path=package/case['spec'];data=json.loads(path.read_text());before=sha256(path)
        if case['id'] in {'E03','E04'}:
            exits=[s for s in data['steps'] if 'exit' in s]
            if len(exits)!=1 or exits[0]['exit']!=1:raise ValueError('original cancellation expectation changed')
            exits[0]['exit']=3221225786;case['expected_exit']=3221225786
            case['native_exit_profile']={'windows':3221225786,'linux':130}
        else:
            fixture=package/case['initial_fixture']/'template/profile.txt.liquid'
            if fixture.read_bytes()!=b'{{ undefined_required_variable }}\n':raise ValueError('original Liquid input changed')
            payload=b'{% if %}\n';fixture.write_bytes(payload)
            for step in data['steps']:
                if step.get('state',{}).get('path')=='template/profile.txt.liquid':
                    step['state']['bytes_base64']=base64.b64encode(payload).decode()
            data['name']='Refuse malformed Liquid syntax after real prompt completion';case['task']=data['name']
        path.write_text(json.dumps(data,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        case['spec_sha256']=sha256(path);changes.append(dict(case=case['id'],before=before,after=sha256(path)))
    declaration.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'development-outcome-disposition.json',dict(schema_version=1,
        retained_initial_package=retained.relative_to(RAW).as_posix(),retained_files=original,changes=changes,
        first_complete_summary='cargo-generate/development/6579be4e7db242b3b9ff20d72f2bdcd8/summary.json',
        first_complete_summary_sha256=sha256(RAW/'cargo-generate/development/6579be4e7db242b3b9ff20d72f2bdcd8/summary.json'),
        first_complete_passed=17,first_complete_failed=3,
        disposition='Windows default Ctrl-C exits with native status 0xC000013A (3221225786), rather than 1; Linux profile will require its exact actual 130. Undefined Liquid variables expand empty rather than failing: the original mistaken error expectation stays retained, and E12 now supplies genuinely malformed syntax. Runner correctly rejected both mismatched exits and the nonexistent error expectation. No product/target-source change or false-green claim.'))
    print('Retained complete 17/3 inputs and screens; corrected native Ctrl-C status and malformed-template fixture.')


if __name__=='__main__':main()
