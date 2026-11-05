import io
import hashlib
import json
import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

from git_town_artifact_audit import (PACKAGE, RAW, SOURCE_ARCHIVE_SHA256,
                                    audit_source_archive, curate_packet, read_archive)
from next20_git_town_prepare import create_source_archive


def archive(name='evidence/report.json', body=b'{}', mode=stat.S_IFREG | 0o644):
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as zf:
        info = zipfile.ZipInfo(name)
        info.external_attr = mode << 16
        zf.writestr(info, body)
    return result.getvalue()


class GitTownArtifactAuditTests(unittest.TestCase):
    def test_reads_regular_member_bytes(self):
        self.assertEqual(read_archive(archive()), {'evidence/report.json': b'{}'})

    def test_rejects_traversal_paths(self):
        with self.assertRaisesRegex(ValueError, 'unsafe provider ZIP member path'):
            read_archive(archive('../outside.json'))

    def test_rejects_symlink_members(self):
        with self.assertRaisesRegex(ValueError, 'encrypted or linked'):
            read_archive(archive('evidence/link', mode=stat.S_IFLNK | 0o777))

    def test_rejects_duplicate_paths(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as zf:
            zf.writestr('evidence/report.json', b'{}')
            zf.writestr('evidence/report.json', b'{"second":true}')
        with self.assertRaisesRegex(ValueError, 'duplicate or oversized'):
            read_archive(stream.getvalue())

    def test_accepts_verified_source_tree_when_archive_payload_was_not_uploaded(self):
        result = audit_source_archive({}, {'source_archive_sha256': SOURCE_ARCHIVE_SHA256})
        self.assertEqual(result, {
            'source_archive_sha256': SOURCE_ARCHIVE_SHA256,
            'source_archive_method': 'reviewed pinned archive digest',
            'source_archive_payload_retained': False,
        })

    def test_verifies_generated_archive_against_complete_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'source'
            target = Path(root) / 'target'
            source.mkdir()
            target.mkdir()
            members = {'README.md': b'Pinned bytes\n', 'internal/main.go': b'package main\n'}
            expected = {}
            for name, body in members.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
                expected[name] = hashlib.sha256(body).hexdigest()
            archive_sha, archive_bytes = create_source_archive(source, expected, target)
            body = (target / 'source.tar.gz').read_bytes()
            acquisition = {
                'source_archive_method': 'deterministic gzip/PAX archive generated from the verified pinned Git checkout',
                'source_archive_sha256': archive_sha,
                'source_archive_bytes': archive_bytes,
            }

            result = audit_source_archive({RAW + 'source.tar.gz': body}, acquisition, expected)

            self.assertTrue(result['source_archive_payload_retained'])
            self.assertEqual(result['source_archive_sha256'], archive_sha)

    def test_generated_archive_rejects_a_manifest_mismatch(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'source'
            target = Path(root) / 'target'
            source.mkdir()
            target.mkdir()
            body = b'Pinned bytes\n'
            (source / 'README.md').write_bytes(body)
            source_hash = hashlib.sha256(body).hexdigest()
            archive_sha, archive_bytes = create_source_archive(
                source, {'README.md': source_hash}, target)
            acquisition = {
                'source_archive_method': 'deterministic gzip/PAX archive generated from the verified pinned Git checkout',
                'source_archive_sha256': archive_sha,
                'source_archive_bytes': archive_bytes,
            }

            with self.assertRaisesRegex(ValueError, 'member differs from pinned provenance'):
                audit_source_archive({RAW + 'source.tar.gz': (target / 'source.tar.gz').read_bytes()},
                                     acquisition, {'README.md': '0' * 64})

    def test_verifies_archive_payload_when_present(self):
        body = b'pinned archive'
        archive_sha = __import__('hashlib').sha256(body).hexdigest()
        # The production digest remains fixed; exercise the retained-byte branch
        # by temporarily supplying the reviewed pin's exact constant through a
        # patched module constant in the test process.
        import git_town_artifact_audit as auditor
        original = auditor.SOURCE_ARCHIVE_SHA256
        auditor.SOURCE_ARCHIVE_SHA256 = archive_sha
        try:
            result = audit_source_archive({RAW + 'source.tar.gz': body},
                                          {'source_archive_sha256': archive_sha})
            self.assertTrue(result['source_archive_payload_retained'])
            with self.assertRaisesRegex(ValueError, 'retained pinned-source archive digest differs'):
                audit_source_archive({RAW + 'source.tar.gz': b'changed'},
                                     {'source_archive_sha256': archive_sha})
        finally:
            auditor.SOURCE_ARCHIVE_SHA256 = original

    def test_curates_reports_and_deduplicates_source_and_binaries(self):
        files = {
            RAW + 'src/main.go': b'canonical source',
            RAW + 'src/.git/config': b'version-control metadata',
            RAW + 'bin/git-town': b'checked target binary',
            RAW + 'fault-binaries/F01.exe': b'checked rebuilt binary',
            RAW + 'case-evidence/N01/report.json': b'{"passed":true}',
            PACKAGE + 'N01.json': b'{"version":3}',
        }
        with tempfile.TemporaryDirectory() as root:
            linux = os.path.join(root, 'linux.zip')
            windows = os.path.join(root, 'windows.zip')
            curate_packet(files, 'linux', linux)
            curate_packet(files, 'windows', windows)
            linux_files = read_archive(Path(linux).read_bytes())
            windows_files = read_archive(Path(windows).read_bytes())
        self.assertIn(RAW + 'src/main.go', linux_files)
        self.assertNotIn(RAW + 'src/.git/config', linux_files)
        self.assertIn(PACKAGE + 'N01.json', linux_files)
        self.assertIn(RAW + 'case-evidence/N01/report.json', windows_files)
        self.assertNotIn(RAW + 'src/main.go', windows_files)
        for retained in (linux_files, windows_files):
            self.assertFalse(any('/bin/' in name or '/fault-binaries/' in name for name in retained))
            index = json.loads(retained['retention-index-v1.json'])
            self.assertTrue(any(row['omitted_after_independent_verification'].startswith('binary bytes')
                                for row in index['members'] if not row['retained']))


if __name__ == '__main__':
    unittest.main()
