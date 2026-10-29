"""Stage exact large-wheel native evidence before removing its expanded duplicate."""
import gzip
import json
import os
import tarfile

from next20_check import RAW,DOC
from next20_native_packet_reader import read_packet
from readiness_compact_native import inventory,physical_members,verify
from readiness_evidence import immutable_json,sha256


def main():
    project='hatch';run='40925331521';generation=1
    proof=DOC/project/'linux-development-readback.json'
    if json.loads(proof.read_text())['run']!=run:raise ValueError('independent native development readback required')
    files,total=inventory(RAW,[run],32*1024**2);canonical={}
    for name,row in sorted(files.items()):
        member=canonical.setdefault((row['bytes'],row['sha256']),name)
        if member!=name:row['member']=member
    physical=physical_members(files)
    output=RAW/'tmp/direct-native-zip/hatch/retained-native-v1'
    for ancestor in [RAW,RAW/'tmp',RAW/'tmp/direct-native-zip',output.parent]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked staged retention ancestor')
    output.mkdir(parents=True,exist_ok=False);archive=output/'packets.tar.gz';limit=48*1024**2
    with archive.open('xb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as target:
                for name,row in physical.items():
                    source=RAW/name
                    if sha256(source)!=row['sha256']:raise ValueError('expanded native source changed')
                    member=tarfile.TarInfo(name);member.size=row['bytes'];member.mode=0o644
                    with source.open('rb') as stream:target.addfile(member,stream)
                    if raw.tell()>limit:raise ValueError('explicit native archive working bound')
        raw.flush();os.fsync(raw.fileno())
    if archive.stat().st_size>limit:raise ValueError('explicit retained native archive bound')
    verify(archive,files)
    selected=next(n for n in files if n.endswith('/N01.report.json'))
    with tarfile.open(archive,'r:gz') as stream:body=stream.extractfile(files[selected].get('member',selected)).read(4*1024**2+1)
    (output/'selected-restore.bin').write_bytes(body)
    if sha256(output/'selected-restore.bin')!=files[selected]['sha256'] or json.loads(body)['results'][0]['status']!='passed':raise ValueError('selected actual development report restore differs')
    immutable_json(output/'index.json',dict(schema_version=2,project=project,generation=generation,runs=[run],files=files,
        expanded_bytes=total,unique_payloads=len(physical),archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
        max_file_bytes=32*1024**2,max_archive_bytes=limit,selected_restore=[selected],selected_restore_path='selected-restore.bin',
        independent_readback_sha256=sha256(proof),temporary_staging=True,
        scope='Every native logical path/hash retained with exact in-archive aliases. Archive temporarily staged under declared shared raw working space; promote only after full original-byte readback and checked expanded removal. Global raw limits still apply; project retained limit remains64MiB.'))
    immutable_json(output/'verified.json',dict(index_sha256=sha256(output/'index.json'),archive_sha256=sha256(archive),members_verified=len(files),
        physical_members_verified=len(physical),selected_restore_verified=1,expanded_removal_performed=False))
    index,restored=read_packet(project,generation,stage=True)
    if set(restored)!=set(files) or any((RAW/name).read_bytes()!=body for name,body in restored.items()):raise ValueError('full staged actual byte readback differs')
    immutable_json(output/'complete-readback.json',dict(schema_version=1,index_sha256=sha256(output/'index.json'),members_compared_byte_exact=len(restored),
        expanded_bytes_compared=total,selected_actual_report=selected,archive_sha256=sha256(archive),project_retained_cap_unchanged=True))
    print('Staged and fully byte-verified',len(files),'native logical files;',total,'expanded ->',archive.stat().st_size,'gzip bytes; removal/promotion still pending.')


if __name__=='__main__':main()
