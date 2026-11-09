"""Public-contract checks for pinned mg scenario development."""
import base64
from pathlib import Path
import unittest

from next20_check import DOC
from next20_mg_scenario import load_contract


class MgScenarioContractTests(unittest.TestCase):
    def test_n02_is_a_public_version_three_edit_save_contract(self):
        path, data, spec, fixture = load_contract(DOC / "mg/n02-edit-append.json")
        self.assertEqual(path.name, "n02-edit-append.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "notes.txt"])
        self.assertEqual(spec["workspace"]["fixture"], "fixtures/n02-edit-append")
        self.assertEqual((fixture / "notes.txt").read_bytes(), b"BASELINE\n")
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True),
                         b"BASELINE\nAPPENDED")
        self.assertEqual(len(data), len((DOC / "mg/n02-edit-append.json").read_bytes()))
        self.assertEqual(spec["steps"][-3], {"key": "CtrlC"})


if __name__ == "__main__":
    unittest.main()
