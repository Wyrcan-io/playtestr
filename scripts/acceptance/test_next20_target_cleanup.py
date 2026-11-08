import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import next20_target_cleanup
from next20_target_cleanup import source_inventory,target_inventory,validate_retained_owned_directories,verify_no_case_evidence


class SourceInventoryTests(unittest.TestCase):
    def test_cleanup_can_account_for_active_case_reports(self):
        with tempfile.TemporaryDirectory() as temporary:
            raw=Path(temporary)
            project=raw/'skim';project.mkdir()
            report=raw/'active'/'skim'/'case-evidence'/'attempt-1'/'report.json'
            report.parent.mkdir(parents=True)
            report.write_text('{"runner_version":"0.4.0-rc.6","report_version":3,"results":[]}')
            previous=next20_target_cleanup.RAW
            try:
                next20_target_cleanup.RAW=raw
                rows=list(next20_target_cleanup.cleanup_reports(project,include_active_case_evidence=True))
            finally:
                next20_target_cleanup.RAW=previous
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0][0],report)

    def test_owned_windows_junction_is_recorded_without_traversal(self):
        if os.name!='nt':
            self.skipTest('Windows junction inventory is a native Windows behavior')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'target';root.mkdir()
            destination=root/'owned-destination';destination.mkdir()
            (destination/'payload.txt').write_text('owned')
            junction=root/'owned-junction'
            result=subprocess.run(['cmd.exe','/c','mklink','/J',str(junction),str(destination)],
                capture_output=True,text=True,check=False)
            if result.returncode:
                self.skipTest('host does not permit creating a junction in the test temp directory')
            inventory=target_inventory(root)
            self.assertEqual(inventory['owned_links'],{'owned-junction':'owned-destination'})
            self.assertEqual(set(inventory['files']),{'owned-destination/payload.txt'})

    def test_windows_junction_escaping_owned_target_is_rejected(self):
        if os.name!='nt':
            self.skipTest('Windows junction inventory is a native Windows behavior')
        with tempfile.TemporaryDirectory() as temporary:
            parent=Path(temporary);root=parent/'target';root.mkdir()
            outside=parent/'outside';outside.mkdir()
            (outside/'payload.txt').write_text('outside')
            junction=root/'external-junction'
            result=subprocess.run(['cmd.exe','/c','mklink','/J',str(junction),str(outside)],
                capture_output=True,text=True,check=False)
            if result.returncode:
                self.skipTest('host does not permit creating a junction in the test temp directory')
            with self.assertRaisesRegex(ValueError,'escapes owned target'):
                target_inventory(root)

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
