"""Materialize the pre-frozen Git Town final host contracts under campaign RAW."""
import json
import shutil

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = 'git-town'


def main():
    package = DOC / PROJECT
    freeze_path = package / 'development-test-freeze.json'
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
    target = RAW / PROJECT / 'host-contracts'
    if target.exists():
        raise ValueError('Git Town final host contracts already exist; inspect and preserve the attempt')
    target.mkdir(parents=True)
    for directory in freeze['directories']:
        destination = target / directory
        destination.resolve().relative_to(target.resolve())
        destination.mkdir(parents=True, exist_ok=True)
    copied = {}
    for name, expected in freeze['inputs'].items():
        source = package / name
        source.resolve(strict=True).relative_to(package.resolve())
        if source.is_symlink() or not source.is_file() or sha256(source) != expected:
            raise ValueError('canonical final input differs from its frozen digest: ' + name)
        if name.startswith('fixtures/branch-repo/'):
            copied[name] = expected
            continue
        destination = target / name
        destination.resolve().relative_to(target.resolve())
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        copied[name] = sha256(destination)
    recipe = json.loads((package / 'source-fixture-recipe-v1.json').read_text(encoding='utf-8'))
    target_root = RAW / 'active' / PROJECT
    fixture_manifest_path = target_root / 'fixture-source.json'
    fixture_manifest = json.loads(fixture_manifest_path.read_text(encoding='utf-8'))
    if (recipe.get('source_pin') != '8d039892574d4852e1843020c31d423234042e78' or
            fixture_manifest.get('source_pin') != recipe['source_pin'] or
            fixture_manifest.get('initial_branch') != recipe['initial_branch'] or
            fixture_manifest.get('secondary_branch') != recipe['secondary_branch'] or
            fixture_manifest.get('remote_count') != recipe['remote_count']):
        raise ValueError('host-generated Git Town fixture does not satisfy the frozen recipe')
    source_fixture = package / 'fixtures' / 'branch-repo'
    destination_fixture = target / 'fixtures' / 'branch-repo'
    if destination_fixture.exists():
        if any(destination_fixture.iterdir()):
            raise ValueError('Git Town host fixture destination already contains data')
        destination_fixture.rmdir()
    shutil.copytree(source_fixture, destination_fixture, symlinks=False)
    dynamic_inputs = {}
    actual_fixture = {}
    for path in sorted(destination_fixture.rglob('*')):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('linked Git Town host fixture member')
        if path.is_file():
            relative = path.relative_to(target).as_posix()
            actual_fixture[path.relative_to(destination_fixture).as_posix()] = dict(
                bytes=path.stat().st_size, sha256=sha256(path))
            dynamic_inputs[relative] = sha256(path)
    if actual_fixture != fixture_manifest.get('files'):
        raise ValueError('copied Git Town host fixture differs from its same-run manifest')
    if copied.get('fixtures/branch-repo/README.md') != dynamic_inputs.get('fixtures/branch-repo/README.md'):
        raise ValueError('host-generated Git Town fixture seed differs from the canonical freeze')
    manifest_copy = target / 'fixture-source.json'
    shutil.copyfile(fixture_manifest_path, manifest_copy)
    dynamic_inputs['fixture-source.json'] = sha256(manifest_copy)
    copied.update(dynamic_inputs)
    immutable_json(target / 'development-test-freeze.json', dict(
        schema_version=1, project=PROJECT,
        canonical_freeze_sha256=sha256(freeze_path),
        inputs=copied, directories=freeze['directories'],
        positive_development_summary=freeze['positive_development_summary'],
        final_ordinary_credit=0))
    print('Materialized exact frozen Git Town contracts:', len(copied), 'files')


if __name__ == '__main__':
    main()
