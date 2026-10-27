"""Lossless solid archive of actual source-built native executable variants."""
import json
import os
from pathlib import Path
import tarfile
import lzma
import hashlib

from next20_check import RAW,ROOT
from next20_cargo_source_corpus import Decoder
from readiness_evidence import immutable_json,sha256


class Output:
    def __init__(self,output):self.output=output
    def write(self,data):
        if self.output.tell()+len(data)>16*1024**2:raise ValueError('solid native executable archive bound')
        return self.output.write(data)
    def flush(self):return self.output.flush()


def main():
    host='windows' if os.name=='nt' else 'linux';project=RAW/'cargo-generate';target=RAW/'active/cargo-generate'
    base=json.loads((target/'runtime.json').read_text());binary=Path(base['native'])
    if sha256(binary)!=base['native_sha256']:raise ValueError('pristine executable changed')
    root=project/'native-solid-variants'/host;root.mkdir(parents=True,exist_ok=False)
    compiled=project/('source-fault-development/v1' if os.name=='nt' else 'source-fault-final-native-exit-v1/v1')
    records={'original':dict(path=binary,sha256=base['native_sha256'])}
    # Keep related22MiB executables within the32MiB dictionary distance.
    for fault in ['F03','F02','F01']:
        receipt=compiled/(fault+'-compiled.json');value=json.loads(receipt.read_text());path=ROOT/value['binary']
        records[fault]=dict(path=path,sha256=value['binary_sha256'],compile_receipt=receipt.relative_to(ROOT).as_posix(),compile_receipt_sha256=sha256(receipt))
    archive=root/'executables.tar.xz';index={};total=0
    with archive.open('xb') as output,lzma.LZMAFile(Output(output),'w',filters=[dict(id=lzma.FILTER_LZMA2,preset=6,dict_size=32*1024**2)]) as compressed,tarfile.open(fileobj=compressed,mode='w|') as stream:
        for name,row in records.items():
            path=row['path'];path.resolve(strict=True).relative_to(target.resolve(strict=True));size=path.stat().st_size;total+=size
            if path.is_symlink() or size>64*1024**2 or total>256*1024**2 or sha256(path)!=row['sha256']:raise ValueError('actual compiled executable changed/bound')
            member=tarfile.TarInfo(name);member.size=size;member.mode=0o755
            with path.open('rb') as payload:stream.addfile(member,payload)
            index[name]={k:v for k,v in row.items() if k!='path'};index[name]['bytes']=size
    reader=Decoder(archive);seen=set()
    try:
        with tarfile.open(fileobj=reader,mode='r|') as stream:
            for member in stream:
                if member.name not in index or member.name in seen or not member.isfile() or member.size!=index[member.name]['bytes']:raise ValueError('solid executable coverage/type/size differs')
                digest=hashlib.sha256();size=0
                with stream.extractfile(member) as payload:
                    while block:=payload.read(65536):size+=len(block);digest.update(block)
                if size!=member.size or digest.hexdigest()!=index[member.name]['sha256']:raise ValueError('actual executable full-byte restore failed')
                seen.add(member.name)
        while reader.read(65536):pass
    finally:reader.close()
    if seen!=set(index):raise ValueError('missing retained actual executable')
    immutable_json(root/'index.json',dict(schema_version=1,encoding='solid-tar+xz',files=index,
        archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,decoded_binary_bytes=total,
        encoder_dictionary_bytes=32*1024**2,decoder_memory_limit_bytes=64*1024**2,
        scope='Every actual pristine/F01/F02/F03 source-built executable byte retained and fully independently read back. No admission or target deletion credit.'))
    print('Retained full native executable corpus:',host,archive.stat().st_size,'compressed bytes; all4 actual binary hashes restored',flush=True)


if __name__=='__main__':main()
