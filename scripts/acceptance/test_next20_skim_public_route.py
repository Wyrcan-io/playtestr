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

    def test_maintenance_refuses_ambiguous_or_missing_query(self):
        with tempfile.TemporaryDirectory() as directory:
            maintenance = Path(directory)
            original = maintenance/'selection.json'
            for command in (['bin/sk.exe'], ['--query=cedar', '--query=cedar']):
                original.write_text(json.dumps({'command': command}), encoding='utf-8')
                with self.subTest(command=command), self.assertRaisesRegex(
                        ValueError, 'cannot identify the exact query argument'):
                    prepare_maintenance_spec(maintenance, original)
                self.assertFalse((maintenance/'selection-maintenance.json').exists())


if __name__ == '__main__':
    unittest.main()
