"""Retain exact local compiled-runtime catalogs without repeated expansions."""
import argparse
import gzip
import json
import re
import tarfile

from next20_check import RAW
from readiness_compact_native import physical_members,verify
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project',choices=['cz-cli','yo']);args=parser.parse_args()
    root=RAW/args.project;files={};total=0
    pattern=re.compile(re.escape(args.project)+r'/(?:runtime-catalogs/[0-9a-f]{64}\.json|rebuilds/[0-9a-f]{32}/runtime-catalog\.json|faults/[0-9a-f]{32}/F0[123]-(?:baseline|mutated|restored|terminal-only)-runtime-catalog\.json)')
    paths=[*root.glob('runtime-catalogs/*.json'),*root.glob('rebuilds/*/runtime-catalog.json'),*root.glob('faults/*/*-runtime-catalog.json')]
    for path in sorted(paths):
        name=path.relative_to(RAW).as_posix()
        if not pattern.fullmatch(name):raise ValueError('Unexpected catalog compaction scope')
        for parent in [path,*path.parents]:
            if parent==RAW:break
            if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():raise ValueError('Linked catalog entry/ancestor')
        size=path.stat().st_size;total+=size
        if size>4*1024**2 or total>128*1024**2 or len(files)>=256:raise ValueError('Local catalog retention bound')
        value=json.loads(path.read_text(encoding='utf-8'))
        if value.get('schema_version')!=1 or not isinstance(value.get('files'),dict):raise ValueError('Not a complete actual runtime catalog')
        files[name]=dict(bytes=size,sha256=sha256(path))
    if not files:raise ValueError('No actual catalogs to retain')
    seen={}
    for name,row in files.items():
        canonical=seen.setdefault((row['bytes'],row['sha256']),name)
        if canonical!=name:row['member']=canonical
    members=physical_members(files);output=root/'retained-catalogs-v1';output.mkdir()
    archive=output/'packets.tar.gz'
    with archive.open('xb') as destination:
        with gzip.GzipFile(filename='',mode='wb',fileobj=destination,mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as target:
                for name,row in sorted(members.items()):
                    path=RAW/name
                    if sha256(path)!=row['sha256']:raise ValueError('Catalog changed while retaining')
                    member=tarfile.TarInfo(name);member.size=row['bytes'];member.mode=0o644
                    with path.open('rb') as stream:target.addfile(member,stream)
                    if destination.tell()>16*1024**2:raise ValueError('Compressed catalog bound')
    verify(archive,files)
    selected=next(iter(files));restore=output/'selected-restore.json'
    with tarfile.open(archive,'r:gz') as stream:
        data=stream.extractfile(files[selected].get('member',selected)).read(4*1024**2+1)
    with restore.open('xb') as stream:stream.write(data)
    if sha256(restore)!=files[selected]['sha256']:raise ValueError('Selected catalog restore differs')
    immutable_json(output/'index.json',dict(schema_version=2,kind='local-interpreted-runtime-catalogs' if args.project=='yo' else 'local-compiled-runtime-catalogs',project=args.project,
        files=files,expanded_bytes=total,archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
        unique_payloads=len(members),selected_restore=dict(logical_path=selected,path='selected-restore.json',sha256=sha256(restore)),
        scope='Every original local catalog logical path/hash retained; exact bytes share only verified one-level in-archive members. No native execution or project credit.'))
    immutable_json(output/'verified.json',dict(index_sha256=sha256(output/'index.json'),archive_sha256=sha256(archive),
        logical_catalogs=len(files),physical_payloads=len(members),selected_restore_verified=True,expanded_removal_performed=False))
    print('Verified local runtime catalog retention:',len(files),'logical paths,',len(members),'exact payloads;',total,'expanded bytes;',archive.stat().st_size,'archive bytes. Literal-file removal still required.')


if __name__=='__main__':main()
