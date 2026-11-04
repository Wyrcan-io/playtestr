"""Verify the hosted Skim checkout byte-for-byte before dependency fetch."""
import json
import argparse
from pathlib import Path
import subprocess

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true',
                        help='compare an already acquired source tree without writing hosted receipts')
    args = parser.parse_args()
    project = RAW / 'active' / 'skim'
    source = project / 'src'
    docs = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass/skim'
    pin = '1ab47f6ba7f1bfc355273bbdd98d4b2056ef95a3'
    provenance_path = docs / 'source-provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    if provenance.get('pin') != pin or provenance.get('repository') != 'skim-rs/skim':
        raise ValueError('Skim provenance does not identify the declared upstream pin')
    if args.verify_only:
        revision = 'local-retained-archive-source'
    else:
        revision = subprocess.run(['git', '-C', str(source), 'rev-parse', 'HEAD'], check=True,
                                  capture_output=True, text=True, timeout=15).stdout.strip()
        if revision != pin:
            raise ValueError('hosted Skim checkout is not the reviewed immutable commit')
    actual = {}
    total = 0
    omitted = provenance.get('omitted_documentation_links', {})
    for path in sorted(source.rglob('*')):
        if '.git' in path.parts:
            continue
        relative = path.relative_to(source).as_posix()
        if relative in omitted:
            expected_target = omitted[relative].get('target')
            if path.is_symlink():
                if path.readlink().as_posix() != expected_target:
                    raise ValueError('omitted documentation link target changed: ' + relative)
            elif path.is_file() and path.read_bytes() != expected_target.encode('utf-8'):
                raise ValueError('Windows link placeholder differs from reviewed Git blob: ' + relative)
            continue
        if path.is_symlink():
            raise ValueError('unexpected linked entry in hosted Skim source: ' + relative)
        if path.is_file():
            size = path.stat().st_size
            total += size
            if size > 8 * 1024 * 1024 or total > 16 * 1024 * 1024:
                raise ValueError('hosted Skim source exceeds reviewed size bounds')
            actual[relative] = sha256(path)
    expected = provenance['files']
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    mismatched = sorted(name for name in expected.keys() & actual.keys()
                        if expected[name] != actual[name])
    if missing or extra or mismatched or len(actual) != provenance['source_blobs_verified']:
        raise ValueError('hosted source differs from provenance: missing=' + repr(missing[:5]) +
                         ', extra=' + repr(extra[:5]) + ', mismatched=' + repr(mismatched[:5]))
    if not args.verify_only:
        project.mkdir(parents=True, exist_ok=True)
        owner = dict(campaign='runner-readiness-next-twenty-project-pass', pin=pin,
                     project='skim-rs/skim', slug='skim', source_only=True,
                     storage_before_bytes=0, workspace=str(ROOT))
        immutable_json(project / 'task-owned.json', owner)
        immutable_json(project / 'source-host-verification.json', dict(
            schema_version=1, project='skim', pin=pin, git_revision=revision,
            source_provenance_sha256=sha256(provenance_path),
            file_count=len(actual), expanded_file_bytes=total,
            source_file_set_sha256=sha256_bytes(json.dumps(actual, sort_keys=True,
                separators=(',', ':')).encode('utf-8')),
            files=actual, target_executed=False,
            policy='Exact source files compared with the reviewed archive provenance before Cargo fetch/build.'))
    print('Verified', len(actual), 'source files at', revision, 'before target execution.')


def sha256_bytes(value):
    import hashlib
    return hashlib.sha256(value).hexdigest()


if __name__ == '__main__':
    main()
