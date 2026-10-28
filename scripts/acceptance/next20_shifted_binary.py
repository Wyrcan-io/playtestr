"""Bounded chunk realignment plus XOR for exact relocated native binaries."""
import hashlib
import lzma
import struct

LIMIT=32*1024**2
CHUNK=4096


def digest(data):return hashlib.sha256(data).hexdigest()


def xor(left,right):return (int.from_bytes(left,'little')^int.from_bytes(right,'little')).to_bytes(len(left),'little')


def encode(base,target):
    if not 0<len(base)<=LIMIT or not 0<len(target)<=LIMIT:raise ValueError('native realignment byte bound')
    anchors={}
    for offset in range(0,max(0,len(base)-15),16):anchors.setdefault(base[offset:offset+16],offset)
    encoder=lzma.LZMACompressor(format=lzma.FORMAT_XZ,preset=6);blocks=[];predicted=0;chunks=0
    for position in range(0,len(target),CHUNK):
        block=target[position:position+CHUNK];votes={}
        for sample in range(0,max(0,len(block)-15),127):
            offset=anchors.get(block[sample:sample+16])
            if offset is not None and offset>=sample:votes[offset-sample]=votes.get(offset-sample,0)+1
        candidates={offset for offset in [predicted,position,*sorted(votes,key=votes.get,reverse=True)[:8]] if 0<=offset<len(base)}
        if not candidates:candidates={0}
        best=None;score=-1;difference=None
        for offset in sorted(candidates):
            delta=xor(block,base[offset:offset+len(block)].ljust(len(block),b'\0'));matching=delta.count(b'\0')
            if matching>score:best=offset;score=matching;difference=delta
        blocks.append(encoder.compress(struct.pack('<I',best)+difference));predicted=best+CHUNK;chunks+=1
    blocks.append(encoder.flush());payload=b''.join(blocks)
    if len(payload)>LIMIT:raise ValueError('native realignment compressed bound')
    record=dict(schema_version=1,encoding='chunk-realignment-xor-v1+xz',chunk_bytes=CHUNK,chunks=chunks,
        base_bytes=len(base),base_sha256=digest(base),target_bytes=len(target),target_sha256=digest(target),delta_bytes=len(payload),delta_sha256=digest(payload))
    if decode(base,payload,record)!=target:raise ValueError('actual relocated binary full byte roundtrip differs')
    return payload,record


def decode(base,payload,record):
    if record.get('schema_version')!=1 or record.get('encoding')!='chunk-realignment-xor-v1+xz' or record['chunk_bytes']!=CHUNK:raise ValueError('unknown native realignment encoding')
    size=record['target_bytes'];chunks=(size+CHUNK-1)//CHUNK
    if not 0<len(base)<=LIMIT or not 0<size<=LIMIT or len(payload)>LIMIT or chunks!=record['chunks']:raise ValueError('native realignment bound')
    if len(base)!=record['base_bytes'] or digest(base)!=record['base_sha256']:raise ValueError('required native dictionary missing/changed')
    if len(payload)!=record['delta_bytes'] or digest(payload)!=record['delta_sha256']:raise ValueError('native realignment encoded bytes changed')
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2);expected=size+4*chunks
    try:data=decoder.decompress(payload,max_length=expected+1)
    except lzma.LZMAError as error:raise ValueError('invalid native realignment stream') from error
    if len(data)!=expected or not decoder.eof or decoder.unused_data:raise ValueError('partial/oversized/trailing native realignment stream')
    result=bytearray();position=0
    while len(result)<size:
        offset=struct.unpack_from('<I',data,position)[0];position+=4;count=min(CHUNK,size-len(result))
        if offset>=len(base):raise ValueError('native realignment reference escaped dictionary')
        result.extend(xor(data[position:position+count],base[offset:offset+count].ljust(count,b'\0')));position+=count
    if position!=len(data) or digest(result)!=record['target_sha256']:raise ValueError('actual reconstructed native binary differs')
    return bytes(result)
