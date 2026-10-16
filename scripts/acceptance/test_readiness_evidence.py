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


if __name__ == '__main__':
    unittest.main()
