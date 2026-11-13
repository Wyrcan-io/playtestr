"""Contract-shape controls for fzy's native PTY scenario matrix."""
import base64
import tempfile
import unittest
from pathlib import Path

import next20_fzy_scenarios as fzy
from next20_fzy_build import ARCHIVE_SHA256, SOURCE_PROVENANCE, file_map, remove_generated_outputs


class FzyScenarioTests(unittest.TestCase):
    def test_contract_has_eight_normal_and_twelve_edge_cases(self):
        rows = fzy.cases()
        self.assertEqual(len(rows), 20)
        self.assertEqual(sum(row["kind"] == "normal" for row in rows), 8)
        self.assertEqual(sum(row["kind"] == "edge" for row in rows), 12)
        self.assertEqual(len({row["id"] for row in rows}), 20)

    def test_each_case_ends_with_an_exact_exit_assertion(self):
        for row in fzy.cases():
            self.assertEqual(row["actions"][-2], {"exit": row["expected_exit"]}, row["id"])
            self.assertEqual(row["actions"][-1]["state"]["path"], "result.txt", row["id"])

    def test_cancel_cases_require_exact_failure_status(self):
        rows = {row["id"]: row for row in fzy.cases()}
        for identity, key in (("E01", "Escape"), ("E02", "CtrlC"),
                              ("E03", "CtrlD"), ("E04", "CtrlG")):
            with self.subTest(case=identity):
                self.assertEqual(rows[identity]["expected_exit"], 1)
                self.assertEqual(rows[identity]["actions"][-2], {"exit": 1})
                self.assertIn({"key": key}, rows[identity]["actions"])

    def test_selection_outputs_are_observed_after_terminal_teardown(self):
        rows = {row["id"]: row for row in fzy.cases()}
        for identity, expected in (("N01", b"apple\n"), ("N05", b"blue\n"),
                                   ("N07", b"apple\n"), ("E07", "café 雪\n".encode()),
                                   ("E08", b"blue\n"), ("E09", b"item03\n")):
            with self.subTest(case=identity):
                actions = rows[identity]["actions"]
                self.assertEqual(actions[-1]["state"]["bytes_base64"],
                                 base64.b64encode(expected).decode("ascii"))
                self.assertTrue(any("expect" in action for action in actions[:-2]),
                                "selection must have positive rendered evidence")

    def test_nul_fixture_and_utf8_fixture_are_byte_exact(self):
        rows = {row["id"]: row for row in fzy.cases()}
        self.assertEqual(rows["E08"]["fixture"], b"amber\0blue\0")
        self.assertEqual(rows["E07"]["fixture"], "café 雪\nplain\n".encode("utf-8"))
        self.assertEqual(rows["E08"]["fixture_path"], "choices.bin")

    def test_shell_adapter_only_redirects_input_and_execs_target(self):
        for row in fzy.cases():
            self.assertTrue(row["command"].startswith("exec fzy "), row["id"])
            self.assertIn(" < ", row["command"], row["id"])
            self.assertIn(" > result.txt", row["command"], row["id"])
            self.assertNotIn(";", row["command"], row["id"])

    def test_native_clean_removes_only_known_compiler_dependency_and_dsym_outputs(self):
        with tempfile.TemporaryDirectory(prefix="fzy-clean-controls-") as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "test").mkdir()
            (root / "src/keep.c").write_text("pinned source", encoding="utf-8")
            pristine = file_map(root)[0]
            (root / "test/fzytest.d").write_text("compiler dependency", encoding="utf-8")
            (root / "deps/theft").mkdir(parents=True)
            (root / "deps/theft/theft.d").write_text("dependency", encoding="utf-8")
            (root / "test/fzytest.dSYM/Contents/Resources/DWARF").mkdir(parents=True)
            (root / "test/fzytest.dSYM/Contents/Resources/DWARF/fzytest").write_bytes(b"debug symbols")
            removed = remove_generated_outputs(root, pristine)
            self.assertIn("test/fzytest.d", {row["path"] for row in removed})
            self.assertIn("test/fzytest.dSYM", {row["path"] for row in removed})
            self.assertEqual(file_map(root)[0], pristine)

    def test_native_clean_refuses_unrecognized_build_output(self):
        with tempfile.TemporaryDirectory(prefix="fzy-clean-refusal-") as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "src/keep.c").write_text("pinned source", encoding="utf-8")
            pristine = file_map(root)[0]
            unexpected = root / "unexpected.bin"
            unexpected.write_bytes(b"keep me")
            with self.assertRaisesRegex(ValueError, "unexpected files"):
                remove_generated_outputs(root, pristine)
            self.assertTrue(unexpected.exists())

    def test_native_build_provenance_is_declared_and_pinned(self):
        import json

        provenance = json.loads(SOURCE_PROVENANCE.read_text(encoding="utf-8"))
        self.assertEqual(provenance["project"], "fzy")
        self.assertEqual(provenance["pin"], fzy.PIN)
        self.assertEqual(provenance["source_archive_sha256"], ARCHIVE_SHA256)
        self.assertEqual(provenance["source_file_count"], 45)


if __name__ == "__main__":
    unittest.main()
