"""Resolve self-contained, hash-verified native identity catalogs without links."""
import re

from readiness_evidence import sha256
from readiness_new_control_matrix import packet_file, read_json


def load_manifest(base, reference):
    path=packet_file(base,reference['manifest'].replace('\\','/'),2*1024**2)
    if sha256(path)!=reference['sha256']:
        raise ValueError('identity manifest checksum differs')
    value=read_json(path,maximum=2*1024**2)
    files=dict(value['files'])
    if 'file_catalogs' not in value:
        return value
    catalogs=value['file_catalogs']
    if value.get('schema_version')!=2 or not isinstance(catalogs,list) or not 1<=len(catalogs)<=2:
        raise ValueError('invalid identity catalog schema')
    scopes=set()
    for reference in catalogs:
        digest=reference.get('sha256','')
        if (set(reference)!={'scope','manifest','sha256'} or reference['scope'] not in {'core','target'}
                or reference['scope'] in scopes or not re.fullmatch('[0-9a-f]{64}',digest)
                or reference['manifest']!='identities/catalogs/'+digest+'.json'):
            raise ValueError('invalid identity catalog reference')
        scopes.add(reference['scope'])
        catalog=packet_file(base,reference['manifest'],2*1024**2)
        if sha256(catalog)!=digest:
            raise ValueError('identity catalog checksum differs')
        payload=read_json(catalog,maximum=2*1024**2)
        if set(payload)!={'schema_version','files'} or payload['schema_version']!=1 or not isinstance(payload['files'],dict):
            raise ValueError('invalid identity catalog payload')
        if set(payload['files'])&set(files):
            raise ValueError('overlapping identity catalog files')
        files.update(payload['files'])
    if len(files)>20000:
        raise ValueError('expanded identity catalog entry bound')
    for name,digest in files.items():
        if (not isinstance(name,str) or '\\' in name or ':' in name or name.startswith('/')
                or any(p in {'','..','.'} for p in name.split('/')) or not isinstance(digest,str)
                or not re.fullmatch('[0-9a-f]{64}',digest)):
            raise ValueError('unsafe identity catalog file entry')
    return dict(value,files=files)
