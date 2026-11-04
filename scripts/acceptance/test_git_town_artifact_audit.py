import io
import stat
import unittest
import zipfile

from git_town_artifact_audit import read_archive


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


if __name__ == '__main__':
    unittest.main()
