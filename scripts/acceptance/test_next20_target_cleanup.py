import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import next20_target_cleanup
from next20_target_cleanup import (read_unlaunched_manifest,source_inventory,target_inventory,
    validate_cleanup_window,validate_retained_owned_directories,verify_no_case_evidence,
    workspace_setup_failure_before_launch)


class SourceInventoryTests(unittest.TestCase):
    def test_cleanup_window_names_are_bounded_and_unique_rebuild_slugs(self):
        self.assertEqual(validate_cleanup_window(None), None)
        self.assertEqual(validate_cleanup_window('rebuild-joe-fault-linux-baseline'),
                         'rebuild-joe-fault-linux-baseline')
        for value in ('baseline', '../rebuild-unsafe', 'rebuild-UPPER', 'rebuild-' + 'a' * 57):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_cleanup_window(value)

    def test_prelaunch_workspace_failure_is_explicitly_distinct_from_launched_work(self):
        failure={'category':'workspace_setup_failure','message':'workspace setup failed: fixture root is absent'}
        row={'status':'failed','failure':failure,'target':{'exited':False},'duration_ms':0,
            'cleanup':{'attempted':False,'graceful':False,'forced':False,'confirmed_exited':False},
            'steps':[{'status':'not_run'}], 'workspace':{'attempted':True,'fixture':'fixtures',
            'prepared':False,'cleanup_attempted':False,'cleaned':False,'retained':False,
            'setup_failure':{'category':'workspace_setup_failure','message':'fixture root is absent'}}}
        data={'results':[row]}
        self.assertTrue(workspace_setup_failure_before_launch(data,row))
        changed={**row,'target':{'exited':True}}
        self.assertFalse(workspace_setup_failure_before_launch(data,changed))
        changed={**row,'workspace':{**row['workspace'],'id':'live-workspace'}}
        self.assertFalse(workspace_setup_failure_before_launch(data,changed))
        changed={**row,'steps':[{'status':'passed'}]}
        self.assertFalse(workspace_setup_failure_before_launch(data,changed))

    def test_unlaunched_manifest_is_project_scoped_and_digest_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);project=root/'joe';project.mkdir()
            manifest=project/'unlaunched.json'
            digest='a'*64
            manifest.write_text('{"schema_version":1,"project":"joe","unlaunched_report_sha256":["'+digest+'"]}')
            self.assertEqual(read_unlaunched_manifest(manifest,project,'joe'),[digest])
            outside=root/'outside.json'
            outside.write_text(manifest.read_text())
            with self.assertRaises(ValueError):read_unlaunched_manifest(outside,project,'joe')
            manifest.write_text('{"schema_version":1,"project":"other","unlaunched_report_sha256":["'+digest+'"]}')
            with self.assertRaises(ValueError):read_unlaunched_manifest(manifest,project,'joe')

    def test_reviewed_joe_install_aliases_are_inventory_bound(self):
        if os.name=='nt':
            self.skipTest('JOE campaign aliases are reviewed native Unix symlinks')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'joe';binary=root/'install'/'bin'/'joe'
            binary.parent.mkdir(parents=True);binary.write_bytes(b'joe binary')
            for name in ('jmacs','jstar','rjoe','jpico'):
                (binary.parent/name).symlink_to('joe')
            inventory=target_inventory(root,project='joe')
            self.assertEqual(inventory['owned_links'],{
                'install/bin/jmacs':'joe','install/bin/jstar':'joe',
                'install/bin/rjoe':'joe','install/bin/jpico':'joe'})
            self.assertEqual(inventory['files']['install/bin/joe']['bytes'],len(b'joe binary'))

    def test_joe_install_alias_must_resolve_to_owned_binary(self):
        if os.name=='nt':
            self.skipTest('JOE campaign aliases are reviewed native Unix symlinks')
        with tempfile.TemporaryDirectory() as temporary:
            parent=Path(temporary);root=parent/'joe';bin_dir=root/'install'/'bin'
            bin_dir.mkdir(parents=True);(bin_dir/'joe').write_bytes(b'joe binary')
            outside=parent/'outside';outside.write_bytes(b'outside')
            (bin_dir/'jmacs').symlink_to(outside)
            with self.assertRaisesRegex(ValueError,'unreviewed cleanup source link'):
                target_inventory(root,project='joe')

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
