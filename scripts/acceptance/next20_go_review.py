"""Bind reviewed module archives, installed source and actual native compile inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from next20_check import DOC,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe Go review project')
    package=DOC/project;target=RAW/'active'/project;approval=json.loads((package/'dependency-source-review-declaration.json').read_text())
    fetch=json.loads((target/'module-fetch.json').read_text());inputs=json.loads((target/'native-package-inputs.json').read_text())
    primary=json.loads((package/'source-provenance.json').read_text());catalog={};modules=[];count=0;total=0
    if approval['pin']!=primary['pin'] or not approval['approved_for_native_build']:raise ValueError('native build not approved')
    for row in fetch['modules']:
        key=row['Path']+'@'+row['Version'];review=approval['modules'][key];directory=Path(row['Dir']);archive=Path(row['Zip'])
        directory.resolve(strict=True).relative_to(target.resolve(strict=True));archive.resolve(strict=True).relative_to(target.resolve(strict=True))
        if sha256(archive)!=review['zip_sha256'] or row['Sum']!=review['go_sum'] or row['GoModSum']!=review['go_mod_sum']:raise ValueError('module archive/checksum identity differs')
        license_paths={}
        for name,digest in review['licenses'].items():
            if sha256(directory/name)!=digest:raise ValueError('reviewed module license differs')
            license_paths[name]=digest
        with zipfile.ZipFile(archive) as bundle:
            names=set()
            for member in bundle.infolist():
                if member.is_dir():continue
                prefix=key+'/'
                if not member.filename.startswith(prefix):raise ValueError('module ZIP root differs')
                relative=member.filename.removeprefix(prefix)
                if relative in names or any(p in {'','.','..'} or ':' in p or '\\' in p for p in relative.split('/')):raise ValueError('unsafe/duplicate module member')
                names.add(relative);count+=1;total+=member.file_size
                if count>20000 or member.file_size>8*1024**2 or total>256*1024**2:raise ValueError('module source readback bound')
                body=bundle.read(member);path=directory/relative
                if not path.is_file() or path.is_symlink() or sha256(path)!=hashlib.sha256(body).hexdigest():raise ValueError('actual installed module source differs: '+key+':'+relative)
                catalog[path.relative_to(target).as_posix()]=hashlib.sha256(body).hexdigest()
        modules.append(dict(path=row['Path'],version=row['Version'],zip_relative_path=archive.relative_to(target).as_posix(),zip_sha256=sha256(archive),go_sum=row['Sum'],go_mod_sum=row['GoModSum'],license=review['license'],licenses=license_paths))
    if len(modules)!=len(approval['modules']):raise ValueError('reviewed module coverage differs')
    for name,digest in primary['files'].items():
        if sha256(target/'src'/name)!=digest:raise ValueError('reviewed primary source changed')
        catalog['src/'+name]=digest
    for name,digest in inputs['files'].items():
        if catalog.get(name)!=digest:raise ValueError('actual compile input absent from reviewed primary/module ZIP bytes')
    helper=ROOT/approval['capture_helper']
    if sha256(helper)!=approval['capture_helper_sha256']:raise ValueError('reviewed stdout capture helper changed')
    immutable_json(target/'dependency-source-catalog.json',dict(schema_version=1,files=catalog,modules=modules,source_bytes=total,
        actual_native_compile_inputs=inputs['files'],native_package_inputs_sha256=sha256(target/'native-package-inputs.json'),
        scope='Every downloaded module archive member equals its installed source,all actual non-standard compile inputs equal primary/archive bytes. SDK/standard library identified as compiler prerequisite,not a retained SDK or sandbox.'))
    immutable_json(target/'dependency-fetch-review.json',dict(schema_version=1,approved=True,modules=modules,source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),source_review_declaration_sha256=sha256(package/'dependency-source-review-declaration.json'),target_executed=False))
    print('Verified',len(modules),'module archives/licenses,',count,'actual module source members and',len(inputs['files']),'native compile inputs; reviewed build approved, target not executed.')


if __name__=='__main__':main()
