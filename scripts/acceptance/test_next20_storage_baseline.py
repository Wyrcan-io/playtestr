"""Storage preflights use immutable receipts instead of walking the old raw tree."""
import json
from pathlib import Path
import tempfile
import unittest

from next20_storage_baseline import prior_campaign_usage
from readiness_evidence import sha256


class PriorCampaignStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.docs = self.root / 'docs/validation/runner-readiness-next-twenty-project-pass'
        self.old = self.root / 'docs/validation/runner-readiness-ten-project-pass'
        self.docs.mkdir(parents=True)
        self.old.mkdir(parents=True)
        self.checkpoint = self.docs / 'storage-checkpoint-v42.json'
        self.closing = self.old / 'closing-storage.json'
        self.current = self.docs / 'storage-checkpoint-v43.json'
        self.checkpoint.write_text(json.dumps({'actual_bytes': {
            'new_campaign_raw': 700, 'combined_raw': 1300}}), encoding='utf-8')
        self.closing.write_text(json.dumps({'retained_bytes': 120, 'curated_bytes': 30,
                                           'active_projects': []}), encoding='utf-8')
        self.current.write_text(json.dumps({'prior_campaign_snapshots': {
            'v42_sha256': sha256(self.checkpoint),
            'first_ten_closing_storage_sha256': sha256(self.closing),
            'v42_new_raw_bytes': 700, 'v42_combined_raw_bytes': 1300,
            'first_ten_raw_bytes': 600, 'first_ten_retained_bytes': 120,
            'first_ten_curated_bytes': 30}}), encoding='utf-8')

    def tearDown(self):
        self.temporary.cleanup()

    def test_returns_receipt_bound_prior_sizes_without_raw_path(self):
        self.assertEqual(prior_campaign_usage(self.docs, self.root),
                         {'raw': 600, 'retained': 120, 'curated': 30})

    def test_rejects_stale_or_changed_prior_storage_receipts(self):
        value = json.loads(self.current.read_text(encoding='utf-8'))
        value['prior_campaign_snapshots']['first_ten_raw_bytes'] = 601
        self.current.write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'baseline differs'):
            prior_campaign_usage(self.docs, self.root)


if __name__ == '__main__':
    unittest.main()
