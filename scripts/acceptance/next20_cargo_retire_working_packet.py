"""Compare every original successful Linux payload before retiring its encoding."""
import json
from next20_check import RAW
from next20_native_packet_reader import read_packet
from next20_cargo_solid_reference import unpack,restore
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def main():
    project=RAW/'cargo-generate';source=RAW/'tmp/direct-native-zip/cargo-generate/retained-native-v12';current=project/'retained-native-v13'
    old_index,old=read_packet('cargo-generate',12,stage=True);index,files=read_packet('cargo-generate',13)
    disposition=index['solid_runtime_disposition'];frame=disposition['superseded_generated_transport_frame']['logical_path']
    if any(files.get(n)!=data for n,data in old.items() if n!=frame):raise ValueError('original substantive successful Linux evidence differs')
    if restore(files,disposition)!=unpack(old[frame],json.loads(old[disposition['original_solid_index']])):raise ValueError('actual compiled executable corpus differs')
    inventory={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in source.iterdir() if p.is_file()}
    if len(inventory)!=len(list(source.iterdir())) or len(inventory)>12:raise ValueError('unknown working packet entries')
    for name,row in inventory.items():
        if (source/name).is_symlink() or row['bytes']>16*1024**2:raise ValueError('working packet member link/size')
    projected=measure(project)['total_bytes']+sum(r['bytes'] for n,r in inventory.items() if n!='packets.tar.xz')+65536
    if projected>64*1024**2 or (project/'retained-native-v12').exists():raise ValueError('historical index promotion scope/headroom differs')
    immutable_json(current/'working-retirement-plan.json',dict(schema_version=1,source_root=str(source),historical_destination=str(project/'retained-native-v12'),
        source_files=inventory,obsolete_generated_archive='packets.tar.xz',current_index_sha256=sha256(current/'index.json'),current_archive_sha256=sha256(current/'packets.tar.xz'),
        canonical_index_sha256=sha256(project/'retained-native-v2/index.json'),canonical_archive_sha256=sha256(project/'retained-native-v2/packets.tar.gz'),
        original_logical_records_verified=len(old),current_logical_records_verified=len(files),all_four_actual_executable_bytes_compared=True,
        projected_retained_bytes_with_margin=projected,scope='Only obsolete generated outer/solid compression wrapper bytes are retired. Every original report/input/metadata and actual executable byte independently compared. All original indices/acquisition/provider/hash receipts move into retained history and count against caps.'))
    print('Full independent comparison:',len(old),'original records and all4 actual executables; projected retained bytes with margin',projected)


if __name__=='__main__':main()
