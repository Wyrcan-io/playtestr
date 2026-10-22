"""Bind the inspected jrnl source and wheel review before offline installation."""
import hashlib
import json

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def main():
    target=RAW/'active/jrnl';source=target/'src'
    marker=json.loads((target/'task-owned.json').read_text())
    tree_path=RAW/'screening/reviews/jrnl-org--jrnl'/marker['pin']/'tree.json'
    tree=json.loads(tree_path.read_text())
    expected={r['path']:r['sha'] for r in tree['tree'] if r['type']=='blob'}
    actual={p.relative_to(source).as_posix():p for p in source.rglob('*') if p.is_file()}
    if set(expected)!=set(actual):raise ValueError('source archive/tree coverage mismatch')
    for name,path in actual.items():
        data=path.read_bytes()
        digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if digest!=expected[name]:raise ValueError('pinned Git source blob mismatch: '+name)
    review=json.loads((target/'dependency-review.json').read_text())
    if len(review['wheels'])!=23 or any(w['startup_hooks'] for w in review['wheels']):
        raise ValueError('different dependency/hook review inputs')
    source_inputs=['pyproject.toml','LICENSE.md','jrnl/main.py','jrnl/install.py','jrnl/config.py',
        'jrnl/path.py','jrnl/editor.py','jrnl/controller.py','jrnl/prompt.py','jrnl/plugins/__init__.py',
        'jrnl/journals/Journal.py']
    record=dict(schema_version=1,approved=True,review_sha256=sha256(target/'dependency-review.json'),
        pinned_tree_sha256=sha256(tree_path),source_blobs_verified=len(actual),
        reviewed_source={n:sha256(source/n) for n in source_inputs},
        package_provenance='Declared upstream Python packages; retained wheel metadata identifies primary project URLs and licenses. No source distributions or automatic wheel startup hooks.',
        native_extensions=['cffi','cryptography','ruamel.yaml.clib'],
        backend='poetry.core.masonry.api from retained poetry-core wheel; editable source build offline without isolation/network',
        execution_scope='Synthetic unencrypted text journal only; explicit config path, no external editor, null keyring backend; no npm/dev tasks or external services.',
        pyxdg_license='Wheel METADATA says UNKNOWN; package source headers/license require attribution check before redistributing dependency bytes. Private local execution only; no dependency redistribution/publication authorized.')
    immutable_json(target/'install-approval.json',record)
    immutable_json(DOC/'jrnl/source-review.json',record)
    print('Pinned source:',len(actual),'exact Git blobs. Reviewed 23 retained wheel inputs and ordinary offline backend; private synthetic execution approved.')


if __name__=='__main__':main()
