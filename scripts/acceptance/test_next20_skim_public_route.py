"""Focused immutability regression for Skim's public maintenance route."""
import json
import tempfile
import unittest
from pathlib import Path

from next20_skim_public_route import prepare_maintenance_spec


class SkimPublicRouteTests(unittest.TestCase):
    def test_maintenance_writes_a_distinct_spec_and_preserves_first_use(self):
        with tempfile.TemporaryDirectory() as directory:
            maintenance = Path(directory)
            original = maintenance/'selection.json'
            baseline = {
                'version': 3,
                'command': ['bin/sk.exe', '--query=cedar'],
                'steps': [{'expect': 'cedar'}, {'snapshot': 'selected.txt'}],
                'snapshots': ['snapshots/selected.txt'],
            }
            original.write_text(json.dumps(baseline), encoding='utf-8')
            original_bytes = original.read_bytes()

            maintained, approved = prepare_maintenance_spec(maintenance, original)

            self.assertEqual(maintained.name, 'selection-maintenance.json')
            self.assertTrue(maintained.is_file())
            self.assertEqual(original.read_bytes(), original_bytes)
            self.assertEqual(json.loads(maintained.read_text(encoding='utf-8')), approved)
            self.assertEqual(approved['command'], ['bin/sk.exe', '--query=amber'])
            self.assertEqual(approved['steps'], [{'expect': 'amber'}, {'snapshot': 'selected.txt'}])

    def test_maintenance_refuses_ambiguous_or_missing_query(self):
        with tempfile.TemporaryDirectory() as directory:
            maintenance = Path(directory)
            original = maintenance/'selection.json'
            cases = [
                {'command': ['bin/sk.exe'], 'steps': [{'expect': 'cedar'}]},
                {'command': ['--query=cedar', '--query=cedar'], 'steps': [{'expect': 'cedar'}]},
                {'command': ['--query=cedar'], 'steps': [{'expect': 'violet'}]},
                {'command': ['--query=cedar'], 'steps': [{'expect': 'cedar'}, {'expect': 'cedar'}]},
            ]
            for value in cases:
                original.write_text(json.dumps(value), encoding='utf-8')
                with self.subTest(value=value), self.assertRaisesRegex(
                        ValueError, 'cannot identify the exact query and result expectation'):
                    prepare_maintenance_spec(maintenance, original)
                self.assertFalse((maintenance/'selection-maintenance.json').exists())


if __name__ == '__main__':
    unittest.main()
