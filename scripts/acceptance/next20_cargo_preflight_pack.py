"""Retain exact source-built preflight binary bytes without a large expanded upload."""
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import tarfile

from next20_check import RAW,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    target=RAW/'active/cargo-generate';build=json.loads((target/'build.json').read_text())
    runtime=json.loads((target/'runtime.json').read_text());binary=Path(runtime['native'])
    binary.resolve(strict=True).relative_to(target.resolve(strict=True))
    if binary.is_symlink() or sha256(binary)!=build['binary_sha256'] or sha256(binary)!=runtime['native_sha256']:raise ValueError('actual compiled binary differs')
    if binary.stat().st_size>64*1024**2:raise ValueError('native binary preflight retention bound')
    host='windows' if os.name=='nt' else 'linux';root=RAW/'cargo-generate/native-preflight'/host;root.mkdir(parents=True)
    archive=root/'compiled-binary.tar.xz'
    if archive.exists():raise ValueError('preserve completed preflight binary retention')
    files={binary.name:binary,'build.json':target/'build.json','version-check.json':target/'version-check.json'}
    index={n:dict(bytes=p.stat().st_size,sha256=sha256(p)) for n,p in files.items()}
    class BoundedOutput:
        def __init__(self,output):self.output=output
        def write(self,data):
            if self.output.tell()+len(data)>16*1024**2:raise ValueError('compressed preflight archive size stop')
            return self.output.write(data)
        def flush(self):return self.output.flush()
    with archive.open('xb') as output,lzma.LZMAFile(BoundedOutput(output),'w',preset=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as stream:
        for name,path in files.items():
            info=tarfile.TarInfo(name);info.size=path.stat().st_size;info.mode=0o755 if name==binary.name else 0o644
            with path.open('rb') as payload:stream.addfile(info,payload)
    if archive.stat().st_size>16*1024**2:raise ValueError('compressed native preflight binary exceeds declared16MiB')
    seen=set()
    with tarfile.open(archive,'r:xz') as stream:
        for member in stream:
            if not member.isfile() or member.name not in index or member.name in seen or member.size!=index[member.name]['bytes']:raise ValueError('retained binary layout differs')
            digest=hashlib.sha256();size=0
            with stream.extractfile(member) as payload:
                while block:=payload.read(65536):size+=len(block);digest.update(block)
            if size!=member.size or digest.hexdigest()!=index[member.name]['sha256']:raise ValueError('retained binary bytes differ')
            seen.add(member.name)
    if seen!=set(index):raise ValueError('retained binary incomplete')
    immutable_json(root/'compiled-binary-index.json',dict(schema_version=1,host=host,files=index,
        archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,actual_native_binary=binary.relative_to(ROOT).as_posix(),
        scope='Exact source-built preflight executable and actual build/version metadata. No final series, source deletion or project-admission credit.'))
    print('Retained and independently read back exact preflight binary:',host,archive.stat().st_size,'compressed bytes')


if __name__=='__main__':main()
