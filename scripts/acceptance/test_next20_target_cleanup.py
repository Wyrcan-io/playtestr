import tempfile
import unittest
from pathlib import Path

from next20_target_cleanup import source_inventory,validate_retained_owned_directories,verify_no_case_evidence


class SourceInventoryTests(unittest.TestCase):
    def test_no_case_cleanup_requires_absent_or_empty_case_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            self.assertTrue(verify_no_case_evidence(root))
            evidence=root/'case-evidence';evidence.mkdir()
            (evidence/'empty').mkdir()
            self.assertTrue(verify_no_case_evidence(root))
            (evidence/'case').mkdir()
            (evidence/'case'/'started.json').write_text('{}')
            with self.assertRaises(ValueError):
                verify_no_case_evidence(root)

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

    def test_final_fault_evidence_directories_are_explicitly_retained(self):
        self.assertEqual(validate_retained_owned_directories(
            ['case-evidence','fault-builds','fault-binaries','fault-events']),
            ['case-evidence','fault-builds','fault-binaries','fault-events'])
        with self.assertRaises(ValueError):
            validate_retained_owned_directories(['src'])
        with self.assertRaises(ValueError):
            validate_retained_owned_directories(['case-evidence','case-evidence'])


if __name__=='__main__':
    unittest.main()
