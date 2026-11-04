import io
import stat
import unittest
import zipfile

from git_town_artifact_audit import (RAW, SOURCE_ARCHIVE_SHA256,
                                    audit_source_archive, read_archive)


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
            'source_archive_payload_retained': False,
        })

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


if __name__ == '__main__':
    unittest.main()

