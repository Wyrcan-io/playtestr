import json
from pathlib import Path
import tempfile
import unittest

from readiness_evidence import Campaign, RAW


class HygenIdentityTests(unittest.TestCase):
    def test_actual_dist_dependency_launcher_and_node_mutations_are_bound(self):
        RAW.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            campaign = Campaign(Path(directory))
            target = Path(directory) / 'active/hygen'
            candidates = [target / 'src/dist/ops/add.js', target / 'src/node_modules/enquirer/index.js',
                          target / 'bin/hygen', target / 'runtime/node']
            for path in candidates:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'reviewed original\n')
            (target / 'task-owned.json').write_text('{}')
            (target / 'src/package.json').write_text('{}')
            (target / 'src/yarn.lock').write_text('# frozen lock\n')
            (target / 'runtime.json').write_text(json.dumps(dict(node=str(candidates[-1]))))
            before = campaign.identity('hygen', ['must-not-launch'])
            for path in candidates:
                with self.subTest(path=path.relative_to(target)):
                    path.write_bytes(b'actual changed executable bytes\n')
                    self.assertNotEqual(before['sha256'], campaign.identity('hygen', ['must-not-launch'])['sha256'])
                    path.write_bytes(b'reviewed original\n')
                    self.assertEqual(before, campaign.identity('hygen', ['must-not-launch']))


if __name__ == '__main__':
    unittest.main()
