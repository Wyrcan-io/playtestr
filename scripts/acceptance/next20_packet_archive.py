"""Read explicitly recorded native gzip/XZ encodings with bounded verification."""
import hashlib
import io
import lzma
import tarfile

from readiness_compact_native import physical_members, verify as verify_gzip


def archive_path(root,index):
    compression=index.get('compression','tar.gz')
    if compression not in {'tar.gz','tar.xz'}:raise ValueError('Unreviewed native packet compression')
    return root/('packets.'+compression)


def tar_mode(index,stream=False):
    compression=index.get('compression','tar.gz')
    if compression not in {'tar.gz','tar.xz'}:raise ValueError('Unreviewed native packet compression')
    return ('r|' if stream else 'r:')+('xz' if compression=='tar.xz' else 'gz')


def verify(archive,files):
    if archive.name=='packets.tar.gz':return verify_gzip(archive,files)
    if archive.name!='packets.tar.xz' or archive.stat().st_size>24*1024**2:raise ValueError('Native XZ compressed bound/encoding')
    members=physical_members(files)
    if len(files)>40000 or sum(row['bytes'] for row in files.values())>128*1024**2 or any(row['bytes']>16*1024**2 for row in files.values()):
        raise ValueError('Native XZ inventory bound')
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
    expanded=decoder.decompress(archive.read_bytes(),max_length=256*1024**2+1)
    if len(expanded)>256*1024**2 or not decoder.eof or decoder.unused_data:raise ValueError('Native XZ frame/stream bound')
    seen=set()
    with tarfile.open(fileobj=io.BytesIO(expanded),mode='r:') as bundle:
        for member in bundle:
            if member.name not in members or member.name in seen or not member.isfile() or member.size!=members[member.name]['bytes']:
                raise ValueError('Native XZ archive coverage/type/size differs')
            value=bundle.extractfile(member).read(16*1024**2+1)
            if len(value)!=member.size or hashlib.sha256(value).hexdigest()!=members[member.name]['sha256']:
                raise ValueError('Native XZ payload hash differs')
            seen.add(member.name)
    if seen!=set(members):raise ValueError('Native XZ archive omitted member')
