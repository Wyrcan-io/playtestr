"""Retain exact local records in XZ and perform bounded genuine restored audits."""
import argparse
from functools import lru_cache
import hashlib
import io
import json
import lzma
import tarfile
import uuid

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


def packet_root():return RAW/'yo/retained-local-v1'


def safe_path(name):
    if not name.startswith('yo/') or len(name)>4096 or any(p in {'','.','..'} or ':' in p or '\\' in p for p in name.split('/')):
        raise ValueError('Unsafe local record path')
    path=RAW/name;path.resolve().relative_to((RAW/'yo').resolve())
    RAW.resolve().relative_to(ROOT.resolve())
    for ancestor in [path,*path.parents]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('Linked local record path')
        if ancestor==RAW:break
    return path


@lru_cache(maxsize=1)
def load_packet(index_digest,archive_digest):
    root=packet_root();index=json.loads((root/'index.json').read_text())
    if index['compression']!='tar.xz' or index['archive_sha256']!=archive_digest or len(index['files'])>4000:
        raise ValueError('Local record packet identity/bounds differ')
    archive=root/'packets.tar.xz'
    if archive.stat().st_size>8*1024**2:raise ValueError('Local compressed packet bound')
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
    expanded=decoder.decompress(archive.read_bytes(),max_length=64*1024**2+1)
    if len(expanded)>64*1024**2 or not decoder.eof or decoder.unused_data:raise ValueError('Local XZ frame/expansion bound')
    result={};total=0
    with tarfile.open(fileobj=io.BytesIO(expanded),mode='r:') as bundle:
        for member in bundle:
            safe_path(member.name)
            if member.name in result or member.name not in index['files'] or not member.isfile() or member.size>16*1024**2:
                raise ValueError('Local record archive coverage/type bound')
            data=bundle.extractfile(member).read(16*1024**2+1);total+=len(data)
            if total>32*1024**2 or dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())!=index['files'][member.name]:
                raise ValueError('Local record archive member mismatch')
            result[member.name]=data
    if set(result)!=set(index['files']):raise ValueError('Local record archive omitted member')
    return index,result


def verified_packet():
    root=packet_root();safe_path(root.relative_to(RAW).as_posix()+'/verified.json')
    proof=json.loads((root/'verified.json').read_text())
    if proof['index_sha256']!=sha256(root/'index.json') or proof['archive_sha256']!=sha256(root/'packets.tar.xz'):
        raise ValueError('Local record index/archive changed')
    return load_packet(proof['index_sha256'],proof['archive_sha256'])


def read_bytes(path):
    path.resolve().relative_to(ROOT)
    if path.is_file():return path.read_bytes()
    _,files=verified_packet();name=path.relative_to(RAW).as_posix()
    if name not in files:raise FileNotFoundError('No retained local record: '+name)
    return files[name]


def compact():
    project=RAW/'yo';root=packet_root()
    if (RAW/'active/yo').exists() or root.exists():raise ValueError('Checked target removal and fresh packet required')
    files={};total=0
    # Keep canonical package/source archives and native models/packets available
    # directly. Pack the original local reports, command logs and metadata once.
    for path in sorted(project.rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(project)
        if relative.parts[0].startswith(('retained-native-','retained-catalogs-','retained-local-')) or relative.parts[0] in {'audits','audit-controls'}:
            continue
        if relative.parts[:2]==('retained-source','npm-cache') or path.suffix in {'.gz','.tgz','.xz'}:continue
        name=path.relative_to(RAW).as_posix();safe_path(name)
        size=path.stat().st_size;total+=size
        if len(files)>=4000 or size>16*1024**2 or total>32*1024**2:raise ValueError('Local record inventory bound')
        files[name]=dict(bytes=size,sha256=sha256(path))
    if not files:raise ValueError('No actual local records to retain')
    root.mkdir();archive=root/'packets.tar.xz'
    with tarfile.open(archive,'w:xz',format=tarfile.PAX_FORMAT,preset=6) as bundle:
        for name,row in files.items():
            path=safe_path(name)
            if sha256(path)!=row['sha256']:raise ValueError('Local record changed during retention')
            member=tarfile.TarInfo(name);member.size=row['bytes'];member.mode=0o644
            with path.open('rb') as source:bundle.addfile(member,source)
    immutable_json(root/'index.json',dict(schema_version=1,project='yo',compression='tar.xz',files=files,
        archive_sha256=sha256(archive),expanded_bytes=total,
        scope='Every original local logical path and exact bytes retained. Canonical gzip packages/source and independent native packets remain separate mandatory members of the same project closure. No scenario or admission credit.'))
    immutable_json(root/'verified.json',dict(schema_version=1,index_sha256=sha256(root/'index.json'),archive_sha256=sha256(archive)))
    _,payloads=verified_packet()
    selected=next(n for n in files if n.endswith('/first-ordinary-report.json'))
    restore=root/'selected-restore.bin';restore.write_bytes(payloads[selected])
    if sha256(restore)!=files[selected]['sha256']:raise ValueError('Selected genuine report restore differs')
    for name,row in files.items():
        if sha256(safe_path(name))!=row['sha256']:raise ValueError('Local record changed before exact duplicate removal')
    for name in files:safe_path(name).unlink()
    if any(safe_path(name).exists() for name in files):raise ValueError('Local record expansion remains')
    immutable_json(root/'expanded-removed.json',dict(schema_version=1,all_expanded_removed=True,
        index_sha256=sha256(root/'index.json'),archive_sha256=sha256(archive),files=len(files),
        selected_restore=dict(logical_path=selected,sha256=sha256(restore)),
        scope='Literal exact local record files removed only after full member verification and selected actual report restoration.'))
    print('Retained exact local records:',len(files),'files,',total,'expanded ->',archive.stat().st_size,'XZ bytes; original logical bytes remain recoverable.')


def audit():
    index,files=verified_packet();root=packet_root();operation=root/'audits'/uuid.uuid4().hex
    operation.mkdir(parents=True)
    if any(safe_path(name).exists() for name in files):raise ValueError('Do not overwrite an existing local record during audit restore')
    restored=[];passed=False
    try:
        for name,data in files.items():
            path=safe_path(name);path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(data)
            restored.append(name)
        from next20_yo_local_audit import main as audit_local
        audit_local();passed=True
    finally:
        for name in restored:
            if sha256(safe_path(name))!=index['files'][name]['sha256']:
                raise ValueError('Restored local evidence changed; preserve it for investigation')
        for name in restored:safe_path(name).unlink()
        immutable_json(operation/'checked.json',dict(schema_version=1,actual_local_audit_passed=passed,
            index_sha256=sha256(root/'index.json'),archive_sha256=sha256(root/'packets.tar.xz'),
            exact_records_restored=len(restored),all_restored_duplicates_removed=True,
            scope='Bounded temporary exact restoration at original logical paths for the actual independent local auditor; native/canonical evidence unchanged.'))
    print('Genuine complete local audit passed from exact XZ record restoration; temporary duplicates checked-removed.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['compact','audit','readback']);args=parser.parse_args()
    if args.operation=='compact':compact()
    elif args.operation=='audit':audit()
    else:
        index,files=verified_packet()
        print('Verified exact bounded XZ readback:',len(files),'original local record paths,',index['expanded_bytes'],'bytes.')


if __name__=='__main__':main()
