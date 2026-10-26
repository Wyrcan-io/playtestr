"""Retain the initial case package before correcting unsupported authoring keys."""
import json
import shutil

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'cargo-generate';retained=RAW/'cargo-generate/development-inputs-v1'
    if retained.exists():raise ValueError('preserve initial case package')
    originals={};total=0
    for path in package.rglob('*'):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked case input')
        if path.is_file():
            total+=path.stat().st_size
            if len(originals)>=4000 or total>16*1024**2:raise ValueError('case package retention bound')
            originals[path.relative_to(package).as_posix()]=sha256(path)
    shutil.copytree(package,retained)
    for name,digest in originals.items():
        if sha256(retained/name)!=digest:raise ValueError('retained original case input differs')
    declaration=package/'scenarios.json';value=json.loads(declaration.read_text());changes=[]
    for case in value['cases']:
        path=package/case['spec'];path.resolve(strict=True).relative_to(package.resolve(strict=True))
        data=json.loads(path.read_text());before=sha256(path);changed=False
        for step in data['steps']:
            if step.get('key') in {'Up','Down'}:
                step['key']='Arrow'+step['key'];changed=True
        if changed:
            path.write_text(json.dumps(data,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
            case['spec_sha256']=sha256(path);changes.append(dict(case=case['id'],before=before,after=sha256(path)))
    if not changes:raise ValueError('no declared authoring key correction')
    declaration.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'development-key-disposition.json',dict(schema_version=1,
        initial_package=retained.relative_to(RAW).as_posix(),retained_files=originals,changes=changes,
        first_report='cargo-generate/development/7df7b5002e034415a28e82bc6ca8b116/N02.report.json',
        first_report_sha256=sha256(RAW/'cargo-generate/development/7df7b5002e034415a28e82bc6ca8b116/N02.report.json'),
        first_attempt='e742eb13d0b14e549e9ce6fdf802951f',
        disposition='Runner correctly refused unknown authoring key Down before target/workspace launch. Corrected to documented ArrowDown/ArrowUp; no product or target source change, and no target cleanup/execution credit for this prelaunch refusal.'))
    print('Retained initial package and corrected',len(changes),'case key spellings; original prelaunch failure remains.')


if __name__=='__main__':main()
