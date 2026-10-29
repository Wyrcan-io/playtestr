"""Prepare bounded exact local evidence compaction with native checked disposal.

Existing compressed source/executable dictionaries and native packets stay
separate mandatory dependencies. Historical packet formats remain unchanged.
"""
import argparse
import hashlib
import io
import json
import lzma
import re
from pathlib import Path
import tarfile

from next20_check import RAW,ROOT,DOC
from readiness_evidence import immutable_json,sha256


def safe_path(name,project):
    if not name.startswith(project+'/') or len(name)>4096 or any(part in {'','.','..'} or ':' in part or '\\' in part for part in name.split('/')):raise ValueError('unsafe local record logical path')
    path=RAW/name;path.resolve().relative_to((RAW/project).resolve())
    for ancestor in [path,*path.parents]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked local record path')
        if ancestor==RAW:break
    return path


def read_packet(project,*,packet='retained-local-v1'):
    if not re.fullmatch(r'retained-(?:local|failed-final)-v[1-9][0-9]{0,2}',packet):raise ValueError('unsafe local packet namespace')
    root=RAW/project/packet;index_path=root/'index.json';index=json.loads(index_path.read_text());archive=root/'packets.tar.xz'
    if index['project']!=project or index['compression']!='tar.xz' or len(index['files'])>4000 or archive.stat().st_size>8*1024**2 or sha256(archive)!=index['archive_sha256']:raise ValueError('local record packet identity/bound differs')
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
    expanded=decoder.decompress(archive.read_bytes(),max_length=64*1024**2+1)
    if len(expanded)>64*1024**2 or not decoder.eof or decoder.unused_data:raise ValueError('local record XZ framing/expansion bound')
    result={};total=0
    with tarfile.open(fileobj=io.BytesIO(expanded),mode='r:') as stream:
        for member in stream:
            safe_path(member.name,project)
            if not member.isfile() or member.name in result or member.name not in index['files'] or member.size>16*1024**2:raise ValueError('local record member coverage/type/size differs')
            data=stream.extractfile(member).read(16*1024**2+1);total+=len(data)
            if total>32*1024**2 or dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())!=index['files'][member.name]:raise ValueError('actual retained local bytes differ')
            result[member.name]=data
    if set(result)!=set(index['files']):raise ValueError('local evidence member omitted')
    return index,result


def prepare(project):
    if not (DOC/project/'source-provenance.json').is_file():raise ValueError('undeclared evidence project')
    if (RAW/'active'/project).exists():raise ValueError('checked target source/runtime removal required before local evidence compaction')
    root=RAW/project/'retained-local-v1'
    if root.exists():raise ValueError('preserve original local retention attempt')
    files={};total=0
    for path in sorted((RAW/project).rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(RAW/project)
        if relative.parts[0].startswith(('retained-native-','retained-local-','retained-failed-final-','registry-source-corpus-','native-solid-variants')):continue
        if relative.parts[0] in {'audits','audit-controls'} or path.suffix in {'.gz','.tgz','.xz'}:continue
        name=path.relative_to(RAW).as_posix();safe_path(name,project);size=path.stat().st_size;total+=size
        if len(files)>=4000 or size>16*1024**2 or total>32*1024**2:raise ValueError('local evidence inventory bound')
        files[name]=dict(bytes=size,sha256=sha256(path))
    if not files:raise ValueError('no actual evidence records')
    root.mkdir();archive=root/'packets.tar.xz'
    with tarfile.open(archive,'w:xz',preset=6) as stream:
        for name,row in files.items():
            path=safe_path(name,project)
            if sha256(path)!=row['sha256']:raise ValueError('actual local evidence changed during retention')
            info=tarfile.TarInfo(name);info.size=row['bytes'];info.mode=0o644
            with path.open('rb') as payload:stream.addfile(info,payload)
    immutable_json(root/'index.json',dict(schema_version=1,project=project,compression='tar.xz',files=files,archive_sha256=sha256(archive),expanded_bytes=total,
        scope='Exact actual local logical records. Compressed source/executable dictionaries and native packets remain mandatory separate retained dependencies. No application/scenario/admission credit.'))
    index,payloads=read_packet(project)
    selected=next(name for name in files if name.endswith('/first-ordinary-report.json'));restore=root/'selected-restore.bin';restore.write_bytes(payloads[selected])
    if sha256(restore)!=files[selected]['sha256']:raise ValueError('selected actual report restoration differs')
    immutable_json(root/'prepared.json',dict(schema_version=1,index_sha256=sha256(root/'index.json'),archive_sha256=sha256(archive),
        selected_restore=dict(logical_path=selected,sha256=sha256(restore)),expanded_removal_confirmed=False))
    print('Prepared and fully read back',len(files),'actual local records:',total,'expanded ->',archive.stat().st_size,'XZ bytes; native checked duplicate removal pending')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--readback',action='store_true');args=parser.parse_args()
    if not (DOC/args.project/'source-provenance.json').is_file() or '/' in args.project or '\\' in args.project:raise ValueError('undeclared project')
    if args.readback:
        index,files=read_packet(args.project);print('Verified complete retained local packet:',len(files),'exact logical records')
    else:prepare(args.project)


if __name__=='__main__':main()
