"""Pure contract checks for Pick's frozen public scenario package."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import next20_pick_scenarios as pick


class PickScenarioContractTests(unittest.TestCase):
    def test_exact_twenty_normal_and_edge_cases(self):
        rows = pick.cases()
        self.assertEqual(len(rows), 20)
        self.assertEqual(sum(row["kind"] == "normal" for row in rows), 8)
        self.assertEqual(sum(row["kind"] == "edge" for row in rows), 12)
        self.assertEqual(len({row["id"] for row in rows}), 20)

    def test_selection_oracles_cover_cursor_query_output_and_cancellation(self):
        rows = {row["id"]: row for row in pick.cases()}
        self.assertIn({"key": "ArrowDown"}, rows["N02"]["actions"])
        self.assertIn("-q ALP", rows["N04"]["command_line"])
        self.assertIn("pick -d -o", rows["N08"]["command_line"])
        self.assertEqual(rows["E04"]["actions"][1], {"key": "ArrowDown"})
        self.assertNotIn({"text": "second"}, rows["E04"]["actions"])
        self.assertEqual(rows["E02"]["expected_exit"], 1)
        self.assertIn({"key": "CtrlC"}, rows["E02"]["actions"])

    def test_every_scenario_ends_with_an_exact_target_exit_assertion(self):
        for row in pick.cases():
            with self.subTest(case=row["id"]):
                self.assertEqual(row["actions"][-1], {"exit": row["expected_exit"]})

    def test_unicode_and_binary_stream_fixtures_are_exact_utf8(self):
        rows = {row["id"]: row for row in pick.cases()}
        self.assertEqual(rows["E05"]["fixture"], "雪山\n雨\n".encode("utf-8"))
        self.assertEqual(rows["E06"]["fixture"], "café 雪\nplain\n".encode("utf-8"))
        self.assertEqual(rows["E07"]["fixture"], b"alpha\r\nbeta\r\n")
        self.assertEqual(rows["E08"]["fixture"], b"")

    def test_each_case_uses_only_redirection_and_exec_shell_adapter(self):
        for row in pick.cases():
            with self.subTest(case=row["id"]):
                self.assertTrue(row["command_line"].startswith("exec pick "))
                self.assertTrue(row["command_line"].endswith("< choices.txt"))
                self.assertNotIn(";", row["command_line"])
                self.assertNotIn("&&", row["command_line"])


if __name__ == "__main__":
    unittest.main()
