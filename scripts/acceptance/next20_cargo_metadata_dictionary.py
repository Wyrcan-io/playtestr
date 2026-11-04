"""Exact current metadata bytes using mandatory original Windows dictionaries."""
import hashlib
import json
from pathlib import Path

from next20_check import RAW,DOC
from next20_local_records import read_packet as local_packet
from next20_native_packet_reader import read_packet
from next20_lzma_dictionary import encode,decode
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def safe(name):
    require(name and not name.startswith('/') and all(p not in {'','.','..'} and ':' not in p and '\\' not in p for p in name.split('/')),'unsafe logical metadata name')
    return name


def digest(body):return hashlib.sha256(body).hexdigest()


class Original:
    def __init__(self):
        self.root=RAW/'cargo-generate';self.local_index,self.records=local_packet('cargo-generate');self.canonical=None
        self.identity=dict(local_index_sha256=sha256(self.root/'retained-local-v1/index.json'),
            local_archive_sha256=sha256(self.root/'retained-local-v1/packets.tar.xz'),
            primary_archive_sha256=sha256(self.root/'retained-source/source.tar.gz'),
            canonical_native2_index_sha256=sha256(self.root/'retained-native-v2/index.json'),
            canonical_native2_archive_sha256=sha256(self.root/'retained-native-v2/packets.tar.gz'),
            historical_admission_sha256=sha256(DOC/'cargo-generate/admission.json'))

    def data(self,name):
        safe(name);require(name.startswith('cargo-generate/retained-source/'),'original metadata base outside exact source namespace')
        path=RAW/name
        if path.is_file():
            require(path.resolve(strict=True)==path and not path.is_symlink(),'linked original metadata base')
            body=path.read_bytes()
        elif name in self.records:body=self.records[name]
        elif name=='cargo-generate/retained-source/dependency-source-catalog.json':
            reference=json.loads(self.records['cargo-generate/retained-source/dependency-source-catalog.reference.json'])
            require(reference['required_index_sha256']==self.identity['canonical_native2_index_sha256'] and reference['required_archive_sha256']==self.identity['canonical_native2_archive_sha256'],'original metadata native dictionary changed')
            if self.canonical is None:self.canonical=read_packet('cargo-generate',2)[1]
            body=self.canonical[reference['member']]
            require(len(body)==reference['bytes'] and digest(body)==reference['sha256'],'original catalog alias bytes differ')
        else:raise ValueError('missing actual original metadata dictionary: '+name)
        require(len(body)<=16*1024**2,'original metadata member bound')
        return body


def write(root,payloads):
    require(payloads and len(payloads)<=128 and sum(map(len,payloads.values()))<=32*1024**2,'current metadata member/expansion bound')
    require(not root.exists(),'preserve original current-metadata encoding attempt')
    root.mkdir(parents=True);(root/'payloads').mkdir()
    old=Original();rows={}
    for number,(name,body) in enumerate(sorted(payloads.items())):
        safe(name);require(name.startswith('cargo-generate/retained-source-rebuild-v1/') and len(body)<=16*1024**2,'current metadata scope/member bound')
        filename=name.rsplit('/',1)[-1];base_name='cargo-generate/retained-source/'+filename
        try:base=old.data(base_name)
        except ValueError:
            base_name='cargo-generate/retained-source/cleanup-inventory.json';base=old.data(base_name)
        if filename=='short-cache-materialized.json':
            base_name='cargo-generate/retained-source/dependency-source-catalog.json';base=old.data(base_name)
        row=dict(bytes=len(body),sha256=digest(body),base_logical_path=base_name,base_bytes=len(base),base_sha256=digest(base))
        if body==base:row['encoding']='exact-original-metadata-reference'
        else:
            payload,codec=encode(base,body);relative='payloads/'+str(number)+'.lzma2'
            with (root/relative).open('xb') as stream:stream.write(payload)
            require(decode(base,(root/relative).read_bytes(),codec)==body,'actual current metadata full-byte roundtrip differs')
            row.update(encoding='raw-lzma2-preset-dictionary-v1',payload=relative,codec=codec)
        rows[name]=row
    size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file());require(size<=4*1024**2,'current metadata encoded bound')
    immutable_json(root/'index.json',dict(schema_version=1,project='cargo-generate',files=rows,required_original_dictionaries=old.identity,
        expanded_bytes=sum(map(len,payloads.values())),encoder='actual metadata bytes,exact original body reference or bounded full-roundtrip raw-LZMA2 dictionary frame',
        scope='All current metadata bytes preserved exactly; original Windows local/native2/primary-source dictionaries remain mandatory and counted. No target/source deletion or qualification credit.'))
    require(read(root)==payloads,'complete metadata dictionary readback differs')
    immutable_json(root/'verified.json',dict(schema_version=1,index_sha256=sha256(root/'index.json'),members_verified=len(rows),all_actual_bytes_compared=True))
    return rows


def read(root):
    index=json.loads((root/'index.json').read_text());require(index['schema_version']==1 and index['project']=='cargo-generate' and len(index['files'])<=128,'metadata dictionary index scope/bound')
    old=Original();require(index['required_original_dictionaries']==old.identity,'mandatory original metadata dictionary missing or changed')
    result={};total=0
    for name,row in index['files'].items():
        safe(name);base=old.data(row['base_logical_path'])
        require(len(base)==row['base_bytes'] and digest(base)==row['base_sha256'],'actual metadata base identity differs')
        if row['encoding']=='exact-original-metadata-reference':body=base
        else:
            require(row['encoding']=='raw-lzma2-preset-dictionary-v1','unknown current metadata encoding')
            safe(row['payload']);path=root/row['payload'];path.resolve(strict=True).relative_to(root.resolve(strict=True))
            require(path.is_file() and not path.is_symlink() and path.stat().st_size<=4*1024**2,'linked or oversized current metadata frame')
            body=decode(base,path.read_bytes(),row['codec'])
        total+=len(body);require(len(body)==row['bytes'] and digest(body)==row['sha256'] and len(body)<=16*1024**2 and total<=32*1024**2,'actual decoded current metadata differs or exceeds bounds')
        result[name]=body
    require(total==index['expanded_bytes'],'current metadata logical coverage differs')
    return result
