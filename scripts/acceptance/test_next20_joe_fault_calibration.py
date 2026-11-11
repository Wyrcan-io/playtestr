"""Static preflight checks for the frozen JOE source-fault set."""
import hashlib
import json
import unittest

from next20_joe_fault_calibration import FAULT_DECLARATION, FAULT_DECLARATIONS, load_faults


class JoeFaultCalibrationTests(unittest.TestCase):
    def test_fault_set_and_manifests_match_the_frozen_declaration(self):
        declaration, faults = load_faults()
        self.assertEqual(set(faults), {
            "joe-forward-delete-noop",
            "joe-save-content-truncated",
            "joe-save-exit-disabled",
        })
        self.assertEqual(len({fault["risk_dimension"] for fault in faults.values()}), 3)
        readback_path = FAULT_DECLARATION.parent / "fault-declaration-source-readback-v2.json"
        readback = json.loads(readback_path.read_text(encoding="utf-8"))
        self.assertEqual(readback["fault_declaration_sha256"], hashlib.sha256(FAULT_DECLARATION.read_bytes()).hexdigest())
        readback_rows = {row["fault_id"]: row for row in readback["faults"]}
        for fault in faults.values():
            manifest = json.loads((FAULT_DECLARATION.parent / fault["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["id"], fault["id"])
            self.assertEqual(manifest["mutated_source_sha256"], fault["mutated_source_sha256"])
            self.assertNotEqual(fault["mutation_old_base64"], fault["mutation_new_base64"])
            self.assertEqual(readback_rows[fault["id"]]["declared_mutated_sha256"], fault["mutated_source_sha256"])
            self.assertTrue(readback_rows[fault["id"]]["exact_pin_bytes_verified"])
        self.assertEqual(declaration["prior_attempts"]["workflow_run"], "43042122414")

    def test_rc7_fault_declaration_binds_the_same_three_pinned_mutations(self):
        declaration, faults = load_faults("native-exit-v2")
        freeze = json.loads((FAULT_DECLARATION.parents[1] / "replacement-candidate-freeze-native-exit-v2.json").read_text())
        readback_path = FAULT_DECLARATIONS["native-exit-v2"].parent / "fault-declaration-source-readback-v3.json"
        readback = json.loads(readback_path.read_text(encoding="utf-8"))
        self.assertEqual(declaration["candidate"], freeze["version"])
        self.assertEqual(declaration["scenario_declaration"], "joe/scenario-declaration-v4.json")
        self.assertEqual(readback["fault_declaration_sha256"], hashlib.sha256(FAULT_DECLARATIONS["native-exit-v2"].read_bytes()).hexdigest())
        self.assertEqual(set(faults), {"joe-forward-delete-noop", "joe-save-content-truncated", "joe-save-exit-disabled"})


if __name__ == "__main__":
    unittest.main()
