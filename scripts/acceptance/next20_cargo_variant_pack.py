"""Retain every compiled fault byte using the independently retained baseline."""
import argparse
import json
import os
from pathlib import Path
import tarfile

from next20_binary_delta import encode,decode,digest
from next20_check import RAW,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--exploratory-compiled',action='store_true');args=parser.parse_args()
    host='windows' if os.name=='nt' else 'linux';project=RAW/'cargo-generate'
    compiled=project/('source-fault-development/v1' if args.exploratory_compiled else 'source-fault-final-native-exit-v1/v1')
    baseline_root=project/'native-preflight'/host;index_path=baseline_root/'compiled-binary-index.json'
    index=json.loads(index_path.read_text());archive=baseline_root/'compiled-binary.tar.xz'
    if sha256(archive)!=index['archive_sha256']:raise ValueError('retained baseline archive changed')
    name='cargo-generate.exe' if os.name=='nt' else 'cargo-generate'
    with tarfile.open(archive,'r:xz') as stream:
        member=stream.getmember(name)
        if not member.isfile() or member.size!=index['files'][name]['bytes'] or member.size>64*1024**2:raise ValueError('baseline member bound')
        base=stream.extractfile(member).read(64*1024**2+1)
    if digest(base)!=index['files'][name]['sha256']:raise ValueError('retained actual baseline bytes changed')
    destination=project/'native-variant-retention'/host;destination.mkdir(parents=True,exist_ok=False)
    records={}
    for fault in ['F01','F02','F03']:
        receipt=compiled/(fault+'-compiled.json');value=json.loads(receipt.read_text());variant=ROOT/value['binary']
        variant.resolve(strict=True).relative_to((RAW/'active/cargo-generate').resolve(strict=True))
        if variant.is_symlink() or variant.stat().st_size!=value['binary_bytes'] or sha256(variant)!=value['binary_sha256']:raise ValueError('actual compiled variant changed')
        payload,row=encode(base,variant.read_bytes());path=destination/(fault+'.xor.xz');path.write_bytes(payload)
        if digest(decode(base,path.read_bytes(),row))!=value['binary_sha256']:raise ValueError('retained actual variant restore failed')
        records[fault]=dict(**row,delta_file=path.name,compile_receipt=receipt.relative_to(ROOT).as_posix(),compile_receipt_sha256=sha256(receipt))
        print(host,fault,len(payload),'bytes; full actual executable roundtrip passed',flush=True)
    immutable_json(destination/'index.json',dict(schema_version=1,host=host,variants=records,
        required_baseline_archive=archive.relative_to(ROOT).as_posix(),required_baseline_archive_sha256=sha256(archive),
        required_baseline_index=index_path.relative_to(ROOT).as_posix(),required_baseline_index_sha256=sha256(index_path),baseline_member=name,
        scope='All actual compiled variant bytes retained losslessly. Baseline dictionary is mandatory and counted; no new target execution or source/runtime deletion.'))


if __name__=='__main__':main()
