"""Retain the original failed Windows harness artifact without treating it as a pass."""
import gzip
import hashlib
import io
import json
import stat
import tarfile
import zipfile

from next20_check import DOC,RAW
from next20_native_packet_reader import read_packet
from next20_native_zip_packet import download,payload_name
from readiness_compact_native import physical_members,verify
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    run='40929251569';revision='0a4cf8868ac120bd628ac450a880d986a6eea317';artifact='next20-harness-windows-2025';artifact_id='12921404315';generation=109
    expected='f800bf1dbddfbcc27839a8c8532ea1fd942b8011018ec240815f223b54dcbb2c';prefix='native/'+run+'/'+artifact+'/'
    destination=RAW/'harness'/('retained-native-v'+str(generation));require(not destination.exists(),'preserve original failed-harness retention attempt')
    provider=json.loads(download(['gh','api','repos/Wyrcan-io/playtestr/actions/runs/'+run],1024**2))
    require(provider['head_sha']==revision and provider['status']=='completed' and provider['conclusion']=='failure' and provider['run_attempt']==1,'wrong original failed provider run')
    metadata=json.loads(download(['gh','api','repos/Wyrcan-io/playtestr/actions/artifacts/'+artifact_id],1024**2))
    require(metadata['name']==artifact and not metadata['expired'] and metadata['size_in_bytes']<=32*1024**2 and metadata['digest']=='sha256:'+expected,'wrong failed artifact')
    staging=RAW/'tmp'/('failed-harness-source-'+artifact_id+'.zip')
    require(not staging.exists(),'reuse retained original staging explicitly rather than redownload')
    payload=download(['gh','api','repos/Wyrcan-io/playtestr/actions/artifacts/'+artifact_id+'/zip'],32*1024**2)
    require(hashlib.sha256(payload).hexdigest()==expected and len(payload)==metadata['size_in_bytes'],'actual original ZIP differs from provider digest/length')
    staging.write_bytes(payload);bodies={};files={};canonical={};folded=set();total=0
    with zipfile.ZipFile(io.BytesIO(payload)) as source:
        require(len(source.infolist())<=20000,'failed artifact entry bound')
        for entry in source.infolist():
            name=payload_name(entry.filename.rstrip('/') if entry.is_dir() else entry.filename)
            require(not entry.flag_bits&1 and not stat.S_ISLNK(entry.external_attr>>16),'unsafe failed artifact entry')
            if entry.is_dir():continue
            logical=prefix+name;require(logical.casefold() not in folded and entry.file_size<=32*1024**2,'failed artifact duplicate/file bound');folded.add(logical.casefold());total+=entry.file_size
            require(total<=128*1024**2 and len(files)<10000,'failed artifact logical bound')
            body=source.read(entry);require(len(body)==entry.file_size,'failed artifact member length')
            row=dict(bytes=len(body),sha256=hashlib.sha256(body).hexdigest());member=canonical.setdefault((len(body),row['sha256']),logical)
            if member!=logical:row['member']=member
            files[logical]=row;bodies[logical]=body
    large=[dict(path=n,bytes=len(b)) for n,b in bodies.items() if len(b)>16*1024**2]
    print('Original failed artifact:',len(files),'logical files;',total,'bytes; large original payloads:',large,flush=True)
    console_name=prefix+'core/2c4300b2055a494b86b8fdad25737d75/console.log';console=bodies[console_name].decode('utf-8')
    finish=json.loads(bodies[prefix+'events/2c4300b2055a494b86b8fdad25737d75-finished.json'])
    require(finish['category']=='harness_timeout' and finish['console_sha256']==hashlib.sha256(bodies[console_name]).hexdigest(),'original suite timeout evidence differs')
    require('test_explicit_large_packet_and_checked_staged_removal_promotion' in console and 'Ran 54 tests' not in console,'original incomplete staged-control signature differs')
    size=sum(p.stat().st_size for p in (RAW/'harness').rglob('*') if p.is_file());limit=min(24*1024**2,64*1024**2-size-1024**2)
    require(limit>0,'no retained harness headroom');destination.mkdir();archive=destination/'packets.tar.gz'
    with archive.open('xb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as target:
            for name,row in physical_members(files).items():
                member=tarfile.TarInfo(name);member.size=row['bytes'];member.mode=0o644;target.addfile(member,io.BytesIO(bodies[name]))
                require(raw.tell()<=limit,'failed retained archive headroom bound')
    require(archive.stat().st_size<=limit,'failed retained archive compressed bound');verify(archive,files)
    immutable_json(destination/'index.json',dict(schema_version=2,project='harness',generation=generation,runs=[run],files=files,expanded_bytes=total,unique_payloads=len(physical_members(files)),
        archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,max_file_bytes=32*1024**2,max_archive_bytes=24*1024**2,
        provider_zip_sha256=expected,provider_zip_bytes=len(payload),selected_restore=[console_name],scope='Complete original failed provider payload,including large synthetic scratch and partial lifecycle evidence. No passing harness/application/cell/admission credit; original ZIP wrapper hash retained,all logical payload bytes preserved.'))
    immutable_json(destination/'verified.json',dict(schema_version=1,index_sha256=sha256(destination/'index.json'),archive_sha256=sha256(archive),members_verified=len(files),selected_restore_verified=1,expanded_payload_created=False))
    _,restored=read_packet('harness',generation);require(restored==bodies,'full original failed ZIP logical-byte readback differs')
    (destination/'selected-restore.bin').write_bytes(bodies[console_name])
    immutable_json(destination/'complete-readback.json',dict(schema_version=1,members_compared_byte_exact=len(bodies),expanded_bytes_compared=total,provider_zip_sha256=expected,index_sha256=sha256(destination/'index.json'),selected_actual_console_sha256=sha256(destination/'selected-restore.bin')))
    immutable_json(DOC/('harness-'+run+'-windows-2025-failure.json'),dict(schema_version=1,run=run,host='windows-2025',tooling_revision=revision,provider_conclusion='failure',
        actual_suite_category=finish['category'],actual_suite_seconds=finish['seconds'],last_named_control='test_explicit_large_packet_and_checked_staged_removal_promotion',
        actual_console_sha256=hashlib.sha256(bodies[console_name]).hexdigest(),retained_generation=generation,index_sha256=sha256(destination/'index.json'),archive_sha256=sha256(archive),
        full_original_payload_files=len(files),large_original_payloads=large,all_actual_payload_bytes_verified=True,root_cause_resolved=False,tests_discovered=None,named_controls_passed=None,new_project_credit=0,
        scope='Original 240-second suite timeout retained in full. Last printed test does not establish root cause. Later fresh successful runs do not turn this failed/incomplete original into a pass. No source/runtime/application qualification credit.'))
    require(staging.resolve(strict=True)==(RAW/'tmp'/staging.name).resolve() and not staging.is_symlink() and sha256(staging)==expected,'unsafe original ZIP staging removal')
    staging.unlink()
    print('Retained and fully read back original failed Windows packet; no disk expansion,source ZIP duplicate removed after exact payload verification. Original failure remains unresolved.')


if __name__=='__main__':main()
