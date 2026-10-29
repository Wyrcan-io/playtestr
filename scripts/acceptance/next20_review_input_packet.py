"""Bounded exact retention of reviewed local primary metadata before target removal."""
import hashlib
import io
import json
import lzma
import tarfile

from readiness_evidence import immutable_json,sha256


def safe(name):
    if not name or name.startswith('/') or any(p in {'','.','..'} or ':' in p or '\\' in p for p in name.split('/')):raise ValueError('unsafe reviewed metadata path')


def write(root,payloads):
    if not payloads or len(payloads)>2000 or sum(map(len,payloads.values()))>16*1024**2:raise ValueError('reviewed metadata retention bound')
    archive=root/'review-inputs.tar.xz';index=root/'review-inputs-index.json'
    if archive.exists() or index.exists():raise ValueError('preserve original reviewed metadata packet')
    rows={}
    with tarfile.open(archive,'w:xz',preset=6) as stream:
        for name,body in sorted(payloads.items()):
            safe(name)
            if len(body)>4*1024**2:raise ValueError('reviewed metadata member bound')
            member=tarfile.TarInfo(name);member.size=len(body);member.mode=0o644;stream.addfile(member,io.BytesIO(body))
            rows[name]=dict(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    if archive.stat().st_size>8*1024**2:raise ValueError('reviewed metadata compressed bound')
    immutable_json(index,dict(schema_version=1,files=rows,archive_sha256=sha256(archive)))
    restored=read(root)
    if restored!=payloads:raise ValueError('reviewed primary metadata exact full readback differs')
    return rows


def read(root):
    index=json.loads((root/'review-inputs-index.json').read_text());archive=root/'review-inputs.tar.xz'
    if index['schema_version']!=1 or len(index['files'])>2000 or archive.stat().st_size>8*1024**2 or sha256(archive)!=index['archive_sha256']:raise ValueError('reviewed metadata packet identity/bound')
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
    expanded=decoder.decompress(archive.read_bytes(),max_length=20*1024**2+1)
    if len(expanded)>20*1024**2 or not decoder.eof or decoder.unused_data:raise ValueError('reviewed metadata expansion/framing bound')
    result={};total=0
    with tarfile.open(fileobj=io.BytesIO(expanded),mode='r:') as stream:
        for member in stream:
            safe(member.name)
            if not member.isfile() or member.size>4*1024**2 or member.name in result or member.name not in index['files']:raise ValueError('reviewed metadata member coverage/bound')
            body=stream.extractfile(member).read(4*1024**2+1);total+=len(body)
            if total>16*1024**2 or dict(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())!=index['files'][member.name]:raise ValueError('reviewed metadata actual bytes changed')
            result[member.name]=body
    if set(result)!=set(index['files']):raise ValueError('reviewed metadata omitted')
    return result
