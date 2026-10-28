"""Retain all four real Linux executables with explicit bounded dictionaries.

Every executable byte is reconstructed and hashed. Only the obsolete generated
solid-XZ transport wrapper is superseded; its original index/hash stays provenance.
"""
import hashlib
import io
import json
import lzma
import tarfile

from next20_check import RAW
from next20_lzma_dictionary import encode,decode
from next20_native_runtime_reference import binary_bundle
from next20_packet_archive import verify
from readiness_compact_native import physical_members
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def digest(data):return hashlib.sha256(data).hexdigest()


def unpack(payload,index):
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
    data=decoder.decompress(payload,max_length=128*1024**2+1)
    if len(data)>128*1024**2 or not decoder.eof or decoder.unused_data:raise ValueError('solid executable decoding bound/trailing')
    result={}
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:') as stream:
        for member in stream:
            if not member.isfile() or member.name not in index['files'] or member.name in result or not 0<member.size<=32*1024**2:raise ValueError('solid executable member coverage/type/bound')
            value=stream.extractfile(member).read(32*1024**2+1);row=index['files'][member.name]
            if len(value)!=row['bytes'] or digest(value)!=row['sha256'] or value[:5]!=b'\x7fELF\x02':raise ValueError('actual retained ELF differs')
            result[member.name]=value
    if set(result)!={'original','F01','F02','F03'}:raise ValueError('all four actual executable bytes required')
    return result


def restore(files,disposition):
    from next20_native_packet_reader import read_packet
    required=disposition['required_canonical_runtime']
    canonical_index,canonical=read_packet('cargo-generate',2)
    if (required['archive']!='cargo-generate/retained-native-v2/packets.tar.gz' or
        required['archive_sha256']!=canonical_index['archive_sha256'] or required['index_sha256']!=sha256(RAW/'cargo-generate/retained-native-v2/index.json')):raise ValueError('solid runtime required canonical dictionary differs')
    base=binary_bundle(canonical[required['logical_frame']],json.loads(canonical[required['logical_frame_index']]))['cargo-generate']
    if len(base)!=required['actual_executable_bytes'] or digest(base)!=required['actual_executable_sha256']:raise ValueError('actual canonical ELF differs')
    if disposition['old_compressed_frame_bytes_reconstructible']:raise ValueError('obsolete solid wrapper must not claim byte reconstruction')
    original_index=json.loads(files[disposition['original_solid_index']]);result={}
    if set(disposition['executables'])!={'original','F01','F02','F03'}:raise ValueError('missing real native executable')
    for name in ['original','F01','F02','F03']:
        row=disposition['executables'][name];expected=original_index['files'][name]
        expected_base='canonical-original' if name=='original' else 'current-original'
        if row['base']!=expected_base:raise ValueError('unsafe native executable dictionary graph')
        result[name]=decode(base if name=='original' else result['original'],files[row['logical_payload']],row['codec'])
        if len(result[name])!=expected['bytes'] or digest(result[name])!=expected['sha256']:raise ValueError('restored actual original/fault ELF differs')
    return result


def main():
    from next20_native_packet_reader import read_packet
    project=RAW/'cargo-generate';source=RAW/'tmp/direct-native-zip/cargo-generate/retained-native-v12'
    old_index,old=read_packet('cargo-generate',12,stage=True)
    canonical_index,canonical=read_packet('cargo-generate',2)
    frame=next(n for n in old if n.endswith('/native-solid-variants/linux/executables.tar.xz'))
    solid_index=frame.removesuffix('executables.tar.xz')+'index.json'
    actual=unpack(old[frame],json.loads(old[solid_index]))
    canonical_frame=next(n for n in canonical if n.endswith('/native-preflight/linux/compiled-binary.tar.xz'))
    canonical_frame_index=canonical_frame.removesuffix('.tar.xz')+'-index.json'
    base=binary_bundle(canonical[canonical_frame],json.loads(canonical[canonical_frame_index]))['cargo-generate']
    required=dict(archive='cargo-generate/retained-native-v2/packets.tar.gz',archive_sha256=canonical_index['archive_sha256'],
        index_sha256=sha256(project/'retained-native-v2/index.json'),logical_frame=canonical_frame,logical_frame_index=canonical_frame_index,
        actual_executable_bytes=len(base),actual_executable_sha256=digest(base),actual_executable_member='cargo-generate')
    additions={};executables={};prefix=frame.removesuffix('native-solid-variants/linux/executables.tar.xz')+'runtime-representation/linux/'
    for name in ['original','F01','F02','F03']:
        payload,codec=encode(base if name=='original' else actual['original'],actual[name]);logical=prefix+name+'.lzma2.dict'
        additions[logical]=payload;executables[name]=dict(base='canonical-original' if name=='original' else 'current-original',logical_payload=logical,codec=codec)
        print('Exact executable dictionary representation:',name,len(payload),'bytes; full actual roundtrip verified',flush=True)
    disposition=dict(schema_version=1,required_canonical_runtime=required,original_solid_index=solid_index,executables=executables,
        superseded_generated_transport_frame=dict(logical_path=frame,bytes=len(old[frame]),sha256=digest(old[frame])),
        old_compressed_frame_bytes_reconstructible=False,
        scope='All four actual compiled executable bytes restored/hash-verified. Bounded graph: canonical physical packet2 -> current original -> each fault. No external dictionary chains or unlike-byte alias. Original solid wrapper checksum is acquisition provenance only.')
    files={n:dict(r) for n,r in old_index['files'].items() if n!=frame}
    if any(r.get('member')==frame for r in files.values()):raise ValueError('unexpected aliased generated solid wrapper')
    for name,data in additions.items():files[name]=dict(bytes=len(data),sha256=digest(data))
    if restore({**old,**additions},disposition)!=actual:raise ValueError('independent complete executable reconstruction differs')
    destination=project/'retained-native-v13'
    if destination.exists():raise ValueError('preserve previous retained representation')
    # Reserve both immutable original index/provenance and the new exact index.
    reserve=2*(source/'index.json').stat().st_size+512*1024
    headroom=64*1024**2-measure(project)['total_bytes']-reserve
    if headroom<=0:raise ValueError('insufficient complete representation headroom')
    destination.mkdir();archive=destination/'packets.tar.xz'
    class Bounded:
        def __init__(self,stream):self.stream=stream
        def write(self,value):
            if self.stream.tell()+len(value)>headroom:raise ValueError('solid representation exceeds measured retained headroom')
            return self.stream.write(value)
        def flush(self):return self.stream.flush()
    physical=physical_members(files)
    with archive.open('xb') as output,lzma.LZMAFile(Bounded(output),'w',preset=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as stream:
        for name,row in sorted(physical.items()):
            data=additions[name] if name in additions else old[name]
            if len(data)!=row['bytes'] or digest(data)!=row['sha256']:raise ValueError('unchanged actual logical evidence differs')
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;stream.addfile(info,io.BytesIO(data))
    verify(archive,files)
    index=dict(old_index,schema_version=4,generation=13,compression='tar.xz',files=files,expanded_bytes=sum(r['bytes'] for r in files.values()),
        unique_payloads=len(physical),archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
        solid_runtime_disposition=disposition,prior_index_sha256=sha256(source/'index.json'),prior_archive_sha256=old_index['archive_sha256'])
    immutable_json(destination/'index.json',index)
    selected=next(n for n in files if n.endswith('N01.report.json'))
    with tarfile.open(archive,'r:xz') as stream:
        restored={n:stream.extractfile(r.get('member',n)).read(16*1024**2+1) for n,r in files.items()}
    if any(len(restored[n])!=r['bytes'] or digest(restored[n])!=r['sha256'] for n,r in files.items()) or restore(restored,disposition)!=actual:raise ValueError('retained complete byte restoration differs')
    (destination/'selected-restore.bin').write_bytes(restored[selected])
    immutable_json(destination/'verified.json',dict(schema_version=1,index_sha256=sha256(destination/'index.json'),archive_sha256=sha256(archive),
        members_verified=len(files),physical_members_verified=len(physical),selected_restore_verified=1,selected_restore_logical_path=selected,
        all_four_actual_executable_payloads_restored=True,obsolete_transport_wrapper_reconstructed=False))
    for name in ['provider.json','acquisition.json']:
        with (destination/name).open('xb') as stream:stream.write((source/name).read_bytes())
    immutable_json(destination/'supersession-prepared.json',dict(schema_version=1,source_root=str(source),source_index_sha256=sha256(source/'index.json'),
        source_archive_sha256=old_index['archive_sha256'],required_replacement_index_sha256=sha256(destination/'index.json'),
        required_replacement_archive_sha256=sha256(archive),all_actual_report_input_metadata_and_four_executable_bytes_verified=True,
        source_working_archive_removal_pending=True,original_wrapper_encoding_reconstructible=False))
    print('Complete Linux final actual payload representation verified:',archive.stat().st_size,'retained archive bytes;',len(files),'logical records; source working packet remains until checked retirement')


if __name__=='__main__':main()
