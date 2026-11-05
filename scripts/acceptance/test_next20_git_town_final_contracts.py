"""Tests for the frozen Git Town final-journal scenario alias."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from next20_check import DOC
from next20_git_town_faults import FAULTS, PIN
from next20_git_town_final_contracts import materialize_scenario_alias


class GitTownFinalContractTests(unittest.TestCase):
    def test_scenario_alias_matches_and_records_frozen_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            payload = b'{"cases": [], "schema_version": 1}\n'
            source = target / 'scenarios-native-exit-v2.json'
            source.write_bytes(payload)
            copied = {source.name: hashlib.sha256(payload).hexdigest()}

            materialize_scenario_alias(target, copied)

            alias = target / 'scenarios.json'
            self.assertEqual(alias.read_bytes(), payload)
            self.assertEqual(copied['scenarios.json'], hashlib.sha256(payload).hexdigest())

    def test_scenario_alias_refuses_changed_frozen_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            (target / 'scenarios-native-exit-v2.json').write_bytes(b'{"cases": []}\n')
            with self.assertRaisesRegex(ValueError, 'source or alias differs'):
                materialize_scenario_alias(target, {'scenarios-native-exit-v2.json': '0' * 64})
            self.assertFalse((target / 'scenarios.json').exists())

    def test_final_fault_declaration_matches_v4_candidate_inputs(self):
        package = DOC / 'git-town'
        declaration = json.loads(
            (package / 'fault-declaration-v5.json').read_text(encoding='utf-8'))
        catalog = json.loads(
            (package / 'scenario-catalog-v4.json').read_text(encoding='utf-8'))
        declared = {item['id']: item for item in declaration['declared_faults']}
        self.assertEqual(declaration['source_pin'], PIN)
        self.assertEqual(declaration['scenario_catalog'], 'scenario-catalog-v4.json')
        self.assertEqual(set(declared), {fault['id'] for fault in FAULTS})
        for fault in FAULTS:
            self.assertEqual(declared[fault['id']]['unchanged_spec'], fault['spec'])
            self.assertEqual(declared[fault['id']]['spec_sha256'],
                             hashlib.sha256((package / fault['spec']).read_bytes()).hexdigest())
        catalog_specs = {case['spec']: case['spec_sha256'] for case in catalog['scenarios']}
        for fault in FAULTS:
            self.assertEqual(catalog_specs[fault['spec']], declared[fault['id']]['spec_sha256'])


if __name__ == '__main__':
    unittest.main()
