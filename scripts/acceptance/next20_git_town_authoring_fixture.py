"""Materialize the committed Git Town fixture template for an exact suite."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


ROOT = Path(__file__).resolve().parents[2]
AUTHORING = ROOT / 'docs' / 'validation' / 'runner-readiness-next-twenty-project-pass' / 'git-town' / 'authoring'
FIXTURE_NAME = 'branch-repo'
TEMPLATE_NAME = 'branch-repo-template'
POINTER = b'gitdir: .gitdir\n'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def linked(path):
    return path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def suite_paths(raw):
    candidate = (ROOT / raw).resolve(strict=True)
    if not candidate.is_dir() or linked(candidate):
        raise ValueError('suite directory must be an ordinary owned directory')
    if not candidate.is_relative_to(AUTHORING.resolve()):
        raise ValueError('suite directory is outside the Git Town authoring namespace')
    fixtures = candidate / 'fixtures'
    template = fixtures / TEMPLATE_NAME
    destination = fixtures / FIXTURE_NAME
    for path in (fixtures, template):
        if not path.is_dir() or linked(path):
            raise ValueError(f'fixture path is missing or linked: {path}')
    manifest = candidate / ('fixture-manifest-v1.json' if candidate == AUTHORING else 'relocation-manifest-v1.json')
    if linked(manifest) or not manifest.is_file():
        raise ValueError('fixture manifest is missing or linked')
    return candidate, fixtures, template, destination, manifest


def expected_files(template, manifest):
    data = json.loads(manifest.read_text(encoding='utf-8'))
    entries = data.get('files') or data.get('byte_identical_files')
    if not isinstance(entries, dict) or not entries or len(entries) > 5000:
        raise ValueError('fixture manifest has no bounded file inventory')
    observed = {}
    for path in template.rglob('*'):
        if linked(path):
            raise ValueError('fixture template contains a link')
        if path.is_file():
            rel = path.relative_to(template).as_posix()
            observed[rel] = path
    if set(observed) != set(entries):
        raise ValueError('fixture template paths differ from its manifest')
    for rel, path in observed.items():
        row = entries[rel]
        if path.stat().st_size != row.get('bytes') or sha256(path) != row.get('sha256'):
            raise ValueError(f'fixture template bytes differ from manifest: {rel}')
    if observed.get('git-pointer.txt') is None or observed['git-pointer.txt'].read_bytes() != POINTER:
        raise ValueError('fixture Git metadata pointer template differs')
    return observed


def target_inventory(root, entries):
    expected = {}
    for rel in entries:
        if rel == 'git-pointer.txt':
            target_rel = '.git'
        elif rel.startswith('.git-metadata/'):
            target_rel = '.gitdir/' + rel[len('.git-metadata/'):]
        else:
            target_rel = rel
        source = entries[rel]
        expected[target_rel] = {
            'bytes': source.stat().st_size,
            'sha256': sha256(source),
        }
    observed = {}
    for path in root.rglob('*'):
        if linked(path):
            raise ValueError('materialized Git Town fixture contains a link')
        if path.is_file():
            observed[path.relative_to(root).as_posix()] = path
    if set(observed) != set(expected):
        raise ValueError('materialized fixture paths differ from the reviewed inventory')
    for rel, path in observed.items():
        row = expected[rel]
        if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
            raise ValueError(f'materialized fixture bytes differ: {rel}')


def prepare(template, destination, entries):
    if destination.exists() or linked(destination):
        raise ValueError('refusing to replace an existing materialized fixture')
    temporary = Path(tempfile.mkdtemp(prefix='.branch-repo-pending-', dir=destination.parent))
    try:
        for rel, source in entries.items():
            if rel == 'git-pointer.txt':
                target_rel = '.git'
            elif rel.startswith('.git-metadata/'):
                target_rel = '.gitdir/' + rel[len('.git-metadata/'):]
            else:
                target_rel = rel
            target = temporary / target_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        target_inventory(temporary, entries)
        os.replace(temporary, destination)
        print(f'Prepared verified synthetic Git Town fixture: {len(entries) - 1} files')
    except BaseException:
        if temporary.exists() and not linked(temporary):
            shutil.rmtree(temporary)
        raise


def remove(destination, entries):
    if not destination.exists():
        print('No materialized synthetic Git Town fixture to remove')
        return
    if not destination.is_dir() or linked(destination):
        raise ValueError('refusing to remove a linked or non-directory fixture path')
    target_inventory(destination, entries)
    shutil.rmtree(destination)
    print('Removed verified synthetic Git Town fixture')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite-directory', required=True,
                        help='repository-relative authoring suite directory')
    parser.add_argument('--remove', action='store_true',
                        help='remove only the exact fixture created from its reviewed template')
    args = parser.parse_args()
    suite, _, template, destination, manifest = suite_paths(args.suite_directory)
    entries = expected_files(template, manifest)
    if args.remove:
        remove(destination, entries)
    else:
        prepare(template, destination, entries)


if __name__ == '__main__':
    main()
