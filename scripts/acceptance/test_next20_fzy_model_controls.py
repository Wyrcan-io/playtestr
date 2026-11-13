"""Semantic regression checks for fzy's reconstructed qualification model."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import next20_fzy_model_controls as model


class FzyModelControlsTests(unittest.TestCase):
    def test_reconstructs_two_native_cells_without_credit_overclaim(self):
        value = model.build_model()
        model.validate(value)
        self.assertEqual(value["totals"]["ordinary_attempts"], 480)
        self.assertEqual(value["totals"]["fault_phases"], 18)
        self.assertEqual(value["totals"]["public_route_attempts"], 16)
        self.assertEqual(value["totals"]["technical_route_attempts"], 16)
        self.assertEqual(value["admission_credit"], 0)

    def test_rejects_all_declared_semantic_corruptions(self):
        value = model.build_model()
        rejected = model.corruption_controls(value)
        self.assertEqual(len(rejected), 17)
        self.assertIn("self_admission", rejected)
        self.assertIn("candidate", rejected)
        self.assertIn("cleanup", rejected)

    def test_candidate_audit_inputs_are_digest_pinned(self):
        values, _, _ = model.read_inputs()
        self.assertEqual(values["development"]["ordinary_passes"], 40)
        self.assertEqual(values["final"]["ordinary_passes"], 480)
        self.assertEqual(values["fault"]["audited_phases"], 18)


if __name__ == "__main__":
    unittest.main()
