"""Read explicitly retained local source/wheel bytes from a standalone native packet."""
import hashlib
import json

from next20_check import RAW
from next20_native_packet_reader import read_packet
from next20_packet_archive import archive_path
from readiness_evidence import sha256


def allowed(name):
    return (name=='source.tar.gz' or name.endswith(('.whl','.zip'))) and not any(p in {'','.','..'} or ':' in p or '\\' in p for p in name.split('/'))


def canonical(project,generation,required=None):
    index,records=read_packet(project,generation)
    root=RAW/project/('retained-native-v'+str(generation))
    identity=dict(generation=generation,index_sha256=sha256(root/'index.json'),archive_sha256=sha256(archive_path(root,index)))
    if index.get('external_exact_payloads') or index.get('runtime_frame_disposition') or index.get('solid_runtime_disposition'):
        raise ValueError('local references require standalone canonical packet')
    if required is not None and identity!=required:raise ValueError('required canonical local payload identities changed')
    return identity,records


def reference_for(name,body,records):
    if not allowed(name):return None
    digest=hashlib.sha256(body).hexdigest()
    for logical,raw in records.items():
        if logical.endswith('/'+name.split('/')[-1]) and raw==body:
            return dict(canonical_logical_path=logical,bytes=len(body),sha256=digest)
    return None


def resolve(name,manifest,records):
    if not allowed(name) or manifest.get('schema_version')!=1:raise ValueError('unsafe local canonical reference')
    row=manifest['files'][name];logical=row['canonical_logical_path']
    if logical not in records:raise ValueError('required canonical local payload missing')
    body=records[logical]
    if len(body)!=row['bytes'] or hashlib.sha256(body).hexdigest()!=row['sha256']:raise ValueError('canonical local payload changed')
    return body


def read_reference(project,name):
    root=RAW/project/'retained-source';manifest=json.loads((root/'canonical-native-references.json').read_text())
    if manifest['project']!=project:raise ValueError('foreign local references')
    _,records=canonical(project,manifest['required_canonical_packet']['generation'],manifest['required_canonical_packet'])
    return resolve(name,manifest,records)
