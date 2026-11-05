"""Tests for the frozen Git Town final-journal scenario alias."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from next20_check import DOC
from next20_git_town_faults import FAULTS, PIN
from next20_git_town_final_contracts import materialize_scenario_alias, validate_scenario_alias


class GitTownFinalContractTests(unittest.TestCase):
    def test_scenario_alias_matches_and_records_frozen_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            payload = b'{"cases": [], "schema_version": 1}\n'
            source = target / 'scenarios-native-exit-v6.json'
            source.write_bytes(payload)
            copied = {source.name: hashlib.sha256(payload).hexdigest()}

            materialize_scenario_alias(target, copied)

            alias = target / 'scenarios.json'
            self.assertEqual(alias.read_bytes(), payload)
            self.assertEqual(copied['scenarios.json'], hashlib.sha256(payload).hexdigest())

    def test_scenario_alias_refuses_changed_frozen_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            (target / 'scenarios-native-exit-v6.json').write_bytes(b'{"cases": []}\n')
            with self.assertRaisesRegex(ValueError, 'source or alias differs'):
                materialize_scenario_alias(target, {'scenarios-native-exit-v6.json': '0' * 64})
            self.assertFalse((target / 'scenarios.json').exists())

    def test_final_journal_alias_requires_the_current_frozen_scenario_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            alias = target / 'scenarios.json'
            payload = b'{"cases": [], "schema_version": 1}\n'
            alias.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            frozen = {'scenarios-native-exit-v6.json': digest, 'scenarios.json': digest}
            self.assertEqual(validate_scenario_alias('scenarios-native-exit-v6.json', alias, frozen), digest)
            with self.assertRaisesRegex(ValueError, 'alias differs'):
                validate_scenario_alias('scenarios-native-exit-v5.json', alias, frozen)

    def test_final_fault_declaration_matches_v8_candidate_inputs(self):
        package = DOC / 'git-town'
        declaration = json.loads(
            (package / 'fault-declaration-v9.json').read_text(encoding='utf-8'))
        catalog = json.loads(
            (package / 'scenario-catalog-v8.json').read_text(encoding='utf-8'))
        declared = {item['id']: item for item in declaration['declared_faults']}
        self.assertEqual(declaration['source_pin'], PIN)
        self.assertEqual(declaration['scenario_catalog'], 'scenario-catalog-v8.json')
        self.assertEqual(set(declared), {fault['id'] for fault in FAULTS})
        for fault in FAULTS:
            self.assertEqual(declared[fault['id']]['unchanged_spec'], fault['spec'])
            self.assertEqual(declared[fault['id']]['spec_sha256'],
                             hashlib.sha256((package / fault['spec']).read_bytes()).hexdigest())
        catalog_specs = {case['spec']: case['spec_sha256'] for case in catalog['scenarios']}
        for fault in FAULTS:
            self.assertEqual(catalog_specs[fault['spec']], declared[fault['id']]['spec_sha256'])

    def test_frozen_native_cases_have_explicit_process_and_step_bounds(self):
        package = DOC / 'git-town'
        catalog = json.loads((package / 'scenario-catalog-v8.json').read_text(encoding='utf-8'))
        self.assertEqual(len(catalog['scenarios']), 20)
        for case in catalog['scenarios']:
            spec = json.loads((package / case['spec']).read_text(encoding='utf-8'))
            self.assertEqual(spec['timeout_ms'], 20000, case['id'])
            self.assertEqual(spec['run_timeout_ms'], 60000, case['id'])

    def test_final_workflow_deadline_covers_the_full_native_series(self):
        workflow = Path(__file__).parents[2] / '.github' / 'workflows' / 'runner-readiness-next20-git-town-final.yml'
        text = workflow.read_text(encoding='utf-8')
        self.assertIn('--timeout 2400 -- python -B scripts/acceptance/next20_git_town_final_series.py', text)
        self.assertIn('timeout-minutes: 60', text)


if __name__ == '__main__':
    unittest.main()
