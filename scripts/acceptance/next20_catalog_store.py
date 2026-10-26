"""Read exact catalog bytes from physical files or verified local retention."""
import hashlib
import json
from pathlib import Path
import tarfile

from next20_check import RAW
from readiness_compact_native import verify
from readiness_evidence import sha256


def catalog_bytes(path,expected_sha256):
    path=Path(path);logical=path.resolve().relative_to(RAW.resolve()).as_posix()
    if path.is_file():
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)() or path.stat().st_size>4*1024**2:
            raise ValueError('Unsafe physical catalog')
        data=path.read_bytes()
    else:
        project=logical.split('/',1)[0]
        if project not in {'cz-cli','yo'}:raise ValueError('No declared local catalog retention for this project')
        retained=RAW/project/'retained-catalogs-v1'
        for checked in [retained,retained/'index.json',retained/'verified.json',retained/'packets.tar.gz']:
            checked.resolve(strict=True).relative_to(RAW.resolve())
            if checked.is_symlink() or getattr(checked,'is_junction',lambda:False)():raise ValueError('Linked catalog retention entry')
        index=json.loads((retained/'index.json').read_text(encoding='utf-8'))
        proof=json.loads((retained/'verified.json').read_text(encoding='utf-8'))
        expected_kind='local-interpreted-runtime-catalogs' if project=='yo' else 'local-compiled-runtime-catalogs'
        if index['kind']!=expected_kind or index['project']!=project or sha256(retained/'index.json')!=proof['index_sha256']:
            raise ValueError('Changed/foreign catalog retention identity')
        if sha256(retained/'packets.tar.gz')!=index['archive_sha256']:raise ValueError('Changed catalog retention payload')
        verify(retained/'packets.tar.gz',index['files'])
        selected=index['selected_restore']
        restored=retained/'selected-restore.json'
        selected_ok=restored.is_file() and not restored.is_symlink() and sha256(restored)==selected['sha256']
        if not restored.exists():
            removed=json.loads((retained/'duplicate-aliases-removed.json').read_text(encoding='utf-8-sig'))
            selected_ok=removed['all_exact_duplicates_removed'] and removed['original_index_sha256']==sha256(retained/'index.json') and removed['selected_restore_sha256']==selected['sha256']
        if selected['path']!='selected-restore.json' or not selected_ok or selected['sha256']!=index['files'][selected['logical_path']]['sha256']:
            raise ValueError('Changed/unverified selected catalog restore')
        canonical=logical
        if canonical not in index['files']:
            aliases=json.loads((retained/'duplicate-aliases.json').read_text(encoding='utf-8'))
            if aliases['original_index_sha256']!=sha256(retained/'index.json'):raise ValueError('Changed catalog alias source index')
            canonical=aliases['aliases'][logical]
            if canonical not in index['files']:raise ValueError('Catalog alias target absent from original packet')
        row=index['files'][canonical]
        if row['bytes']>4*1024**2 or row['sha256']!=expected_sha256:raise ValueError('Wrong bounded retained catalog')
        with tarfile.open(retained/'packets.tar.gz','r:gz') as archive:
            data=archive.extractfile(row.get('member',canonical)).read(4*1024**2+1)
        if len(data)!=row['bytes']:raise ValueError('Retained catalog size differs')
    if hashlib.sha256(data).hexdigest()!=expected_sha256:raise ValueError('Catalog bytes differ from actual recorded identity')
    return data


if __name__=='__main__':
    import argparse
    from readiness_evidence import immutable_json
    parser=argparse.ArgumentParser();parser.add_argument('project',choices=['cz-cli','yo']);args=parser.parse_args()
    retained=RAW/args.project/'retained-catalogs-v1'
    index=json.loads((retained/'index.json').read_text(encoding='utf-8'))
    for name,row in index['files'].items():
        if (RAW/name).exists():raise ValueError('Catalog expansion not removed')
        if len(catalog_bytes(RAW/name,row['sha256']))!=row['bytes']:raise ValueError('Original logical catalog size differs')
    immutable_json(retained/'read-back-verified.json',dict(schema_version=1,logical_paths_verified=len(index['files']),
        index_sha256=sha256(retained/'index.json'),archive_sha256=sha256(retained/'packets.tar.gz'),
        all_original_expansions_absent=True,scope='Actual byte-exact readback of every original local catalog logical path after checked removal. No target/native/admission credit.'))
    print('Verified exact readback of',len(index['files']),'original local catalog paths after checked expansion removal.')
