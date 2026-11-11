"""Regression checks for JOE scenario cleanup receipts."""
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from next20_joe_scenarios import DOC, process_tree_cleanup, verify_declarations


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

    def test_rc7_development_and_final_declarations_match_exact_frozen_candidate(self):
        root = DOC / "joe"
        for name, phase, reps in (("scenario-attempt-v8.json", "scenario-development", 1),
                                  ("scenario-attempt-v7.json", "final-qualification", 12)):
            attempt = root / name
            verify_declarations(attempt, phase, "native-exit-v2")
            data = json.loads(attempt.read_text(encoding="utf-8"))
            self.assertEqual(data["candidate"], "v0.4.0-rc.7")
            self.assertEqual(data["series"], "native-exit-v2")
            self.assertEqual({cell["repetitions"] for cell in data["native_cells"]}, {reps})

    def test_rc7_declaration_rejects_candidate_hash_tampering(self):
        attempt = DOC / "joe" / "scenario-attempt-v7.json"
        data = json.loads(attempt.read_text(encoding="utf-8"))
        data["candidate_archive_sha256"]["linux"] = "0" * 64
        with TemporaryDirectory() as temp:
            path = Path(temp) / "attempt.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_declarations(path, "final-qualification", "native-exit-v2")


if __name__ == "__main__":
    unittest.main()
