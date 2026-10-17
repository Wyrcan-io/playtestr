import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from readiness_evidence import RAW
import readiness_rubygems_profiles as profiles


class BundlerProfileTests(unittest.TestCase):
    def test_exact_native_suite_keeps_paged_resize_and_excludes_receipts(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            root=Path(folder)
            runtime=root/'active/rubygems/runtime.json';runtime.parent.mkdir(parents=True)
            runtime.write_text(json.dumps({'native_platform':'x86_64-linux'}))
            with patch.object(profiles,'RAW',root):profiles.main()
            suite=root/'rubygems/host-contracts'
            specs=list(suite.rglob('*.json'));self.assertEqual(len(specs),20)
            self.assertFalse((suite/'reviewed-contract-freeze.json').exists())
            self.assertTrue((suite/'build-fixture/dist').is_dir())
            self.assertEqual(list((suite/'build-fixture/dist').iterdir()),[])
            resize=json.loads((suite/'edge-resize-collision.json').read_text())
            self.assertIn('--paginate',resize['env']['THOR_DIFF'])
            self.assertEqual(len([s for s in resize['steps'] if 'resize' in s]),2)
            for path in specs:self.assertTrue((suite/json.loads(path.read_text())['workspace']['fixture']).is_dir())


if __name__=='__main__':unittest.main()
