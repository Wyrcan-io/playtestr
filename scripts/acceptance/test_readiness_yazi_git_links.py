"""Exercise actual filesystem links accepted by the pinned Git-source review."""
from pathlib import Path
import tempfile
import unittest

from readiness_old_yazi_git import license_link


class LicenseLinks(unittest.TestCase):
    def test_exact_link_and_changed_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'LICENSE').write_bytes(b'reviewed license')
            package=root/'ratatui-core';package.mkdir();link=package/'LICENSE'
            try:link.symlink_to('../LICENSE')
            except OSError as error:self.skipTest('native link prerequisite unavailable: '+str(error))
            self.assertEqual(license_link(link,root),b'../LICENSE')
            link.unlink();(root/'other').write_bytes(b'owned canary');link.symlink_to('../other')
            with self.assertRaisesRegex(RuntimeError,'unreviewed'):license_link(link,root)

    def test_unlisted_link_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'LICENSE').write_bytes(b'reviewed license')
            package=root/'unlisted';package.mkdir();link=package/'LICENSE'
            try:link.symlink_to('../LICENSE')
            except OSError as error:self.skipTest('native link prerequisite unavailable: '+str(error))
            with self.assertRaisesRegex(RuntimeError,'unreviewed'):license_link(link,root)


if __name__=='__main__':unittest.main()
