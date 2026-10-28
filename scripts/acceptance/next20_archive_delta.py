"""Lossless COPY/INSERT archive representation with one required dictionary."""
import hashlib
import lzma
import struct

LIMIT=32*1024**2
BASE_LIMIT=32*1024**2


def digest(data):return hashlib.sha256(data).hexdigest()


def encode(base,target):
    if not 0<len(base)<=BASE_LIMIT or not 0<len(target)<=LIMIT:raise ValueError('archive representation byte bound')
    anchors={}
    for offset in range(0,max(0,len(base)-31),256):anchors.setdefault(base[offset:offset+32],offset)
    operations=bytearray();position=0;literal=0;copies=0
    def insert(data):
        if data:operations.extend(b'I'+struct.pack('<I',len(data))+data)
    while position+32<=len(target):
        offset=anchors.get(target[position:position+32])
        if offset is None:position+=1;continue
        size=32;maximum=min(len(base)-offset,len(target)-position)
        while size+4096<=maximum and base[offset+size:offset+size+4096]==target[position+size:position+size+4096]:size+=4096
        while size<maximum and base[offset+size]==target[position+size]:size+=1
        insert(target[literal:position]);operations.extend(b'C'+struct.pack('<II',offset,size));copies+=1
        position+=size;literal=position
    insert(target[literal:]);operations.extend(b'E')
    if len(operations)>2*LIMIT:raise ValueError('archive representation operation bound')
    payload=lzma.compress(bytes(operations),format=lzma.FORMAT_XZ,preset=6)
    if len(payload)>LIMIT:raise ValueError('archive representation compressed bound')
    record=dict(schema_version=1,encoding='copy-insert-v1+xz',base_bytes=len(base),base_sha256=digest(base),
        target_bytes=len(target),target_sha256=digest(target),delta_bytes=len(payload),delta_sha256=digest(payload),copy_operations=copies)
    if decode(base,payload,record)!=target:raise ValueError('archive representation full byte roundtrip differs')
    return payload,record


def decode(base,payload,record):
    if record.get('schema_version')!=1 or record.get('encoding')!='copy-insert-v1+xz':raise ValueError('unrecognized archive representation')
    if not 0<len(base)<=BASE_LIMIT or not 0<record['target_bytes']<=LIMIT or len(payload)>LIMIT:raise ValueError('archive representation bound')
    if len(base)!=record['base_bytes'] or digest(base)!=record['base_sha256']:raise ValueError('required archive dictionary missing/changed')
    if len(payload)!=record['delta_bytes'] or digest(payload)!=record['delta_sha256']:raise ValueError('archive representation payload changed')
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
    try:operations=decoder.decompress(payload,max_length=2*LIMIT+1)
    except lzma.LZMAError as error:raise ValueError('invalid archive representation stream') from error
    if len(operations)>2*LIMIT or not decoder.eof or decoder.unused_data:raise ValueError('truncated/trailing/oversized archive representation stream')
    result=bytearray();position=0;ended=False;copies=0
    while position<len(operations):
        action=operations[position:position+1];position+=1
        if action==b'E':ended=True;break
        if action==b'C':
            if position+8>len(operations):raise ValueError('partial archive copy instruction')
            offset,size=struct.unpack_from('<II',operations,position);position+=8;copies+=1
            if not size or offset+size>len(base):raise ValueError('archive copy escaped required dictionary')
            block=base[offset:offset+size]
        elif action==b'I':
            if position+4>len(operations):raise ValueError('partial archive insertion instruction')
            size=struct.unpack_from('<I',operations,position)[0];position+=4
            if not size or position+size>len(operations):raise ValueError('partial/empty archive insertion')
            block=operations[position:position+size];position+=size
        else:raise ValueError('unknown archive representation instruction')
        if len(result)+len(block)>record['target_bytes']:raise ValueError('archive reconstruction exceeded target bound')
        result.extend(block)
    if not ended or position!=len(operations) or len(result)!=record['target_bytes'] or copies!=record['copy_operations'] or digest(result)!=record['target_sha256']:raise ValueError('archive reconstruction coverage/hash differs')
    return bytes(result)
