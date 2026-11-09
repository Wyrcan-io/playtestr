"""Contract checks for the first frozen-candidate mg PTY pilot."""
import base64
import json
from pathlib import Path
import tempfile
import unittest

from next20_check import DOC
from next20_mg_pilot import EXPECTED_BYTES
from next20_mg_pilot_cleanup import inventory


class MgPilotContractTests(unittest.TestCase):
    def test_n01_requires_visible_text_save_confirmation_exit_and_exact_bytes(self):
        spec = json.loads((DOC / "mg/pilot-n01.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["version"], 3)
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "pilot.txt"])
        self.assertEqual(spec["workspace"]["fixture"], "fixtures/pilot-n01")
        steps = spec["steps"]
        self.assertEqual([next(iter(step)) for step in steps], [
            "text", "key", "expect", "key", "key", "expect", "key", "key", "exit", "state"])
        self.assertEqual(steps[2]["expect"], "MG_PTY_PILOT_RC6")
        self.assertEqual(steps[5]["expect"], "Wrote pilot.txt")
        self.assertEqual(steps[8]["exit"], 0)
        state = steps[9]["state"]
        self.assertEqual(state["path"], "pilot.txt")
        self.assertEqual(state["kind"], "file")
        self.assertEqual(base64.b64decode(state["bytes_base64"], validate=True), EXPECTED_BYTES)

    def test_cleanup_inventory_counts_only_regular_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "runner.bin").write_bytes(b"binary")
            (root / "receipt.json").write_text("{}", encoding="utf-8")
            self.assertEqual(inventory(root), (2, 8))


if __name__ == "__main__":
    unittest.main()
