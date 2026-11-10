"""Contract selection and deterministic hashing checks for mg fault calibration."""
import tempfile
from pathlib import Path
import unittest

from next20_mg_fault_calibration import MUTATIONS, inventory, sha_map


class MgFaultCalibrationTests(unittest.TestCase):
    def test_each_fault_uses_a_distinct_frozen_contract(self):
        self.assertEqual(set(MUTATIONS), {
            "save-no-write", "delete-byte-corruption", "readonly-edit-accepted", "undo-delete-omitted"})
        self.assertEqual({row["contract"] for row in MUTATIONS.values()}, {
            "n02-edit-append.json", "n03-query-replace.json", "e06-readonly-buffer.json",
            "n05-undo-redo.json"})
        self.assertTrue(MUTATIONS["save-no-write"]["requires_state_failure"])

    def test_source_map_hash_is_order_independent_and_sensitive_to_bytes(self):
        self.assertEqual(sha_map({"a": "one", "b": "two"}),
                         sha_map({"b": "two", "a": "one"}))
        self.assertNotEqual(sha_map({"a": "one"}), sha_map({"a": "changed"}))

    def test_cleanup_inventory_counts_regular_files_and_bounds_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "file").write_bytes(b"mg")
            (root / "child").mkdir()
            (root / "child" / "nested").write_bytes(b"source")
            self.assertEqual(inventory(root), (2, 8))


if __name__ == "__main__":
    unittest.main()
