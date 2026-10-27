"""Bind a native build to the once-retained complete compiled-source dictionary."""
import argparse
import hashlib
import json
import re
from pathlib import PurePosixPath

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def file_digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');args=parser.parse_args()
    package=DOC/'cargo-generate';target=RAW/'active/cargo-generate';plan_path=package/'compiled-registry-retention-plan.json'
    plan=json.loads(plan_path.read_text());selected=plan['selected_archives'];catalog=json.loads((target/'dependency-source-catalog.json').read_text())
    packages={n.removesuffix('.crate') for n in selected}
    files={'/'.join(PurePosixPath(n).parts[4:]):h for n,h in catalog['files'].items() if PurePosixPath(n).parts[4] in packages}
    for name,row in selected.items():
        if catalog['archives_sha256'].get(row['original_source'])!=row['sha256']:raise ValueError('native registry archive differs from canonical retained source')
    path=package/'registry-source-corpus-reference-v1.json'
    if args.publish:
        root=RAW/'cargo-generate/registry-source-corpus-v1';index_path=root/'index.json';index=json.loads(index_path.read_text())
        archive=root/'sources.tar.xz'
        if sha256(archive)!=index['archive_sha256'] or index['files']!=files or index['plan_sha256']!=sha256(plan_path):raise ValueError('canonical retained source corpus differs')
        immutable_json(path,dict(schema_version=1,plan_sha256=sha256(plan_path),required_dictionary_archive='registry-source-corpus-v1/sources.tar.xz',
            required_dictionary_archive_sha256=sha256(archive),required_dictionary_archive_bytes=archive.stat().st_size,
            required_dictionary_index_sha256=sha256(index_path),source_files=len(files),source_files_digest=file_digest(files),
            scope='Required once-retained source dictionary counted within project/aggregate caps; missing dictionary invalidates qualification. Exact decoded source/tar bytes, not original gzip wrappers.'))
        print('Published required source dictionary identity:',len(files),'files');return
    reference=json.loads(path.read_text())
    if reference['plan_sha256']!=sha256(plan_path) or reference['source_files_digest']!=file_digest(files) or reference['source_files']!=len(files):raise ValueError('native sources differ from required canonical dictionary')
    build=json.loads((target/'build.json').read_text());console=RAW/'cargo-generate'/build['build_attempt']/'console.log'
    compiled={name+'-'+version for name,version in re.findall(r'Compiling ([A-Za-z0-9_-]+) v([0-9][^\s]*)',console.read_text())}
    compiled.discard('cargo-generate-0.25.1')
    if not compiled or not compiled<=packages:raise ValueError('actual native compiler used an unretained registry source: '+str(sorted(compiled-packages)))
    immutable_json(target/'required-source-dictionary.json',dict(schema_version=1,reference_sha256=sha256(path),
        required_dictionary=reference,actual_build_receipt_sha256=sha256(target/'build.json'),actual_build_console_sha256=sha256(console),
        actual_compiled_registry_packages=sorted(compiled),actual_source_files_digest=file_digest(files),
        scope='Native original compile-source closure maps to required local retained dictionary; remote job does not claim to possess or independently decode the canonical local archive.'))
    print('Native compiled source closure binds required canonical dictionary:',len(compiled),'registry packages')


if __name__=='__main__':main()
