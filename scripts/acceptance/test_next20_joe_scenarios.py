"""Regression checks for JOE scenario cleanup receipts."""
import unittest

from next20_joe_scenarios import process_tree_cleanup


class JoeScenarioCleanupTests(unittest.TestCase):
    def test_nonzero_expected_fault_uses_bounded_command_cleanup_receipt(self):
        commands = [{"exit_code": 1,
                     "process_tree_cleanup": "process group absent; no owned descendants remain"}]
        self.assertEqual(process_tree_cleanup(None, commands), commands[0]["process_tree_cleanup"])

    def test_successful_command_cleanup_receipt_takes_precedence(self):
        result = {"process_tree_cleanup": "no live processes remain; owned tree absent"}
        commands = [{"process_tree_cleanup": "incomplete"}]
        self.assertEqual(process_tree_cleanup(result, commands), result["process_tree_cleanup"])

    def test_missing_cleanup_evidence_stays_missing(self):
        self.assertIsNone(process_tree_cleanup(None, []))


if __name__ == "__main__":
    unittest.main()
