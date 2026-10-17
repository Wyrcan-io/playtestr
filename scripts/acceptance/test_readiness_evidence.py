import concurrent.futures
import json
from pathlib import Path
import tempfile
import unittest
import uuid

from readiness_evidence import Campaign, RAW, immutable_json


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        RAW.mkdir(parents=True, exist_ok=True)
        self.folder = tempfile.TemporaryDirectory(dir=RAW)
        self.addCleanup(self.folder.cleanup)
        self.campaign = Campaign(Path(self.folder.name))

    def test_concurrent_exclusive_events(self):
        def write(_):
            identity = uuid.uuid4().hex
            for event in ['started', 'identified', 'launched', 'finished']:
                self.campaign.append(dict(id=identity, event=event, project='fixture', label='control'))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(write, range(20)))
        self.assertEqual(len(self.campaign.attempts()), 20)

    def test_duplicate_cannot_overwrite_failure(self):
        path = Path(self.folder.name)/'failure.json'
        immutable_json(path, {'status':'failed'})
        with self.assertRaises(FileExistsError):
            immutable_json(path, {'status':'passed'})
        self.assertEqual(json.loads(path.read_text())['status'], 'failed')

    def test_interrupted_and_malformed_records_reject(self):
        events = Path(self.folder.name)/'events'
        events.mkdir()
        partial = events/'.event.partial'
        partial.write_bytes(b'{')
        with self.assertRaises(ValueError): self.campaign.attempts()
        partial.unlink()
        (events/'bad.json').write_bytes(b'{')
        with self.assertRaises(ValueError): self.campaign.attempts()

    def test_started_without_outcome_rejects(self):
        self.campaign.append(dict(id=uuid.uuid4().hex,event='started',project='fixture',label='control'))
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.campaign.attempts()

    def test_downloaded_go_sources_have_module_boundary(self):
        boundary = Path(self.folder.name)/'go.mod'
        self.assertIn(b'module playtestr.invalid/', boundary.read_bytes())
        Campaign(Path(self.folder.name))
        boundary.write_bytes(b'module unexpected\n')
        with self.assertRaisesRegex(ValueError, 'module boundary'):
            Campaign(Path(self.folder.name))

    def test_rejected_prelaunch_identity_is_accounted_without_credit(self):
        import asyncio
        from adversarial_process import execute
        class RejectIdentity(Campaign):
            def identity(self, project, argv):
                raise ValueError('synthetic prelaunch identity rejection')
        campaign=RejectIdentity(Path(self.folder.name))
        with self.assertRaisesRegex(ValueError,'identity rejection'):
            asyncio.run(execute(['must-not-launch'],'identity-control','rejected-setup',
                                timeout=5,campaign=campaign))
        attempts=campaign.attempts()
        self.assertEqual(len(attempts),1)
        events=next(iter(attempts.values()))
        self.assertNotIn('identified',events)
        self.assertNotIn('launched',events)
        self.assertEqual(events['finished']['harness_cleanup'],'not_started')

    def test_success_without_prelaunch_identity_rejects(self):
        identity=uuid.uuid4().hex
        self.campaign.append(dict(id=identity,event='started',project='fixture',label='control'))
        self.campaign.append(dict(id=identity,event='finished',project='fixture',label='control',
                                  category='passed',exit_code=0,harness_cleanup='harness_process_reaped'))
        with self.assertRaisesRegex(ValueError,'prelaunch identity'):
            self.campaign.attempts()

    def test_editable_target_mutation_changes_prelaunch_identity(self):
        target=Path(self.folder.name)/'active/poetry'
        source=target/'src/src/poetry/changed.py'
        source.parent.mkdir(parents=True)
        source.write_bytes(b'reviewed original\n')
        (target/'task-owned.json').write_text('{}')
        (target/'src/pyproject.toml').write_text('[project]\nname="owned-control"\n')
        (target/'src/poetry.lock').write_text('# reviewed lock\n')
        before=self.campaign.identity('poetry',['must-not-launch'])
        source.write_bytes(b'real source mutation\n')
        after=self.campaign.identity('poetry',['must-not-launch'])
        self.assertNotEqual(before['sha256'],after['sha256'])
        source.write_bytes(b'reviewed original\n')
        restored=self.campaign.identity('poetry',['must-not-launch'])
        self.assertEqual(before,restored)

    def test_real_template_mutation_changes_prelaunch_identity(self):
        target=Path(self.folder.name)/'active/rubygems'
        source=target/'src/lib/bundler/templates/version.rb.tt'
        source.parent.mkdir(parents=True)
        source.write_bytes(b'VERSION = "0.1.0"\n')
        (target/'task-owned.json').write_text('{}')
        (target/'src/exe').mkdir()
        (target/'src/bundler.gemspec').write_text('# reviewed gemspec\n')
        before=self.campaign.identity('rubygems',['must-not-launch'])
        source.write_bytes(b'VERSION = "0.1.1"\n')
        after=self.campaign.identity('rubygems',['must-not-launch'])
        self.assertNotEqual(before['sha256'],after['sha256'])
        source.write_bytes(b'VERSION = "0.1.0"\n')
        self.assertEqual(before,self.campaign.identity('rubygems',['must-not-launch']))

    def test_rust_source_mutation_changes_prelaunch_identity_and_restores(self):
        target=Path(self.folder.name)/'active/edit'
        source=target/'src/crates/edit/src/document.rs';source.parent.mkdir(parents=True)
        original=b'fn save() { reviewed_write(); }\n';source.write_bytes(original)
        (target/'task-owned.json').write_text('{}')
        binary=target/'target/reviewed.exe';binary.parent.mkdir();binary.write_bytes(b'reviewed binary')
        (target/'build.json').write_text(json.dumps({'binary_relative_path':'target/reviewed.exe'}))
        before=self.campaign.identity('edit',['must-not-launch'])
        source.write_bytes(b'fn save() { wrong_write(); }\n')
        self.assertNotEqual(before,self.campaign.identity('edit',['must-not-launch']))
        source.write_bytes(original)
        self.assertEqual(before,self.campaign.identity('edit',['must-not-launch']))
        binary.write_bytes(b'changed binary')
        self.assertNotEqual(before,self.campaign.identity('edit',['must-not-launch']))
        binary.write_bytes(b'reviewed binary')
        self.assertEqual(before,self.campaign.identity('edit',['must-not-launch']))

    def test_new_recorder_fixture_bytes_are_bound_before_export_exists(self):
        package=Path(self.folder.name)/'record-package';fixture=package/'fixture';fixture.mkdir(parents=True)
        selected=fixture/'selected.txt';selected.write_bytes(b'reviewed fixture\n')
        argv=['playtestr','record','--output',str(package/'not-created.json'),'--fixture','fixture','--','trusted-target']
        before=self.campaign.identity('fixture',argv)
        selected.write_bytes(b'changed fixture\n')
        self.assertNotEqual(before,self.campaign.identity('fixture',argv))
        selected.write_bytes(b'reviewed fixture\n')
        self.assertEqual(before,self.campaign.identity('fixture',argv))

    def test_identified_success_requires_launch_but_setup_failure_is_counted(self):
        identity=uuid.uuid4().hex
        for event in ['started','identified']:
            self.campaign.append(dict(id=identity,event=event,project='fixture',label='control'))
        self.campaign.append(dict(id=identity,event='finished',project='fixture',label='control',
            category='passed',exit_code=0,harness_cleanup='harness_process_reaped'))
        with self.assertRaisesRegex(ValueError,'launch'):
            self.campaign.attempts()
        setup=Campaign(Path(self.folder.name)/'prelaunch-timeout')
        identity=uuid.uuid4().hex
        for event in ['started','identified']:
            setup.append(dict(id=identity,event=event,project='fixture',label='bounded-setup'))
        setup.append(dict(id=identity,event='finished',project='fixture',label='bounded-setup',
            category='harness_timeout',exit_code=None,harness_cleanup='not_started'))
        self.assertEqual(len(setup.attempts()),1)


if __name__ == '__main__':
    unittest.main()
