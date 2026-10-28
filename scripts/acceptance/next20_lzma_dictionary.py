"""Bounded raw LZMA2 using an explicit, hash-required executable dictionary.

Uses the already installed read-only liblzma C API. Raw preset-dictionary data
is deliberately not labelled .xz; standard container decoding is insufficient.
"""
import ctypes as c
import hashlib
from pathlib import Path
import sys

LIMIT=32*1024**2


def digest(data):return hashlib.sha256(data).hexdigest()


class Options(c.Structure):
    _fields_=[('dict_size',c.c_uint32),('preset_dict',c.c_void_p),('preset_dict_size',c.c_uint32),
        ('lc',c.c_uint32),('lp',c.c_uint32),('pb',c.c_uint32),('mode',c.c_int),('nice_len',c.c_uint32),
        ('mf',c.c_int),('depth',c.c_uint32),('ext_flags',c.c_uint32),('ext_size_low',c.c_uint32),('ext_size_high',c.c_uint32),
        *[('reserved_int'+str(i),c.c_uint32) for i in range(4,9)],
        *[('reserved_enum'+str(i),c.c_int) for i in range(1,5)],('reserved_ptr1',c.c_void_p),('reserved_ptr2',c.c_void_p)]


class Filter(c.Structure):_fields_=[('id',c.c_uint64),('options',c.c_void_p)]


def library():
    choices=[Path(sys.prefix)/'Library/bin/liblzma.dll',Path('C:/Program Files/Git/mingw64/bin/liblzma-5.dll'),
        Path('/usr/lib/x86_64-linux-gnu/liblzma.so.5'),Path('/usr/lib/aarch64-linux-gnu/liblzma.so.5'),Path('/usr/lib/liblzma.5.dylib')]
    loaded=None;path=None
    for candidate in choices:
        if candidate.is_file() or str(candidate)=='/usr/lib/liblzma.5.dylib':
            try:loaded=c.CDLL(str(candidate));path=candidate;break
            except OSError:continue
    if loaded is None:raise ValueError('read-only installed liblzma prerequisite unavailable; no global installation')
    if c.sizeof(c.c_void_p)!=8 or c.sizeof(Options)!=112 or c.sizeof(Filter)!=16:raise ValueError('unsupported liblzma options ABI')
    loaded.lzma_version_string.restype=c.c_char_p;version=loaded.lzma_version_string().decode('ascii')
    if not version.startswith('5.'):raise ValueError('unsupported liblzma ABI version')
    loaded.lzma_lzma_preset.argtypes=[c.POINTER(Options),c.c_uint32];loaded.lzma_lzma_preset.restype=c.c_uint8
    loaded.lzma_raw_encoder_memusage.argtypes=[c.POINTER(Filter)];loaded.lzma_raw_encoder_memusage.restype=c.c_uint64
    loaded.lzma_raw_decoder_memusage.argtypes=[c.POINTER(Filter)];loaded.lzma_raw_decoder_memusage.restype=c.c_uint64
    loaded.lzma_raw_buffer_encode.argtypes=[c.POINTER(Filter),c.c_void_p,c.c_void_p,c.c_size_t,c.c_void_p,c.POINTER(c.c_size_t),c.c_size_t];loaded.lzma_raw_buffer_encode.restype=c.c_int
    loaded.lzma_raw_buffer_decode.argtypes=[c.POINTER(Filter),c.c_void_p,c.c_void_p,c.POINTER(c.c_size_t),c.c_size_t,c.c_void_p,c.POINTER(c.c_size_t),c.c_size_t];loaded.lzma_raw_buffer_decode.restype=c.c_int
    return loaded,dict(path=str(path),version=version,sha256=digest(path.read_bytes()) if path.is_file() else None)


def filters(lib,base):
    dictionary=c.create_string_buffer(base);options=Options()
    if lib.lzma_lzma_preset(c.byref(options),6):raise ValueError('liblzma preset unavailable')
    options.dict_size=LIMIT;options.preset_dict=c.cast(dictionary,c.c_void_p);options.preset_dict_size=len(base)
    chain=(Filter*2)(Filter(0x21,c.addressof(options)),Filter(2**64-1,None))
    return dictionary,options,chain


def encode(base,target):
    if not 0<len(base)<=LIMIT or not 0<len(target)<=LIMIT:raise ValueError('raw dictionary input bound')
    lib,identity=library();dictionary,options,chain=filters(lib,base)
    memory=lib.lzma_raw_encoder_memusage(chain)
    if memory>512*1024**2:raise ValueError('raw dictionary encoder memory bound')
    source=c.create_string_buffer(target);output=c.create_string_buffer(min(LIMIT+1024**2,len(target)+1024**2));position=c.c_size_t()
    status=lib.lzma_raw_buffer_encode(chain,None,source,len(target),output,c.byref(position),len(output))
    if status!=0 or not 0<position.value<=LIMIT:raise ValueError('raw dictionary encoder failed/bound: '+str(status))
    payload=output.raw[:position.value]
    record=dict(schema_version=1,encoding='raw-lzma2-preset-dictionary-v1',dictionary_bytes=LIMIT,
        base_bytes=len(base),base_sha256=digest(base),target_bytes=len(target),target_sha256=digest(target),
        delta_bytes=len(payload),delta_sha256=digest(payload),encoder_memory_bytes=memory,encoder_library=identity)
    if decode(base,payload,record)!=target:raise ValueError('actual raw dictionary full byte roundtrip differs')
    return payload,record


def decode(base,payload,record):
    if record.get('schema_version')!=1 or record.get('encoding')!='raw-lzma2-preset-dictionary-v1' or record['dictionary_bytes']!=LIMIT:raise ValueError('unknown raw dictionary format')
    if not 0<len(base)<=LIMIT or not 0<record['target_bytes']<=LIMIT or len(payload)>LIMIT:raise ValueError('raw dictionary decode size bound')
    if len(base)!=record['base_bytes'] or digest(base)!=record['base_sha256']:raise ValueError('required native dictionary missing/changed')
    if len(payload)!=record['delta_bytes'] or digest(payload)!=record['delta_sha256']:raise ValueError('raw dictionary encoded bytes changed')
    lib,_=library();dictionary,options,chain=filters(lib,base)
    if lib.lzma_raw_decoder_memusage(chain)>64*1024**2:raise ValueError('raw dictionary decoder memory bound')
    source=c.create_string_buffer(payload);output=c.create_string_buffer(record['target_bytes']);input_position=c.c_size_t();output_position=c.c_size_t()
    status=lib.lzma_raw_buffer_decode(chain,None,source,c.byref(input_position),len(payload),output,c.byref(output_position),len(output))
    if status!=0 or input_position.value!=len(payload) or output_position.value!=record['target_bytes']:raise ValueError('raw dictionary partial/trailing/corrupt stream: '+str(status))
    result=output.raw
    if digest(result)!=record['target_sha256']:raise ValueError('actual decoded native executable bytes differ')
    return result


def self_test():
    import copy
    import random
    base=random.Random(12).randbytes(65536);target=b'prefix'+base[:32000]+b'changed'+base[32008:]+b'tail'
    payload,record=encode(base,target)
    if decode(base,payload,record)!=target:raise ValueError('raw dictionary positive control failed')
    rejected=0
    for dictionary,data in [(b'wrong',payload),(base,payload[:-1]),(base,payload+b'trailing')]:
        changed=copy.deepcopy(record);changed.update(delta_bytes=len(data),delta_sha256=digest(data))
        try:decode(dictionary,data,changed)
        except ValueError:rejected+=1
        else:raise ValueError('raw dictionary corruption was accepted')
    changed=copy.deepcopy(record);changed['target_sha256']='0'*64
    try:decode(base,payload,changed)
    except ValueError:rejected+=1
    else:raise ValueError('raw dictionary false target accepted')
    print('Actual installed liblzma raw-dictionary roundtrip and',rejected,'missing/truncated/trailing/wrong-target controls passed; no product qualification credit')


if __name__=='__main__':self_test()
