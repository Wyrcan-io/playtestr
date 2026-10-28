"""Read every retained compiled source and executable byte for both Cargo cells."""
import hashlib
import io
import json
from pathlib import PurePosixPath
import re
import tarfile
import uuid

from next20_check import RAW,DOC
from next20_cargo_source_corpus import Decoder,source_files,MAX_TAR
from next20_cargo_source_reference import file_digest
from next20_cargo_solid_reference import restore
from next20_local_records import read_packet as local_packet
from next20_native_packet_reader import read_packet
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    project=RAW/'cargo-generate';package=DOC/'cargo-generate';corpus=project/'registry-source-corpus-v1'
    index=json.loads((corpus/'index.json').read_text());reference=json.loads((package/'registry-source-corpus-reference-v1.json').read_text())
    require(sha256(corpus/'index.json')==reference['required_dictionary_index_sha256'] and sha256(corpus/'sources.tar.xz')==reference['required_dictionary_archive_sha256']==index['archive_sha256'],'required actual registry source corpus differs')
    require(index['plan_sha256']==reference['plan_sha256']==sha256(package/'compiled-registry-retention-plan.json'),'compiled-source retention plan changed')
    reader=Decoder(corpus/'sources.tar.xz');seen=set();files={}
    try:
        with tarfile.open(fileobj=reader,mode='r|') as stream:
            for member in stream:
                require(member.isfile() and member.name in index['members'] and member.name not in seen and member.size<=MAX_TAR,'source corpus member coverage/type/bound')
                data=stream.extractfile(member).read(MAX_TAR+1);row=index['members'][member.name]
                require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'retained exact inner registry tar differs')
                files.update(source_files(data,member.name.removesuffix('.tar')));seen.add(member.name)
        while reader.read(65536):pass
    finally:reader.close()
    require(set(index['members'])==seen and files==index['files'] and len(files)==reference['source_files'] and file_digest(files)==reference['source_files_digest'],'complete actual registry source file readback differs')
    local_index,local=local_packet('cargo-generate');native_index,native=read_packet('cargo-generate',13);canonical_index,canonical=read_packet('cargo-generate',2)
    def data(records,prefix,name):
        path=RAW/(prefix+name)
        return path.read_bytes() if path.is_file() else records[prefix+name]
    provenance=json.loads((package/'source-provenance.json').read_text());plan=json.loads((package/'compiled-registry-retention-plan.json').read_text())
    packages={name.removesuffix('.crate') for name in plan['selected_archives']};cells=[]
    for host,records,prefix in [('windows',local,''),('linux',native,'native/40758514842/next20-cargo-linux-final/')]:
        def get(name):return data(records,prefix,name)
        build=json.loads(get('cargo-generate/retained-source/build.json'))
        acquisition=json.loads(get('cargo-generate/retained-source/acquisition.json'))
        source=get('cargo-generate/retained-source/source.tar.gz');actual={}
        require(hashlib.sha256(source).hexdigest()==acquisition['archive_sha256'] and acquisition['source_files']==provenance['files'],'actual acquired primary source provenance differs')
        with tarfile.open(fileobj=io.BytesIO(source),mode='r:gz') as stream:
            for member in stream:
                if member.isdir():continue
                name='/'.join(PurePosixPath(member.name).parts[1:])
                require(member.isfile() and name in provenance['files'] and name not in actual and member.size<=8*1024**2,'primary pinned source archive member differs')
                value=stream.extractfile(member).read(8*1024**2+1);actual[name]=hashlib.sha256(value).hexdigest()
        require(actual==provenance['files'],'actual primary source file bytes differ')
        if host=='windows':
            ref=json.loads(get('cargo-generate/retained-source/dependency-source-catalog.reference.json'))
            require(ref['required_archive']=='cargo-generate/retained-native-v2/packets.tar.gz' and ref['required_archive_sha256']==canonical_index['archive_sha256'] and ref['required_index_sha256']==sha256(project/'retained-native-v2/index.json'),'actual Windows source catalog required packet differs')
            catalog_bytes=canonical[ref['member']]
            require(len(catalog_bytes)==ref['bytes'] and hashlib.sha256(catalog_bytes).hexdigest()==ref['sha256'],'actual catalog reference is not byte-identical')
        else:catalog_bytes=get('cargo-generate/retained-source/dependency-source-catalog.json')
        require(hashlib.sha256(catalog_bytes).hexdigest()==build['dependency_source_catalog_sha256'],'actual build source catalog differs')
        catalog=json.loads(catalog_bytes)
        selected={'/'.join(PurePosixPath(n).parts[4:]):digest for n,digest in catalog['files'].items() if PurePosixPath(n).parts[4] in packages}
        require(selected==files,'native actual compiled-source dictionary file bytes differ')
        for name,row in plan['selected_archives'].items():require(catalog['archives_sha256'][row['original_source']]==row['sha256'],'native locked registry archive acquisition differs')
        console=get('cargo-generate/'+build['build_attempt']+'/console.log').decode('utf-8')
        compiled={name+'-'+version for name,version in re.findall(r'Compiling ([A-Za-z0-9_-]+) v([0-9][^\s]*)',console)};compiled.discard('cargo-generate-0.25.1')
        require(bool(compiled) and compiled<=packages,'actual compile used unretained registry source')
        if host=='linux':
            executables=restore(native,native_index['solid_runtime_disposition']);binary_hashes={n:hashlib.sha256(v).hexdigest() for n,v in executables.items()}
        else:
            root=project/'native-solid-variants/windows';binary_index=json.loads((root/'index.json').read_text());require(sha256(root/'executables.tar.xz')==binary_index['archive_sha256'],'actual Windows executable corpus differs')
            decoder=Decoder(root/'executables.tar.xz');binary_hashes={}
            try:
                with tarfile.open(fileobj=decoder,mode='r|') as stream:
                    for member in stream:
                        require(member.isfile() and member.name in binary_index['files'] and member.name not in binary_hashes,'actual Windows executable coverage/type')
                        digest=hashlib.sha256();size=0
                        with stream.extractfile(member) as payload:
                            while block:=payload.read(65536):size+=len(block);digest.update(block)
                        row=binary_index['files'][member.name];require(size==row['bytes'] and digest.hexdigest()==row['sha256'],'full actual Windows executable bytes differ');binary_hashes[member.name]=digest.hexdigest()
                while decoder.read(65536):pass
            finally:decoder.close()
        require(set(binary_hashes)=={'original','F01','F02','F03'} and binary_hashes['original']==build['binary_sha256'],'all actual original/fault executables required')
        fault_root='cargo-generate/'+('source-fault-development/v1/' if host=='windows' else 'source-fault-final-native-exit-v1/v1/')
        for fault in ['F01','F02','F03']:require(json.loads(get(fault_root+fault+'-compiled.json'))['binary_sha256']==binary_hashes[fault],'actual retained mutation differs from compiler receipt')
        cells.append(dict(host=host,primary_source_files=len(actual),actual_compiled_registry_packages=sorted(compiled),actual_executable_sha256=binary_hashes))
    destination=project/('source-closure-'+uuid.uuid4().hex+'.json')
    immutable_json(destination,dict(schema_version=1,registry_inner_tars=len(seen),registry_source_files=len(files),
        required_corpus_index_sha256=sha256(corpus/'index.json'),required_corpus_archive_sha256=sha256(corpus/'sources.tar.xz'),
        current_linux_index_sha256=sha256(project/'retained-native-v13/index.json'),current_linux_archive_sha256=sha256(project/'retained-native-v13/packets.tar.xz'),
        windows_executable_index_sha256=sha256(project/'native-solid-variants/windows/index.json'),windows_executable_archive_sha256=sha256(project/'native-solid-variants/windows/executables.tar.xz'),
        cells=cells,scope='Every actual compiled primary/registry source byte and original/three-fault native executable byte read back. Decoded crate tar bytes retained; original gzip wrappers are acquisition provenance only. Not branch coverage or project admission.'))
    print('Complete actual source/executable readback:',len(seen),'registry packages,',len(files),'registry files,167primary files per native host,all8 actual executables')


if __name__=='__main__':main()
