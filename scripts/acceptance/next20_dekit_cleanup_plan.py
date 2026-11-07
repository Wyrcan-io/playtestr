"""Verify and compact rejected DeKit evidence before native checked workspace removal."""
import json
from pathlib import Path
import shutil

from readiness_evidence import immutable_json, sha256

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'artifacts/runner-readiness-next-twenty-project-pass'
DOC = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass'
ACTIVE = RAW / 'active/dekit'
DEST = RAW / 'dekit/retained-exploratory-v1'
OMIT = {'cargo-home', 'cargo-target', 'home', 'rustup-home', 'src', 'tmp'}


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    require(ACTIVE.is_dir() and not ACTIVE.is_symlink(), 'owned DeKit root absent or linked')
    require(not DEST.exists(), 'retained evidence destination already exists')
    acquisition = json.loads((ACTIVE / 'acquisition.json').read_text(encoding='utf-8'))
    provenance = json.loads((DOC / 'dekit/source-provenance.json').read_text(encoding='utf-8'))
    source = ACTIVE / 'src'
    expected = provenance['files']
    observed = {}
    for path in source.rglob('*'):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('linked pinned source path refused: ' + str(path.relative_to(source)))
        if path.is_file() and '.git' not in path.relative_to(source).parts:
            observed[path.relative_to(source).as_posix()] = sha256(path)
    require(observed == expected, 'materialized DeKit source differs from the exact reviewed pin')
    source_archive = ACTIVE / 'source.tar.gz'
    require(sha256(source_archive) == acquisition['archive_sha256'], 'retained source archive differs from acquisition receipt')
    DEST.mkdir(parents=True)
    copied = []
    for path in sorted(ACTIVE.rglob('*')):
        relative = path.relative_to(ACTIVE)
        if not relative.parts or relative.parts[0] in OMIT:
            continue
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('unreviewed link in evidence being preserved: ' + str(relative))
        if path.is_file():
            destination = DEST / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            digest = sha256(path)
            require(sha256(destination) == digest and path.stat().st_size == destination.stat().st_size,
                    'copied evidence differs: ' + str(relative))
            copied.append(dict(source=relative.as_posix(), retained=destination.relative_to(RAW).as_posix(),
                bytes=destination.stat().st_size, sha256=digest))
    require(any(row['source'] == 'source.tar.gz' for row in copied), 'pinned source archive was not retained')
    # Re-read every member after the full copy pass, before cleanup is allowed.
    for row in copied:
        path = DEST / Path(row['source'])
        require(path.is_file() and path.stat().st_size == row['bytes'] and sha256(path) == row['sha256'],
                'preserved evidence readback differs: ' + row['source'])
    receipt = DEST / 'preservation-index.json'
    immutable_json(receipt, dict(schema_version=1, project='dekit', pin=acquisition['pin'],
        source_archive_sha256=sha256(source_archive), source_files_verified=len(observed),
        source_tree_manifest_sha256=sha256(DOC / 'dekit/source-provenance.json'),
        copied_files=copied, copied_file_count=len(copied),
        scope='Compact evidence copy of rejected exploratory build, test, smoke and cleanup receipts. The exact pinned source tarball is retained. Rust/Cargo compiler and dependency caches, extracted source, and isolated home/temp are deliberately excluded as reproducible target workspace data.'))
    reparse = []
    for path in ACTIVE.rglob('*'):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            reparse.append(path.relative_to(ACTIVE).as_posix())
    plan = dict(schema_version=1, project='dekit', workspace=str(ACTIVE.resolve()),
        preserved_index=str(receipt), preserved_index_sha256=sha256(receipt),
        source_tree_files=len(observed), source_archive_sha256=sha256(source_archive),
        remove_exact_reparse_points=reparse, remove_owned_root=True,
        disposition='Rejected exploratory workspace; no further DeKit execution is planned. Preserve copied receipts and pinned source tarball before checked removal.')
    immutable_json(DEST / 'checked-removal-plan.json', plan)
    print('DeKit cleanup plan prepared: source pin verified across', len(observed),
          'files; preserved', len(copied), 'evidence files; reparse points:', reparse)


if __name__ == '__main__':
    main()
