"""Prepare checked disposal of redundant compiler cache and retention experiments."""
import hashlib
import json
from pathlib import Path
import tarfile
import uuid

from next20_check import RAW,ROOT,DOC
from next20_cargo_source_corpus import Decoder
from next20_binary_delta import decode
from next20_rust_fetch import short_owned_path
from readiness_evidence import immutable_json,sha256


def main():
    project=RAW/'cargo-generate';target=RAW/'active/cargo-generate'
    runtime=json.loads((target/'runtime.json').read_text());binary=Path(runtime['native'])
    if sha256(binary)!=runtime['native_sha256']:raise ValueError('original executable not restored')
    solid=project/'native-solid-variants/windows';index=json.loads((solid/'index.json').read_text());archive=solid/'executables.tar.xz'
    if sha256(archive)!=index['archive_sha256']:raise ValueError('required retained executable corpus changed')
    reader=Decoder(archive);restored={}
    try:
        with tarfile.open(fileobj=reader,mode='r|') as stream:
            for member in stream:
                if member.name in restored or member.name not in index['files'] or not member.isfile() or member.size!=index['files'][member.name]['bytes']:raise ValueError('retained executable layout differs')
                data=stream.extractfile(member).read(64*1024**2+1)
                if hashlib.sha256(data).hexdigest()!=index['files'][member.name]['sha256']:raise ValueError('required actual executable restore failed')
                restored[member.name]=data
        while reader.read(65536):pass
    finally:reader.close()
    if set(restored)!={'original','F01','F02','F03'} or restored['original']!=binary.read_bytes():raise ValueError('incomplete retained executable corpus')
    delta_root=project/'native-variant-retention/windows';delta_index=json.loads((delta_root/'index.json').read_text());paths=[]
    for fault,row in delta_index['variants'].items():
        path=delta_root/row['delta_file']
        if decode(restored['original'],path.read_bytes(),row)!=restored[fault]:raise ValueError('superseded representation differs from retained actual executable')
        paths.append(path)
    baseline=project/'native-preflight/windows';baseline_index=json.loads((baseline/'compiled-binary-index.json').read_text());base_archive=baseline/'compiled-binary.tar.xz'
    if sha256(base_archive)!=baseline_index['archive_sha256']:raise ValueError('superseded baseline archive changed')
    with tarfile.open(base_archive,'r:xz') as stream:
        if stream.extractfile('cargo-generate.exe').read(64*1024**2+1)!=restored['original']:raise ValueError('superseded baseline differs from retained executable')
    paths.append(base_archive)
    corpus=project/'registry-source-corpus-v1';reference=json.loads((DOC/'cargo-generate/registry-source-corpus-reference-v1.json').read_text())
    if sha256(corpus/'sources.tar.xz')!=reference['required_dictionary_archive_sha256'] or sha256(corpus/'index.json')!=reference['required_dictionary_index_sha256']:raise ValueError('required exact source corpus changed')
    cache=RAW/'r';owner=json.loads((cache/'task-owned.json').read_text());materialized=json.loads((cache/'materialized.json').read_text())
    if owner['workspace']!=str(ROOT) or owner['source_target']!=str(target) or owner['project']!='cargo-generate':raise ValueError('foreign short compiler cache')
    # The complete retained source corpus already passed full source-file
    # readback. Recheck the original compressed registry once (369 archives),
    # then let the native removal command hash every cache byte against the
    # frozen materialization catalog; avoid three redundant16k-file scans.
    for name,digest in materialized['archives'].items():
        if sha256(target/'cargo-home'/name)!=digest:raise ValueError('still-preserved original registry archive changed')
    expected_cache={**materialized['files'],**materialized['archives']}
    files={};cache_files={};total=0
    for root in [cache]:
        for path in root.rglob('*'):
            if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked disposable cache')
            if path.is_file():
                relative=path.relative_to(cache).as_posix();digest=expected_cache.get(relative)
                cache_files[path.relative_to(ROOT).as_posix()]=dict(bytes=path.stat().st_size,sha256=digest if digest is not None else sha256(path))
    if not set(expected_cache)<={Path(name).relative_to(cache.relative_to(ROOT)).as_posix() for name in cache_files}:raise ValueError('materialized cache source payload missing')
    for path in paths:
        if path.is_symlink():raise ValueError('linked redundant representation')
        files[path.relative_to(ROOT).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha256(path))
    total=sum(r['bytes'] for r in [*files.values(),*cache_files.values()])
    if len(cache_files)>25000 or total>512*1024**2:raise ValueError('disposable representation bound')
    root=project/'checked-pruning';root.mkdir(exist_ok=True);identifier=uuid.uuid4().hex
    immutable_json(root/(identifier+'.json'),dict(schema_version=1,workspace=str(ROOT),cache_root=str(cache),
        cache_short=short_owned_path(cache),target_root=str(target),target_short=short_owned_path(target),
        cache_files=cache_files,files=files,total_bytes=total,
        required_archive_sha256=sha256(archive),required_archive=str(archive),
        required_source_archive=str(corpus/'sources.tar.xz'),required_source_archive_sha256=sha256(corpus/'sources.tar.xz'),
        scope='Expendable duplicate short compiler cache and superseded experimental encodings only; all exact actual executable/source bytes retained, original registry remains, metadata/first failures/reports untouched.'))
    print('Prepared checked pruning:',identifier,total,'bytes; original registry and full retained source/executable corpus verified')


if __name__=='__main__':main()
