"""Fetch one locked Unix-only dependency for build-hook review; execute none."""
import hashlib
import io
import tarfile
import tomllib
import urllib.request

from readiness_evidence import RAW,immutable_json,sha256


def main():
    source=RAW/'active/edit/src'
    package=next(p for p in tomllib.loads((source/'Cargo.lock').read_text())['package'] if p['name']=='libc')
    name='libc-'+package['version'];root=RAW/'edit/unix-dependency-review';root.mkdir(exist_ok=False)
    with urllib.request.urlopen('https://static.crates.io/crates/libc/'+name+'.crate',timeout=30) as response:
        data=response.read(2*1024**2+1)
    if len(data)>2*1024**2 or hashlib.sha256(data).hexdigest()!=package['checksum']:
        raise RuntimeError('locked libc archive checksum/size mismatch')
    archive=root/(name+'.crate');archive.write_bytes(data)
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as stream:
        hooks={}
        for relative in ['build.rs','Cargo.toml']:
            member=stream.getmember(name+'/'+relative)
            if not member.isfile() or member.size>64*1024:raise RuntimeError('dependency review input bounds')
            value=stream.extractfile(member).read(member.size+1)
            if len(value)!=member.size:raise RuntimeError('truncated dependency review input')
            (root/relative).write_bytes(value);hooks[relative]=hashlib.sha256(value).hexdigest()
    immutable_json(root/'identity.json',dict(package=name,archive_sha256=sha256(archive),review_inputs=hooks,
        execution=False,lock_sha256=sha256(source/'Cargo.lock')))
    print((root/'build.rs').read_text(encoding='utf-8'))


if __name__=='__main__':main()
