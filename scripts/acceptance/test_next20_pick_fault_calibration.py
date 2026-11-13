"""Contract checks for Pick's post-freeze source-fault calibration."""
import base64
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import next20_pick_fault_calibration as calibration


class PickFaultCalibrationTests(unittest.TestCase):
    def test_declaration_has_three_distinct_frozen_fault_oracles(self):
        declaration, _, freeze, rows = calibration.load_declaration()
        self.assertEqual(declaration["expected_attempts"], 18)
        self.assertEqual(declaration["hosts"], ["linux", "darwin"])
        self.assertEqual(freeze["version"], "v0.4.0-rc.8")
        self.assertEqual({fault["id"] for fault, _, _ in rows}, {"F01", "F02", "F03"})
        self.assertEqual({scenario["id"] for _, _, scenario in rows}, {"E11", "E02", "N01"})
        for fault, _, scenario in rows:
            spec = json.loads((calibration.DOC / scenario["spec_path"]).read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(spec["steps"]), fault["expected_failure_step"])
            self.assertTrue(fault["expected_failure_categories"])

    def test_each_patch_is_single_declared_source_substitution(self):
        _, _, _, rows = calibration.load_declaration()
        for fault, _, _ in rows:
            with self.subTest(fault=fault["id"]):
                patch = (calibration.DOC / fault["patch"]).read_text(encoding="utf-8")
                old = base64.b64decode(fault["mutation_old_base64"], validate=True)
                new = base64.b64decode(fault["mutation_new_base64"], validate=True)
                removed = [line[1:] for line in patch.splitlines() if line.startswith("-") and not line.startswith("---")]
                added = [line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")]
                self.assertEqual(len(removed), 1)
                self.assertEqual(len(added), 1)
                self.assertIn(old.decode("utf-8").rstrip("\n"), patch)
                self.assertIn(new.decode("utf-8").rstrip("\n"), patch)
                self.assertEqual(len(fault["baseline_source_sha256"]), 64)
                self.assertEqual(len(fault["mutated_source_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
