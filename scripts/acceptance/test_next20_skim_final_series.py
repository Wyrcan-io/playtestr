"""Pure contract-profile checks for Skim's frozen rc.6 final series."""
import copy
import json
from pathlib import Path
import unittest

from next20_skim_final_series import BATCHES, CASES, transform_contract


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT/'docs/validation/runner-readiness-next-twenty-project-pass/skim'


class SkimFinalSeriesTests(unittest.TestCase):
    def contract(self, case):
        base = json.loads((PACKAGE/'scenario-declaration-v5.json').read_text(encoding='utf-8'))
        rows = {row['id']: row for row in base['scenarios']}
        revision = json.loads((PACKAGE/'scenario-declaration-v6.json').read_text(encoding='utf-8'))
        rows.update({row['id']: row for row in revision['replacements']})
        self.assertIn(case, rows)
        return json.loads((PACKAGE/rows[case]['contract']).read_text(encoding='utf-8'))

    def test_profile_is_twelve_declared_batches_for_all_twenty_cases(self):
        self.assertEqual([row['id'] for row in BATCHES], list(range(12)))
        self.assertEqual(len(CASES), 20)
        self.assertEqual(len(set(CASES)), 20)
        declaration = json.loads((PACKAGE/'final-series-declaration-native-exit-v9.json').read_text(encoding='utf-8'))
        self.assertEqual(declaration['batches'], BATCHES)
        self.assertEqual(declaration['scenario_ids'], CASES)

    def test_viewport_profile_preserves_declared_edge_boundaries(self):
        ordinary = self.contract('N01')
        changed = transform_contract(4, 'N01', ordinary)
        self.assertEqual((changed['width'], changed['height']), (ordinary['width']+10, ordinary['height']+2))
        for case in ('E03', 'E04', 'E05', 'E06'):
            original = self.contract(case)
            self.assertEqual(transform_contract(4, case, original), original)

    def test_viewport_profile_preserves_exact_wrapping_snapshot(self):
        original = self.contract('N08')
        self.assertEqual(transform_contract(4, 'N08', original), original)

    def test_segmented_input_is_ordered_and_semantically_identical(self):
        original = self.contract('N02')
        changed = transform_contract(7, 'N02', original)
        before = [s['text'] for s in original['steps'] if set(s) == {'text'}]
        after = [s['text'] for s in changed['steps'] if set(s) == {'text'}]
        self.assertEqual(''.join(after), ''.join(before))
        self.assertTrue(all(len(value) <= 3 for value in after))
        self.assertEqual([s for s in original['steps'] if 'key' in s],
                         [s for s in changed['steps'] if 'key' in s])

    def test_small_height_and_tight_startup_are_scoped(self):
        n01 = self.contract('N01')
        self.assertEqual(transform_contract(10, 'N01', n01)['height'], 12)
        e03 = self.contract('E03')
        self.assertEqual(transform_contract(11, 'E03', e03).get('startup_timeout_ms', 0), 0)
        self.assertEqual(transform_contract(11, 'N01', n01)['startup_timeout_ms'], 2000)

    def test_profile_does_not_mutate_frozen_source_contracts(self):
        original = self.contract('N01')
        snapshot = copy.deepcopy(original)
        for batch in range(12):
            transform_contract(batch, 'N01', original)
        self.assertEqual(original, snapshot)


if __name__ == '__main__':
    unittest.main()
