import json
from pathlib import Path
import tempfile
import unittest

from readiness_evidence import Campaign, RAW


class RcloneIdentityTests(unittest.TestCase):
    def test_compiled_app_source_lock_compiler_and_binary_are_bound(self):
        RAW.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            campaign = Campaign(Path(directory))
            target = Path(directory) / 'active/rclone'
            files = [target / 'src/fs/config/configfile/configfile.go', target / 'src/go.sum',
                     target / 'bin/rclone', target / 'toolchain/go/bin/go']
            for path in files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'reviewed original\n')
            (target / 'task-owned.json').write_text('{}')
            (target / 'src/go.mod').write_text('module github.com/rclone/rclone\n')
            (target / 'runtime.json').write_text(json.dumps(dict(go=str(files[-1]))))
            (target / 'build.json').write_text(json.dumps(dict(binary_relative_path='bin/rclone')))
            (target / 'toolchain/sdk.json').write_text('{}')
            original = campaign.identity('rclone', ['must-not-launch'])
            for path in files:
                with self.subTest(path=path.relative_to(target)):
                    path.write_bytes(b'actual changed input\n')
                    self.assertNotEqual(original['sha256'], campaign.identity('rclone', ['must-not-launch'])['sha256'])
                    path.write_bytes(b'reviewed original\n')
                    self.assertEqual(original, campaign.identity('rclone', ['must-not-launch']))


if __name__ == '__main__':
    unittest.main()
