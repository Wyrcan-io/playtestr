"""Deduplicate exact archive bytes without changing their original index/format."""
import argparse
import gzip
import json
from pathlib import Path
import re

from next20_archive_delta import encode,decode,digest
from next20_check import RAW
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def dictionary_bytes(base,view):
    payload=base.read_bytes()
    if view=='gzip-bytes':return payload
    if view!='gzip-bytes+decoded-tar':raise ValueError('unknown canonical dictionary view')
    with gzip.open(base,'rb') as stream:decoded=stream.read(16*1024**2+1)
    if len(decoded)>16*1024**2:raise ValueError('decoded canonical dictionary bound')
    return payload+decoded


def representation_identity(root):
    path=root/'archive-representation.json';record=json.loads(path.read_text())
    project=root.parent.name
    if record['format']!='exact-original-gzip+copy-insert-v1' or record['original_archive']!='packets.tar.gz' or record['delta_file']!='archive.delta.xz':raise ValueError('unrecognized native archive representation')
    reference=record['required_dictionary']
    if not re.fullmatch(re.escape(project)+r'/retained-native-v[0-9]{1,4}/packets\.tar\.gz',reference):raise ValueError('unsafe required archive dictionary path')
    base=RAW/reference;base.resolve(strict=True).relative_to((RAW/project).resolve(strict=True))
    if base.parent==root or not base.is_file() or (base.parent/'archive-representation.json').exists():raise ValueError('archive representation dictionary chain/cycle/missing payload')
    for ancestor in [root,root.parent,RAW,RAW.parent,base,base.parent]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked archive representation/dictionary path')
    if sha256(base)!=record.get('required_dictionary_archive_sha256',record['codec']['base_sha256']) or sha256(base.parent/'index.json')!=record['required_dictionary_index_sha256']:raise ValueError('required canonical archive dictionary changed')
    if sha256(root/'index.json')!=record['original_index_sha256'] or sha256(root/record['delta_file'])!=record['codec']['delta_sha256']:raise ValueError('original index or encoded archive bytes changed')
    index=json.loads((root/'index.json').read_text())
    if record['codec']['target_sha256']!=index['archive_sha256']:raise ValueError('archive representation is not the exact original indexed archive')
    proof=json.loads((root/'archive-representation-verified.json').read_text())
    if proof['representation_sha256']!=sha256(path) or proof['original_index_sha256']!=sha256(root/'index.json'):raise ValueError('archive representation verification changed')
    return record,base,sha256(path)


def restore_archive(root):
    record,base,_=representation_identity(root)
    result=decode(dictionary_bytes(base,record.get('required_dictionary_view','gzip-bytes')),(root/record['delta_file']).read_bytes(),record['codec'])
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--generation',type=int,required=True);parser.add_argument('--dictionary-generation',type=int,required=True)
    parser.add_argument('--dictionary-view',choices=['gzip-bytes','gzip-bytes+decoded-tar'],default='gzip-bytes+decoded-tar');args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project) or not 1<=args.generation<=1000 or not 1<=args.dictionary_generation<=1000:raise ValueError('invalid archive representation scope')
    root=RAW/args.project/('retained-native-v'+str(args.generation));base_root=RAW/args.project/('retained-native-v'+str(args.dictionary_generation))
    original=root/'packets.tar.gz';base=base_root/'packets.tar.gz'
    for path in [original,base]:
        path.resolve(strict=True).relative_to((RAW/args.project).resolve(strict=True))
        if path.is_symlink() or path.stat().st_size>16*1024**2:raise ValueError('archive dictionary/target bound')
    index=json.loads((root/'index.json').read_text());base_index=json.loads((base_root/'index.json').read_text())
    if sha256(original)!=index['archive_sha256'] or sha256(base)!=base_index['archive_sha256']:raise ValueError('original native archive index differs')
    from next20_packet_archive import verify
    verify(original,index['files']);verify(base,base_index['files'])
    payload,codec=encode(dictionary_bytes(base,args.dictionary_view),original.read_bytes())
    available=64*1024**2-measure(RAW/args.project)['total_bytes']-65536
    print('Measured exact archive representation:',len(payload),'bytes; available',available,'copies',codec['copy_operations'],flush=True)
    if len(payload)>=original.stat().st_size or len(payload)>available:raise ValueError('lossless archive representation does not fit measured headroom or save bytes')
    delta=root/'archive.delta.xz'
    with delta.open('xb') as stream:stream.write(payload)
    record=dict(schema_version=1,format='exact-original-gzip+copy-insert-v1',original_archive='packets.tar.gz',
        original_index_sha256=sha256(root/'index.json'),delta_file=delta.name,codec=codec,
        required_dictionary=base.relative_to(RAW).as_posix(),required_dictionary_index_sha256=sha256(base_root/'index.json'),
        required_dictionary_archive_sha256=sha256(base),required_dictionary_view=args.dictionary_view,
        scope='Original gzip bytes/index/all logical file identities remain unchanged. Exact COPY/INSERT representation requires this still-physical canonical dictionary, counted once. No unlike-byte alias, chain, payload deletion or qualification credit.')
    path=root/'archive-representation.json';immutable_json(path,record)
    immutable_json(root/'archive-representation-verified.json',dict(schema_version=1,representation_sha256=sha256(path),original_index_sha256=sha256(root/'index.json'),
        original_archive_sha256=sha256(original),required_dictionary_sha256=sha256(base),delta_sha256=sha256(delta),full_original_gzip_byte_roundtrip=True,expanded_archive_removal_pending=True))
    if restore_archive(root)!=original.read_bytes():raise ValueError('on-disk representation does not reconstruct every original archive byte')
    print('Exact original gzip bytes fully restored:',original.stat().st_size,'->',len(payload),'dictionary representation bytes; original index/format unchanged, native duplicate removal pending')


if __name__=='__main__':main()
