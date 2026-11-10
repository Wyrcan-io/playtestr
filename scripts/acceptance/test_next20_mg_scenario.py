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

    def test_n08_edits_and_saves_utf8_with_wide_character(self):
        path, data, spec, fixture = load_contract(DOC / "mg/n08-utf8-wide.json")
        self.assertEqual(path.name, "n08-utf8-wide.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "notes.txt"])
        self.assertEqual(spec["env"]["LANG"], "C.UTF-8")
        self.assertEqual(spec["env"]["LC_CTYPE"], "C.UTF-8")
        initial = "caf\u00e9 wide: \u754c\n".encode("utf-8")
        expected = "caf\u00e9 wide: \u754c \u03bb\n".encode("utf-8")
        self.assertEqual((fixture / "notes.txt").read_bytes(), initial)
        self.assertEqual(spec["steps"][0], {"expect": "caf\u00e9 wide: \u754c"})
        self.assertEqual(spec["steps"][2], {"text": " \u03bb"})
        self.assertEqual(spec["steps"][3], {"expect": "caf\u00e9 wide: \u754c \u03bb"})
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True), expected)
        self.assertEqual(len(data), len((DOC / "mg/n08-utf8-wide.json").read_bytes()))

    def test_e01_saves_an_unchanged_zero_byte_file(self):
        path, data, spec, fixture = load_contract(DOC / "mg/e01-empty-save.json")
        self.assertEqual(path.name, "e01-empty-save.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "empty.txt"])
        self.assertEqual((fixture / "empty.txt").read_bytes(), b"")
        self.assertEqual(spec["steps"][0], {"expect": "empty.txt"})
        self.assertEqual(spec["steps"][1:4],
                         [{"key": "CtrlX"}, {"key": "CtrlS"},
                          {"expect": "(No changes need to be saved)"}])
        self.assertEqual(spec["steps"][-1],
                         {"state": {"path": "empty.txt", "kind": "file", "bytes_base64": ""}})
        self.assertEqual(len(data), len((DOC / "mg/e01-empty-save.json").read_bytes()))

    def test_e02_refuses_movement_past_buffer_boundaries(self):
        path, data, spec, fixture = load_contract(DOC / "mg/e02-buffer-boundaries.json")
        self.assertEqual(path.name, "e02-buffer-boundaries.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "notes.txt"])
        self.assertEqual((fixture / "notes.txt").read_bytes(), b"x")
        self.assertEqual(spec["steps"][:7], [
            {"expect": "x"}, {"key": "CtrlB"}, {"expect": "Beginning of buffer"},
            {"key": "CtrlF"}, {"expect": "x"}, {"key": "CtrlF"},
            {"expect": "End of buffer"},
        ])
        self.assertEqual(spec["steps"][7:10], [
            {"key": "CtrlB"}, {"key": "CtrlB"}, {"expect": "Beginning of buffer"},
        ])
        self.assertEqual(spec["steps"][-1],
                         {"state": {"path": "notes.txt", "kind": "file", "bytes_base64": "eA=="}})
        self.assertEqual(len(data), len((DOC / "mg/e02-buffer-boundaries.json").read_bytes()))

    def test_e03_backspace_at_line_start_joins_previous_line(self):
        path, data, spec, fixture = load_contract(DOC / "mg/e03-backspace-join.json")
        self.assertEqual(path.name, "e03-backspace-join.json")
        self.assertEqual(spec["command"], ["mg", "-S", "-n", "notes.txt"])
        self.assertEqual((fixture / "notes.txt").read_bytes(), b"first\nsecond\n")
        self.assertEqual(spec["steps"][:6], [
            {"expect": "first"}, {"expect": "second"}, {"key": "CtrlN"},
            {"key": "CtrlA"}, {"key": "Backspace"}, {"expect": "firstsecond"},
        ])
        self.assertEqual(spec["steps"][8], {"expect": "Wrote "})
        self.assertEqual(spec["steps"][-1], {
            "state": {"path": "notes.txt", "kind": "file", "bytes_base64": "Zmlyc3RzZWNvbmQK"}
        })
        self.assertEqual(len(data), len((DOC / "mg/e03-backspace-join.json").read_bytes()))

    def test_e04_edits_a_line_longer_than_the_viewport(self):
        path, data, spec, fixture = load_contract(DOC / "mg/e04-extended-line.json")
        self.assertEqual(path.name, "e04-extended-line.json")
        self.assertEqual(spec["width"], 80)
        self.assertEqual((fixture / "notes.txt").read_bytes(), b"0123456789" * 12 + b"END\n")
        self.assertEqual(spec["steps"][:5], [
            {"expect": "0123456789"}, {"key": "CtrlE"}, {"expect": "END"},
            {"text": "!"}, {"expect": "END!"},
        ])
        expected = b"0123456789" * 12 + b"END!\n"
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True), expected)
        self.assertEqual(len(data), len((DOC / "mg/e04-extended-line.json").read_bytes()))

    def test_e05_deletes_one_complete_wide_utf8_character(self):
        path, data, spec, fixture = load_contract(DOC / "mg/e05-wide-backspace.json")
        self.assertEqual(path.name, "e05-wide-backspace.json")
        self.assertEqual(spec["env"]["LANG"], "C.UTF-8")
        self.assertEqual(spec["env"]["LC_CTYPE"], "C.UTF-8")
        self.assertEqual((fixture / "notes.txt").read_bytes(), "A\u754cB\n".encode("utf-8"))
        self.assertEqual(spec["steps"][:5], [
            {"expect": "A\u754cB"}, {"key": "CtrlF"}, {"key": "CtrlF"},
            {"key": "Backspace"}, {"expect": "AB"},
        ])
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True), b"AB\n")
        self.assertEqual(len(data), len((DOC / "mg/e05-wide-backspace.json").read_bytes()))

    def test_e06_read_only_buffer_rejects_edit_and_preserves_bytes(self):
        path, data, spec, fixture = load_contract(DOC / "mg/e06-readonly-buffer.json")
        self.assertEqual(path.name, "e06-readonly-buffer.json")
        original = b"protected sample\n"
        self.assertEqual((fixture / "notes.txt").read_bytes(), original)
        self.assertEqual(spec["steps"][1:8], [
            {"key": "CtrlX"}, {"key": "CtrlQ"}, {"text": "X"},
            {"expect": "Buffer is read only"}, {"key": "CtrlX"},
            {"key": "CtrlS"}, {"expect": "(No changes need to be saved)"},
        ])
        self.assertEqual(base64.b64decode(spec["steps"][-1]["state"]["bytes_base64"], validate=True), original)
        self.assertEqual(len(data), len((DOC / "mg/e06-readonly-buffer.json").read_bytes()))

    def test_e07_save_as_missing_parent_leaves_no_partial_path(self):
        path, data, spec, fixture = load_contract(DOC / "mg/e07-missing-parent.json")
        self.assertEqual(path.name, "e07-missing-parent.json")
        self.assertEqual((fixture / "notes.txt").read_bytes(), b"original content\n")
        self.assertEqual(spec["steps"][1:7], [
            {"key": "CtrlX"}, {"key": "CtrlW"}, {"expect": "Write file"},
            {"text": "missing/child.txt"}, {"key": "Enter"},
            {"expect": "Cannot open file for writing"},
        ])
        self.assertEqual(spec["steps"][-2:], [
            {"state": {"path": "notes.txt", "kind": "file", "bytes_base64": "b3JpZ2luYWwgY29udGVudAo="}},
            {"state": {"path": "missing", "kind": "absent"}},
        ])
        self.assertEqual(len(data), len((DOC / "mg/e07-missing-parent.json").read_bytes()))

if __name__ == "__main__":
    unittest.main()
