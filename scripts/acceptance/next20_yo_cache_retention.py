"""Retain exact non-package npm cache bytes compactly before checked cleanup."""
import gzip
import io
import json
import tarfile

from next20_check import RAW
from readiness_evidence import immutable_json, sha256


def main():
    target=RAW/'active/yo';cache=target/'npm-cache'
    owner=json.loads((target/'task-owned.json').read_text())
    if owner['slug']!='yo':raise ValueError('Wrong owned cache target')
    retained=target/'npm-metadata-retention'
    if retained.exists():raise ValueError('Preserve existing cache retention attempt')
    files={};total=0
    for path in cache.rglob('*'):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('Linked cache input')
        if not path.is_file():continue
        with path.open('rb') as stream:signature=stream.read(2)
        if signature==b'\x1f\x8b':continue
        size=path.stat().st_size;total+=size
        if len(files)>=4000 or size>16*1024**2 or total>80*1024**2:raise ValueError('Cache metadata retention bound')
        files[path.relative_to(target).as_posix()]=dict(bytes=size,sha256=sha256(path))
    retained.mkdir();archive=retained/'packets.tar.gz'
    with archive.open('xb') as output,gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as zipped,tarfile.open(fileobj=zipped,mode='w|',format=tarfile.PAX_FORMAT) as bundle:
        for name,row in sorted(files.items()):
            data=(target/name).read_bytes()
            if len(data)!=row['bytes'] or sha256(target/name)!=row['sha256']:raise ValueError('Cache changed during retention')
            member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o644
            bundle.addfile(member,io.BytesIO(data))
    if archive.stat().st_size>16*1024**2:raise ValueError('Cache metadata compressed bound')
    observed={}
    with tarfile.open(archive,'r|gz') as bundle:
        for member in bundle:
            if member.name not in files or not member.isfile() or member.size!=files[member.name]['bytes']:
                raise ValueError('Unexpected cache retention member')
            data=bundle.extractfile(member).read(16*1024**2+1)
            import hashlib
            observed[member.name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if observed!=files:raise ValueError('Exact cache readback differs')
    immutable_json(retained/'index.json',dict(schema_version=1,project='yo',kind='exact-npm-nonpackage-cache',
        files=files,archive_sha256=sha256(archive),expanded_bytes=total,
        package_payloads='Original gzip package bytes stay at their original cache paths; metadata and logs remain exactly recoverable from this self-contained archive.'))
    # One process, literal owned cache file paths; no recursive or computed-root
    # deletion. Verify all inputs again before unlinking the exact retained set.
    resolved_cache=cache.resolve(strict=True)
    for name,row in files.items():
        path=target/name;path.resolve(strict=True).relative_to(resolved_cache)
        if path.is_symlink() or sha256(path)!=row['sha256']:raise ValueError('Cache changed before exact duplicate removal')
    for name in files:(target/name).unlink()
    if any((target/name).exists() for name in files):raise ValueError('Retained cache duplicate remains')
    immutable_json(retained/'removed.json',dict(schema_version=1,exact_nonpackage_files_removed=True,
        index_sha256=sha256(retained/'index.json'),archive_sha256=sha256(archive),removed_files=len(files),
        scope='Exact metadata/log duplicates removed only after complete member byte readback. Package payloads unchanged. No target runtime files removed.'))
    print('Retained exact npm metadata/log bytes:',total,'expanded ->',archive.stat().st_size,'compressed; package payloads unchanged.')


if __name__=='__main__':main()
