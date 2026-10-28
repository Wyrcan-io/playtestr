"""Replace a redundant generated binary transport frame with exact inner references.

Original indices and acquisition hashes stay historical. Unlike compressed frames
are never aliased: actual executable bytes and current metadata are compared in
full, while the obsolete transport encoding is explicitly not reconstructed.
"""
import argparse
import hashlib
import io
import json
import lzma
import tarfile

from next20_check import RAW
from next20_lzma_dictionary import encode,decode
from next20_native_packet_reader import read_packet
from next20_packet_archive import verify
from readiness_compact_native import physical_members
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def binary_bundle(payload,index):
    if len(payload)>16*1024**2:raise ValueError('native transport frame bound')
    decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=64*1024**2)
    tar=decoder.decompress(payload,max_length=80*1024**2+1)
    if len(tar)>80*1024**2 or not decoder.eof or decoder.unused_data:raise ValueError('native transport frame decoding bound')
    files={}
    with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as stream:
        for member in stream:
            if not member.isfile() or member.name in files or member.name not in index['files'] or member.size>64*1024**2:raise ValueError('native binary bundle member differs')
            data=stream.extractfile(member).read(64*1024**2+1)
            if dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())!=index['files'][member.name]:raise ValueError('actual bundled executable/metadata bytes differ')
            files[member.name]=data
    if set(files)!=set(index['files']):raise ValueError('native binary bundle incomplete')
    return files


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--source-generation',type=int,required=True)
    parser.add_argument('--generation',type=int,required=True);parser.add_argument('--canonical-generation',type=int,required=True);parser.add_argument('--stage',action='store_true');args=parser.parse_args()
    old_index,old=read_packet(args.project,args.source_generation);canonical_index,canonical=read_packet(args.project,args.canonical_generation)
    project=RAW/args.project;source=project/('retained-native-v'+str(args.source_generation));canonical_root=project/('retained-native-v'+str(args.canonical_generation))
    final_destination=project/('retained-native-v'+str(args.generation))
    destination=RAW/'tmp/native-runtime-reference'/(args.project+'-v'+str(args.generation)) if args.stage else final_destination
    if final_destination.exists():raise ValueError('preserve existing final retained generation')
    if destination.exists():raise ValueError('preserve prior runtime-reference generation')
    frames=[n for n in old if n.endswith('/native-preflight/linux/compiled-binary.tar.xz')]
    canonical_frames=[n for n in canonical if n.endswith('/native-preflight/linux/compiled-binary.tar.xz')]
    if len(frames)!=1 or len(canonical_frames)!=1:raise ValueError('missing/ambiguous source-built native transport frames')
    frame=frames[0];canonical_frame=canonical_frames[0];frame_index=frame.removesuffix('.tar.xz')+'-index.json';canonical_frame_index=canonical_frame.removesuffix('.tar.xz')+'-index.json'
    actual_index=json.loads(old[frame_index]);reference_index=json.loads(canonical[canonical_frame_index])
    actual=binary_bundle(old[frame],actual_index);original=binary_bundle(canonical[canonical_frame],reference_index)
    for binary in [actual['cargo-generate'],original['cargo-generate']]:
        if binary[:5]!=b'\x7fELF\x02' or int.from_bytes(binary[18:20],'little')!=62:raise ValueError('actual native runtime is not Linuxamd64 ELF')
    additions={};runtime_representation=dict(kind='identical-canonical-payload')
    if actual['cargo-generate']!=original['cargo-generate']:
        delta,codec=encode(original['cargo-generate'],actual['cargo-generate'])
        delta_name=frame.split('/cargo-generate/native-preflight/')[0]+'/cargo-generate/runtime-representation/linux/cargo-generate.lzma2.dict'
        additions[delta_name]=delta;runtime_representation=dict(kind=codec['encoding'],logical_delta=delta_name,codec=codec)
        print('Different actual ELF bytes retained losslessly:',len(delta),'representation bytes; no identical-executable alias',flush=True)
    prefix=frame.split('/cargo-generate/native-preflight/')[0]+'/active/'+args.project+'/'
    metadata={}
    for name in ['build.json','version-check.json']:
        logical=prefix+name
        if old.get(logical)!=actual[name]:raise ValueError('current actual native build/version metadata not independently retained in original packet')
        metadata[name]=dict(logical_path=logical,bytes=len(actual[name]),sha256=hashlib.sha256(actual[name]).hexdigest())
    required=dict(archive=canonical_root.relative_to(RAW).as_posix()+'/packets.tar.gz',archive_sha256=canonical_index['archive_sha256'],
        index_sha256=sha256(canonical_root/'index.json'),logical_frame=canonical_frame,logical_frame_index=canonical_frame_index,
        actual_executable_member='cargo-generate',actual_executable_sha256=hashlib.sha256(original['cargo-generate']).hexdigest(),actual_executable_bytes=len(original['cargo-generate']))
    disposition=dict(schema_version=1,superseded_generated_transport_frame=dict(logical_path=frame,bytes=len(old[frame]),sha256=hashlib.sha256(old[frame]).hexdigest()),
        required_canonical_runtime=required,current_exact_metadata=metadata,all_inner_target_executable_and_metadata_bytes_preserved=True,
        current_native_executable=dict(bytes=len(actual['cargo-generate']),sha256=hashlib.sha256(actual['cargo-generate']).hexdigest(),representation=runtime_representation),
        old_compressed_frame_bytes_reconstructible=False,
        scope='Explicit native runtime payload representation, not unlike-frame or unlike-executable aliasing. Generated transport encoding is superseded; its hash remains acquisition provenance. Actual executable bytes are either identical canonical bytes or fully hash-verified raw-LZMA2 dictionary reconstruction. Current build/version metadata stays separate and unchanged. All reports/contracts/screens/first failures remain exact.')
    files={name:dict(row) for name,row in old_index['files'].items() if name!=frame}
    for name,data in additions.items():
        if name in files:raise ValueError('runtime representation logical path already exists')
        files[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if any(row.get('member')==frame for row in files.values()):raise ValueError('transport frame has undeclared logical aliases')
    physical=physical_members(files);reserve=max(512*1024,(source/'index.json').stat().st_size+65536)
    headroom=8*1024**2 if args.stage else 64*1024**2-measure(project)['total_bytes']-reserve
    if args.stage and measure(RAW)['total_bytes']+headroom+reserve>4*1024**3:raise ValueError('working compaction staging exceeds raw campaign budget')
    if headroom<=0:raise ValueError('runtime-reference representation lacks current storage headroom')
    destination.parent.mkdir(parents=True,exist_ok=True);destination.mkdir();archive=destination/'packets.tar.xz'
    if args.stage:
        immutable_json(destination/'task-owned.json',dict(schema_version=1,workspace=str(RAW.parent.parent),project=args.project,generation=args.generation,
            desired_retained_root=str(final_destination),source_retained_root=str(source),scope='Bounded temporary compaction working data, counted in raw bytes. Not retained/current qualification until checked promotion.'))
    class Bounded:
        def __init__(self,output):self.output=output
        def write(self,data):
            if self.output.tell()+len(data)>headroom:raise ValueError('runtime-reference archive exceeds measured project headroom')
            return self.output.write(data)
        def flush(self):return self.output.flush()
    with archive.open('xb') as output,lzma.LZMAFile(Bounded(output),'w',preset=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as stream:
        for name,row in sorted(physical.items()):
            data=additions[name] if name in additions else old[name]
            if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('unchanged native logical record differs')
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;stream.addfile(info,io.BytesIO(data))
    verify(archive,files)
    selected=next(n for n in files if n.endswith('/2/E02.report.json'))
    index=dict(old_index,schema_version=3,generation=args.generation,compression='tar.xz',files=files,selected_restore=[selected],
        expanded_bytes=sum(row['bytes'] for row in files.values()),archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
        unique_payloads=len(physical),runtime_frame_disposition=disposition,prior_index_sha256=sha256(source/'index.json'),
        prior_archive_sha256=old_index['archive_sha256'],
        scope='Every substantive original report/contract/input/screen and current metadata byte retained; exact native executable payload requires verified canonical dictionary. One explicitly superseded generated compression frame is acquisition provenance only. Old indices/receipts untouched; no qualification credit.')
    if len((json.dumps(index,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode())>reserve-16384:raise ValueError('runtime-reference index exceeds reserved headroom')
    immutable_json(destination/'index.json',index)
    restore=destination/'selected-restore.bin'
    with tarfile.open(archive,'r:xz') as stream:
        restore.write_bytes(stream.extractfile(files[selected].get('member',selected)).read(16*1024**2+1))
        if additions:
            retained_delta=stream.extractfile(delta_name).read(16*1024**2+1)
            if decode(original['cargo-generate'],retained_delta,codec)!=actual['cargo-generate']:raise ValueError('retained unlike executable does not restore every actual byte')
    if sha256(restore)!=files[selected]['sha256']:raise ValueError('actual original failed report restore differs')
    immutable_json(destination/'verified.json',dict(schema_version=1,index_sha256=sha256(destination/'index.json'),archive_sha256=sha256(archive),
        members_verified=len(files),physical_members_verified=len(physical),selected_restore_verified=1,selected_restore_logical_path=selected,
        expanded_payload_created=False,required_canonical_runtime_verified=True,obsolete_transport_encoding_retained=False))
    for name in ['provider.json','acquisition.json']:
        if (source/name).is_file():
            with (destination/name).open('xb') as stream:stream.write((source/name).read_bytes())
    immutable_json(source/'superseded-retention.json',dict(schema_version=1,source_index_sha256=sha256(source/'index.json'),source_archive_sha256=old_index['archive_sha256'],
        required_replacement=final_destination.relative_to(RAW).as_posix(),required_replacement_index_sha256=sha256(destination/'index.json'),
        required_replacement_archive_sha256=sha256(archive),required_canonical_runtime=required,
        transport_frame_disposition=disposition,original_archive_removal_pending=True))
    if args.stage:
        staged={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in destination.iterdir() if p.is_file()}
        projected=measure(project)['total_bytes']-(source/'packets.tar.gz').stat().st_size+sum(row['bytes'] for row in staged.values())+65536
        if projected>64*1024**2:raise ValueError('fully staged replacement would exceed retained project cap after promotion')
        immutable_json(destination/'staged-prepared.json',dict(schema_version=1,project=args.project,generation=args.generation,
            staged_root=str(destination),desired_retained_root=str(final_destination),source_retained_root=str(source),
            source_archive_sha256=old_index['archive_sha256'],source_index_sha256=sha256(source/'index.json'),
            files=staged,projected_retained_bytes_with_margin=projected,required_canonical_runtime=required,
            all_required_original_report_input_metadata_and_actual_executable_bytes_verified=True,
            obsolete_generated_transport_encoding_reconstructible=False,qualification_credit=0))
    print('Native runtime payload reference verified in full:',archive.stat().st_size,'replacement bytes;',len(files),'exact report/input/metadata records; original encoding duplicate removal pending')


if __name__=='__main__':main()
