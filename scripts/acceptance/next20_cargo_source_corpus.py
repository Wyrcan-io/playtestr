"""Retain exact compiled registry source tar bodies in one bounded solid corpus.

Original gzip wrapper checksums remain acquisition provenance. The corpus retains
the complete decoded tar bytes and every original source-file byte, not the gzip
wrapper encoding. Historical retained packets are never rewritten.
"""
import gzip
import hashlib
import io
import json
import lzma
from pathlib import PurePosixPath
import tarfile

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256

MAX_ARCHIVE=48*1024**2
MAX_TAR=256*1024**2
MAX_TOTAL=1024**3


class Output:
    def __init__(self,output):self.output=output
    def write(self,data):
        if self.output.tell()+len(data)>MAX_ARCHIVE:raise ValueError('source corpus compressed size bound')
        return self.output.write(data)
    def flush(self):return self.output.flush()


class Decoder:
    """Tar streaming reader with explicit XZ memory, output and trailing bounds."""
    def __init__(self,path):
        self.source=path.open('rb');self.decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
        self.total=0
    def read(self,size):
        if size<0 or size>MAX_TAR:raise ValueError('source corpus reader request bound')
        output=bytearray()
        while len(output)<size:
            if self.decoder.eof:
                if self.decoder.unused_data or self.source.read(1):raise ValueError('trailing source corpus data')
                break
            block=self.source.read(65536) if self.decoder.needs_input else b''
            if not block and self.decoder.needs_input:raise ValueError('truncated source corpus')
            output.extend(self.decoder.decompress(block,max_length=size-len(output)))
        self.total+=len(output)
        if self.total>MAX_TOTAL+8*1024**2:raise ValueError('source corpus decoded bound')
        return bytes(output)
    def close(self):self.source.close()


def source_files(payload,package):
    files={};total=0
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:') as stream:
        for member in stream:
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!=package:raise ValueError('source member escaped package')
            if member.isdir():continue
            if not member.isfile() or member.size>32*1024**2 or member.name in files:raise ValueError('source member kind/size/duplicate')
            data=stream.extractfile(member).read(member.size+1);total+=len(data)
            if len(data)!=member.size or total>MAX_TAR or len(files)>60000:raise ValueError('source payload bound')
            files[member.name]=hashlib.sha256(data).hexdigest()
    return files


def main():
    target=RAW/'active/cargo-generate';plan_path=DOC/'cargo-generate/compiled-registry-retention-plan.json'
    plan=json.loads(plan_path.read_text());catalog_path=target/'dependency-source-catalog.json';catalog=json.loads(catalog_path.read_text())
    root=RAW/'cargo-generate/registry-source-corpus-v1';root.mkdir(parents=True,exist_ok=False)
    archive=root/'sources.tar.xz';records={};total=0;expected_files={}
    # 32MiB dictionary: explicitly bounded encoder working memory below512MiB,
    # one decoded crate below256MiB, decoder64MiB; no timing validation overlaps.
    with archive.open('xb') as output,lzma.LZMAFile(Output(output),'w',filters=[dict(id=lzma.FILTER_LZMA2,preset=6,dict_size=32*1024**2)]) as compressed,tarfile.open(fileobj=compressed,mode='w|') as stream:
        for name,row in plan['selected_archives'].items():
            path=target/row['original_source'];path.resolve(strict=True).relative_to(target.resolve(strict=True))
            if path.is_symlink() or path.stat().st_size!=row['bytes'] or sha256(path)!=row['sha256']:raise ValueError('original locked source archive changed')
            with gzip.open(path,'rb') as decoded:payload=decoded.read(MAX_TAR+1)
            total+=len(payload)
            if len(payload)>MAX_TAR or total>MAX_TOTAL:raise ValueError('source tar body bound')
            package=name.removesuffix('.crate');files=source_files(payload,package)
            expected={ '/'.join(PurePosixPath(n).parts[4:]):h for n,h in catalog['files'].items() if PurePosixPath(n).parts[4]==package }
            if files!=expected:raise ValueError('decoded exact crate source differs from original reviewed catalog')
            expected_files.update(files);member_name=package+'.tar';info=tarfile.TarInfo(member_name);info.size=len(payload);info.mode=0o644
            stream.addfile(info,io.BytesIO(payload))
            records[member_name]=dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),original_gzip_sha256=row['sha256'],original_gzip_bytes=row['bytes'])
    reader=Decoder(archive);seen=set();restored_files={}
    try:
        with tarfile.open(fileobj=reader,mode='r|') as stream:
            for member in stream:
                if member.name not in records or member.name in seen or not member.isfile() or member.size!=records[member.name]['bytes']:raise ValueError('source corpus member coverage differs')
                payload=stream.extractfile(member).read(MAX_TAR+1)
                if len(payload)!=member.size or hashlib.sha256(payload).hexdigest()!=records[member.name]['sha256']:raise ValueError('source corpus decoded tar bytes changed')
                restored_files.update(source_files(payload,member.name.removesuffix('.tar')));seen.add(member.name)
        while reader.read(65536):pass
    finally:reader.close()
    if seen!=set(records) or restored_files!=expected_files:raise ValueError('source corpus independent full readback differs')
    immutable_json(root/'index.json',dict(schema_version=1,encoding='tar-of-exact-decoded-crate-tars+xz',archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
        plan_sha256=sha256(plan_path),original_source_catalog_sha256=sha256(catalog_path),members=records,files=restored_files,
        decoded_tar_bytes=total,encoder_dictionary_bytes=32*1024**2,decoder_memory_limit_bytes=64*1024**2,
        original_gzip_wrapper_retained=False,source_payload_and_inner_tar_bytes_retained=True,
        scope='Actual compiled-source closure, including preserved failed builds; not branch coverage. Original gzip wrappers are acquisition checksum provenance only. No source/cache deletion or admission credit.'))
    print('Full source corpus roundtrip:',len(records),'crates,',len(restored_files),'files,',archive.stat().st_size,'compressed bytes',flush=True)


if __name__=='__main__':main()
