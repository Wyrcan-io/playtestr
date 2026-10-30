"""Retain exact Go module archives and actual native executable variants."""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path
import shutil
import tarfile

from next20_check import DOC,RAW,ROOT
from next20_local_native_references import canonical,reference_for
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--canonical-native-generation',type=int);args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe Go corpus project')
    target=RAW/'active'/project;owner=json.loads((target/'task-owned.json').read_text());fetch=json.loads((target/'module-fetch.json').read_text());review=json.loads((DOC/project/'dependency-source-review-declaration.json').read_text())
    if owner['workspace']!=str(ROOT) or owner['slug']!=project or owner['pin']!=review['pin']:raise ValueError('foreign Go retention source')
    output=RAW/project/'go-module-corpus';output.mkdir(parents=True,exist_ok=False);files={};refs={};base=None;identity=None
    if args.canonical_native_generation is not None:identity,base=canonical(project,args.canonical_native_generation)
    def retain(path,name):
        path.resolve(strict=True).relative_to(target.resolve(strict=True));body=path.read_bytes();row=reference_for(name,body,base) if base is not None else None
        if row is not None:refs[name]=row;files[name]=dict(bytes=len(body),sha256=row['sha256']);return
        destination=output/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(body)
        if destination.read_bytes()!=body:raise ValueError('Go source/archive copy changed')
        files[name]=dict(bytes=len(body),sha256=sha256(destination))
    for row in fetch['modules']:
        rule=review['modules'][row['Path']+'@'+row['Version']]
        if sha256(row['Zip'])!=rule['zip_sha256']:raise ValueError('reviewed Go archive changed before retention')
        prefix=row['Path']+'/@v/'+row['Version']
        for field,suffix in [('Zip','.zip'),('GoMod','.mod'),('Info','.info')]:retain(Path(row[field]),'archives/'+prefix+suffix)
    for cache in [target/'gopath/pkg/sumdb',target/'gopath/pkg/mod/cache/download/sumdb']:
        if cache.is_dir():
            for path in sorted(cache.rglob('*')):
                if path.is_file():retain(path,'sumdb/'+path.relative_to(target/'gopath/pkg').as_posix())
    sdk=target/'toolchain/sdk.json'
    if sdk.is_file():retain(sdk,'toolchain-prerequisite.json')
    if refs:immutable_json(output/'canonical-native-references.json',dict(schema_version=1,project=project,required_canonical_packet=identity,files=refs,scope='Every referenced source ZIP compared byte-exact with actual original and mandatory standalone native packet. No reference chains or remote reconstruction.'))
    immutable_json(output/'index.json',dict(schema_version=1,project=project,files=files,modules=len(fetch['modules']),exact_native_references=len(refs),
        source_review_sha256=sha256(DOC/project/'dependency-source-review-declaration.json'),scope='All actual acquired module ZIP/go.mod/version bodies and available SumDB proof-cache bytes retained exactly. SDK descriptor only,not full SDK. Native binaries are separate exact solid packet.'))
    binaries={}
    for directory in [target/'bin',target/'fault-builds',target/'maintenance-builds']:
        if directory.is_dir():
            for path in sorted(directory.rglob('*')):
                if not path.is_file() or path.name.endswith(('.json','.go','.txt','.patch')):continue
                path.resolve(strict=True).relative_to(target.resolve(strict=True));body=path.read_bytes()
                if not body.startswith((b'MZ',b'\x7fELF')):raise ValueError('unreviewed native binary format')
                if len(body)>16*1024**2 or len(binaries)>=64:raise ValueError('native binary corpus bound')
                binaries[path.relative_to(target).as_posix()]=body
    if not binaries or sum(map(len,binaries.values()))>128*1024**2:raise ValueError('native binary expanded bound')
    archive=output/'executables.tar.xz';rows={};unique={}
    with tarfile.open(archive,'w:xz',preset=6) as stream:
        for name,body in binaries.items():
            digest=hashlib.sha256(body).hexdigest();member=unique.setdefault((len(body),digest),name);row=dict(bytes=len(body),sha256=digest)
            if member!=name:
                if binaries[member]!=body:raise ValueError('same-hash executable bytes differ')
                row['member']=member
            else:
                info=tarfile.TarInfo(name);info.size=len(body);info.mode=0o755;stream.addfile(info,io.BytesIO(body))
            rows[name]=row
    if archive.stat().st_size>8*1024**2:raise ValueError('native binary compressed bound')
    restored={}
    with tarfile.open(archive,'r:xz') as stream:
        for member in stream:
            if not member.isfile() or member.name not in binaries or member.name in restored or member.size!=len(binaries[member.name]):raise ValueError('native binary restore coverage differs')
            restored[member.name]=stream.extractfile(member).read(16*1024**2+1)
    for name,row in rows.items():
        if restored[row.get('member',name)]!=binaries[name]:raise ValueError('native executable exact full restoration differs')
    immutable_json(output/'executables-index.json',dict(schema_version=1,project=project,files=rows,archive_sha256=sha256(archive),logical_files=len(rows),unique_payloads=len(unique),all_actual_bytes_compared=True,
        scope='Actual primary,capture,fault and intended-maintenance executable bytes,all restored byte-exact. Source/compile receipts identify each role; duplicate logical paths are exact in-archive aliases. No compatibility credit.'))
    print('Retained',len(fetch['modules']),'actual module archives/metadata;',len(refs),'exact native references;',len(binaries),'native executable paths ->',archive.stat().st_size,'XZ bytes. Full byte readback passed.')


if __name__=='__main__':main()
