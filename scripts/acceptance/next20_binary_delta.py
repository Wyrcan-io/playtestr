"""Lossless bounded executable deltas; the exact baseline is a required dictionary."""
import hashlib
import lzma

LIMIT=64*1024**2
COMPRESSED_LIMIT=16*1024**2


def digest(data):return hashlib.sha256(data).hexdigest()


def xor(left,right):
    return (int.from_bytes(left,'little') ^ int.from_bytes(right,'little')).to_bytes(len(left),'little')


def encode(base,target):
    if not 0<len(base)<=LIMIT or not 0<len(target)<=LIMIT:raise ValueError('executable size bound')
    encoder=lzma.LZMACompressor(format=lzma.FORMAT_XZ,preset=6)
    blocks=[]
    for offset in range(0,len(target),65536):
        block=target[offset:offset+65536]
        dictionary=base[offset:offset+len(block)].ljust(len(block),b'\0')
        blocks.append(encoder.compress(xor(block,dictionary)))
    blocks.append(encoder.flush());payload=b''.join(blocks)
    if len(payload)>COMPRESSED_LIMIT:raise ValueError('compressed executable delta bound')
    record=dict(schema_version=1,encoding='xor-zero-extended-base+xz',base_bytes=len(base),base_sha256=digest(base),
        target_bytes=len(target),target_sha256=digest(target),delta_bytes=len(payload),delta_sha256=digest(payload))
    if decode(base,payload,record)!=target:raise ValueError('actual executable roundtrip differs')
    return payload,record


def decode(base,payload,record):
    if record.get('schema_version')!=1 or record.get('encoding')!='xor-zero-extended-base+xz':raise ValueError('delta encoding')
    size=record['target_bytes']
    if not 0<size<=LIMIT or not 0<len(base)<=LIMIT or len(payload)>COMPRESSED_LIMIT:raise ValueError('delta size bound')
    if len(base)!=record['base_bytes'] or digest(base)!=record['base_sha256']:raise ValueError('required baseline dictionary missing/changed')
    if len(payload)!=record['delta_bytes'] or digest(payload)!=record['delta_sha256']:raise ValueError('delta bytes changed')
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
    try:plain=decoder.decompress(payload,max_length=size+1)
    except lzma.LZMAError as error:raise ValueError('invalid delta stream') from error
    if len(plain)!=size or not decoder.eof or decoder.unused_data:raise ValueError('partial/oversized/trailing delta stream')
    result=b''.join(xor(plain[o:o+65536],base[o:o+min(65536,size-o)].ljust(min(65536,size-o),b'\0')) for o in range(0,size,65536))
    if digest(result)!=record['target_sha256']:raise ValueError('reconstructed executable differs')
    return result
