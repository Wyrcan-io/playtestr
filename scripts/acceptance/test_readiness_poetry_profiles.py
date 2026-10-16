import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from readiness_evidence import RAW
import readiness_poetry_profiles


class PoetryProfileTests(unittest.TestCase):
    def test_native_selection_excludes_fault_receipts(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            with patch.object(readiness_poetry_profiles,'RAW',Path(folder)):
                readiness_poetry_profiles.main()
            suite=Path(folder)/'poetry/host-contracts'
            specs=list(suite.rglob('*.json'))
            self.assertEqual(len(specs),20)
            self.assertFalse((suite/'faults').exists())
            for path in specs:
                spec=json.loads(path.read_text())
                self.assertEqual(spec['version'],3)
                self.assertTrue(spec['steps'])
                self.assertTrue((path.parent/spec['workspace']['fixture']).is_dir())


if __name__=='__main__':unittest.main()
