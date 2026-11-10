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
        self.assertEqual(spec["steps"][7], {"expect": "Wrote "})
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True),
                         b"BASELINE\nAPPENDED")
        self.assertEqual(len(data), len((DOC / "mg/n02-edit-append.json").read_bytes()))
        self.assertEqual(spec["steps"][-3], {"key": "CtrlC"})

    def test_n03_uses_meta_percent_and_checks_query_replace_result(self):
        path, data, spec, fixture = load_contract(DOC / "mg/n03-query-replace.json")
        self.assertEqual(path.name, "n03-query-replace.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "notes.txt"])
        self.assertEqual((fixture / "notes.txt").read_bytes(), b"one needle and needle.\n")
        self.assertEqual(spec["steps"][0], {"expect": "one needle and needle."})
        self.assertIn({"expect": "Query replace:"}, spec["steps"])
        self.assertIn({"expect": "Query replace needle with:"}, spec["steps"])
        self.assertIn({"expect": "Replaced 2 occurrences"}, spec["steps"])
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True),
                         b"one TOKEN and TOKEN.\n")
        self.assertEqual(len(data), len((DOC / "mg/n03-query-replace.json").read_bytes()))

    def test_n04_cuts_a_marked_word_and_yanks_it_at_end(self):
        path, data, spec, fixture = load_contract(DOC / "mg/n04-cut-yank.json")
        self.assertEqual(path.name, "n04-cut-yank.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "notes.txt"])
        self.assertEqual((fixture / "notes.txt").read_bytes(), b"alpha beta gamma\n")
        self.assertEqual(sum(1 for s in spec["steps"] if s == {"key": "CtrlF"}), 10)
        self.assertIn({"key": "CtrlSpace"}, spec["steps"])
        self.assertIn({"key": "CtrlW"}, spec["steps"])
        self.assertIn({"key": "CtrlY"}, spec["steps"])
        yank = spec["steps"].index({"key": "CtrlY"})
        self.assertEqual(spec["steps"][yank - 2:yank + 1],
                         [{"key": "CtrlE"}, {"text": " "}, {"key": "CtrlY"}])
        self.assertIn({"expect": "alpha  gamma"}, spec["steps"])
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True),
                         b"alpha  gamma beta\n")
        self.assertEqual(len(data), len((DOC / "mg/n04-cut-yank.json").read_bytes()))

    def test_n05_undo_and_redo_of_a_deletion(self):
        path, data, spec, fixture = load_contract(DOC / "mg/n05-undo-redo.json")
        self.assertEqual(path.name, "n05-undo-redo.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "notes.txt"])
        self.assertEqual((fixture / "notes.txt").read_bytes(), b"seed changed\n")
        self.assertEqual(sum(1 for s in spec["steps"] if s == {"key": "CtrlX"}), 5)
        self.assertEqual(sum(1 for s in spec["steps"] if s == {"text": "u"}), 3)
        self.assertEqual(sum(1 for s in spec["steps"] if s == {"key": "Backspace"}), 8)
        self.assertEqual([s for s in spec["steps"] if "expect" in s],
                         [{"expect": "seed changed"}, {"expect": "seed"},
                          {"expect": "seed changed"}, {"expect": "seed changed"},
                          {"expect": "seed"}, {"expect": "Wrote "}])
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True),
                         b"seed\n")
        self.assertEqual(len(data), len((DOC / "mg/n05-undo-redo.json").read_bytes()))

    def test_n06_saves_as_a_second_file_and_preserves_the_original(self):
        path, data, spec, fixture = load_contract(DOC / "mg/n06-save-as.json")
        self.assertEqual(path.name, "n06-save-as.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "notes.txt"])
        original = b"source remains\n"
        self.assertEqual((fixture / "notes.txt").read_bytes(), original)
        steps = spec["steps"]
        save_as = steps.index({"key": "CtrlW"})
        self.assertEqual(steps[save_as - 1], {"key": "CtrlX"})
        self.assertEqual(steps[save_as + 1:save_as + 5],
                         [{"expect": "Write file:"}, {"key": "CtrlU"},
                          {"text": "notes-copy.txt"}, {"key": "Enter"}])
        self.assertEqual([s["state"]["path"] for s in steps if "state" in s],
                         ["notes.txt", "notes-copy.txt"])
        self.assertEqual([base64.b64decode(s["state"]["bytes_base64"], validate=True)
                          for s in steps if "state" in s], [original, original])
        self.assertEqual(len(data), len((DOC / "mg/n06-save-as.json").read_bytes()))

    def test_n07_switches_buffers_and_preserves_both_files(self):
        path, data, spec, fixture = load_contract(DOC / "mg/n07-buffer-switch.json")
        self.assertEqual(path.name, "n07-buffer-switch.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "first.txt"])
        self.assertEqual((fixture / "first.txt").read_bytes(), b"first buffer identity\n")
        self.assertEqual((fixture / "second.txt").read_bytes(), b"second buffer identity\n")
        steps = spec["steps"]
        visit = steps.index({"key": "CtrlF"})
        self.assertEqual(steps[visit - 1], {"key": "CtrlX"})
        self.assertEqual(steps[visit + 1:visit + 5],
                         [{"expect": "Find file:"}, {"key": "CtrlU"},
                          {"text": "second.txt"}, {"key": "Enter"}])
        switch = steps.index({"text": "b"})
        self.assertEqual(steps[switch - 1], {"key": "CtrlX"})
        self.assertEqual(steps[switch + 1:switch + 4],
                         [{"expect": "Switch to buffer"}, {"text": "first.txt"},
                          {"key": "Enter"}])
        self.assertEqual([s["state"]["path"] for s in steps if "state" in s],
                         ["first.txt", "second.txt"])
        self.assertEqual([base64.b64decode(s["state"]["bytes_base64"], validate=True)
                          for s in steps if "state" in s],
                         [b"first buffer identity\n", b"second buffer identity\n"])
        self.assertEqual(len(data), len((DOC / "mg/n07-buffer-switch.json").read_bytes()))


if __name__ == "__main__":
    unittest.main()
