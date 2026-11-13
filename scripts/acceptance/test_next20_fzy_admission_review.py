"""Reviewable package-boundary checks for fzy's exact-candidate admission."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import next20_fzy_admission_review as review


class FzyAdmissionReviewTests(unittest.TestCase):
    def test_complete_rc8_package_passes_without_closing_campaign_gate(self):
        receipt = review.build_review()
        review.validate(receipt)
        self.assertEqual(receipt["project_admission_credit"], 1)
        self.assertEqual(receipt["campaign_final_gate_credit"], 0)
        self.assertEqual(receipt["failed_attempts_retained_zero_credit"], 11)

    def test_review_rejects_weakening_required_claims(self):
        receipt = review.build_review()
        mutations = [
            lambda r: r.update(final_ordinary_passes=479),
            lambda r: r.update(distinct_detected_source_faults=2),
            lambda r: r.update(semantic_corruptions_rejected=0),
            lambda r: r.update(saved_state_coverage_credit=1),
            lambda r: r.update(delivered_ci="passed"),
            lambda r: r.update(campaign_final_gate_credit=1),
            lambda r: r.update(project_admission_credit=0),
        ]
        for mutate in mutations:
            corrupted = copy.deepcopy(receipt)
            mutate(corrupted)
            with self.assertRaises(ValueError):
                review.validate(corrupted)


if __name__ == "__main__":
    unittest.main()
