import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from readiness_evidence import RAW
import readiness_rubygems_profiles as profiles


class BundlerProfileTests(unittest.TestCase):
    def test_windows_profiles_explicitly_inherit_system_drive_and_preserve_entry_sets(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            root=Path(folder)
            with patch.object(profiles,'RAW',root),patch.object(profiles,'WINDOWS',True):profiles.main()
            suite=root/'rubygems/host-contracts'
            for path in suite.glob('*.json'):
                actual=json.loads(path.read_text());original=json.loads((profiles.PACKAGE/path.name).read_text())
                self.assertIn('SystemDrive',actual['inherit_env'])
                self.assertEqual(actual['steps'],original['steps'])
                if actual['name']=='Bundler N06':
                    self.assertEqual(actual['env']['BUNDLE_FORCE_RUBY_PLATFORM'],'true')
                    self.assertNotIn('--remove-platform',actual['command'])

    def test_exact_native_suite_keeps_paged_resize_and_excludes_receipts(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            root=Path(folder)
            runtime=root/'active/rubygems/runtime.json';runtime.parent.mkdir(parents=True)
            runtime.write_text(json.dumps({'native_platform':'x86_64-linux','installed_ruby_executable':'/usr/bin/ruby3.2'}))
            with patch.object(profiles,'RAW',root):profiles.main()
            suite=root/'rubygems/host-contracts'
            specs=list(suite.rglob('*.json'));self.assertEqual(len(specs),20)
            self.assertFalse((suite/'reviewed-contract-freeze.json').exists())
            self.assertTrue((suite/'build-fixture/dist').is_dir())
            self.assertEqual(list((suite/'build-fixture/dist').iterdir()),[])
            resize=json.loads((suite/'edge-resize-collision.json').read_text())
            self.assertIn('--paginate',resize['env']['THOR_DIFF'])
            self.assertEqual(len([s for s in resize['steps'] if 'resize' in s]),2)
            if not profiles.WINDOWS:
                self.assertEqual(json.loads((suite/'normal-gem.json').read_text())['env']['NO_COLOR'],'1')
            for path in specs:self.assertTrue((suite/json.loads(path.read_text())['workspace']['fixture']).is_dir())


if __name__=='__main__':unittest.main()
