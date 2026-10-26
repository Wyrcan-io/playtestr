"""Prove newly repeated local catalogs are byte-exact existing archive members."""
import json

from next20_check import RAW
from next20_catalog_store import catalog_bytes
from readiness_evidence import immutable_json, sha256


def main():
    retained=RAW/'cz-cli/retained-catalogs-v1'
    index=json.loads((retained/'index.json').read_text(encoding='utf-8'))
    aliases={};files={}
    paths=[*sorted((RAW/'cz-cli/runtime-catalogs').glob('*.json')),RAW/'cz-cli/retained-source/launch-runtime-catalog.json']
    for path in paths:
        path.resolve(strict=True).relative_to(RAW/'cz-cli')
        if path.is_symlink():raise ValueError('linked repeated catalog')
        digest=sha256(path);size=path.stat().st_size
        matches=[name for name,row in index['files'].items() if (row['sha256'],row['bytes'])==(digest,size)]
        if not matches:raise ValueError('Repeated catalog is not byte-exact existing payload: '+path.name)
        canonical=sorted(matches)[0]
        if catalog_bytes(RAW/canonical,digest)!=path.read_bytes():raise ValueError('Alias actual payload differs')
        logical=path.relative_to(RAW).as_posix();aliases[logical]=canonical;files[logical]=dict(bytes=size,sha256=digest)
    selected=retained/'selected-restore.json'
    if catalog_bytes(RAW/index['selected_restore']['logical_path'],index['selected_restore']['sha256'])!=selected.read_bytes():raise ValueError('Selected restore differs from archive')
    files[selected.relative_to(RAW).as_posix()]=dict(bytes=selected.stat().st_size,sha256=sha256(selected))
    immutable_json(retained/'duplicate-aliases.json',dict(schema_version=1,aliases=aliases,files=files,
        original_index_sha256=sha256(retained/'index.json'),archive_sha256=index['archive_sha256'],selected_restore_sha256=sha256(selected),
        scope='Exact repeated bytes only. Original archive/index unchanged; new logical paths map directly to existing original packet entries, never to another alias. Selected restore was verified byte exactly before removal. No execution credit.'))
    print('Verified repeated exact catalog payloads:',len(files),'files',sum(r['bytes'] for r in files.values()),'bytes; checked literal removal pending.')


if __name__=='__main__':main()
