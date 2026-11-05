import tempfile
import unittest
from pathlib import Path

from next20_target_cleanup import source_inventory


class SourceInventoryTests(unittest.TestCase):
    def test_excludes_git_metadata_but_hashes_primary_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'main.go').write_bytes(b'package main\n')
            (root/'.git').mkdir()
            (root/'.git'/'config').write_bytes(b'private local checkout metadata')
            inventory=source_inventory(root)
            self.assertEqual(set(inventory),{'main.go'})

    def test_rejects_linked_primary_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            outside=root/'outside.txt';outside.write_text('source')
            try:
                (root/'linked.txt').symlink_to(outside)
            except (OSError,NotImplementedError):
                self.skipTest('host does not permit creating a symlink in the test temp directory')
            with self.assertRaises(ValueError):
                source_inventory(root)


if __name__=='__main__':
    unittest.main()
