import base64
import unittest

from next20_percol_scenarios import cases, expected_spec


class PercolScenarioContractTests(unittest.TestCase):
    def test_contract_is_twenty_distinct_normal_and_edge_cases(self):
        rows = cases()
        self.assertEqual(20, len(rows))
        self.assertEqual(20, len({row["id"] for row in rows}))
        self.assertEqual(8, sum(row["kind"] == "normal" for row in rows))
        self.assertEqual(12, sum(row["kind"] == "edge" for row in rows))

    def test_each_case_has_exact_captured_output_and_exit(self):
        for row in cases():
            with self.subTest(row=row["id"]):
                state = row["actions"][-1]["state"]
                self.assertEqual("result.txt", state["path"])
                self.assertEqual(row["expected_stdout_base64"], state["bytes_base64"])
                self.assertEqual(row["expected_stdout"], base64.b64decode(state["bytes_base64"]))
                self.assertIn({"exit": row["expected_exit"]}, row["actions"][:-1])

    def test_shell_adapter_is_limited_to_input_output_and_exec(self):
        for row in cases():
            with self.subTest(row=row["id"]):
                spec = expected_spec(row)
                self.assertTrue(row["command"].startswith(
                    'exec "$PERCOL_PYTHON" "$PERCOL_SOURCE/bin/percol"'))
                self.assertIn("> result.txt", row["command"])
                self.assertTrue(" < " in row["command"] or row["fixture_path"] in row["command"])
                self.assertNotIn("&&", row["command"])
                self.assertNotIn(";", row["command"])
                self.assertEqual(["PATH", "PERCOL_PYTHON", "PERCOL_SOURCE", "PYTHONPATH",
                                  "DYLD_LIBRARY_PATH"], spec["inherit_env"])
                self.assertEqual("1", spec["env"]["PYTHONDONTWRITEBYTECODE"])
                self.assertNotIn("PERCOL_PYTHON", spec["env"])

    def test_risk_cases_cover_real_percol_controls(self):
        rows = {row["id"]: row for row in cases()}
        self.assertIn({"key": "CtrlSpace"}, rows["N06"]["actions"])
        self.assertIn("--caret-position=0", rows["E01"]["options"])
        self.assertIn("--query=art", rows["N03"]["options"])
        self.assertEqual("Match a substring query", rows["N03"]["title"])
        self.assertIn("--query=apx", rows["N07"]["options"])
        self.assertIn({"key": "Backspace"}, rows["N07"]["actions"])
        self.assertEqual({"expect": "apx"}, rows["N07"]["actions"][0])
        self.assertEqual(("--eager",), tuple(rows["E06"]["options"]))
        self.assertIn({"expect": "1/2"}, rows["E06"]["actions"])
        self.assertEqual(("--query=missing",), tuple(rows["E05"]["options"]))
        self.assertNotIn({"text": "missing"}, rows["E05"]["actions"])
        self.assertEqual(("--case-sensitive",), tuple(rows["E07"]["options"]))
        self.assertEqual({"expect": "Blue"}, rows["E07"]["actions"][0])
        self.assertIn({"expect": "1/1"}, rows["E07"]["actions"])
        self.assertIn("--match-method=regex", rows["E08"]["options"])
        self.assertIn("--reverse", rows["E09"]["options"])
        self.assertNotIn(" < ", rows["E11"]["command"])
        self.assertIn("choices.txt", rows["E11"]["command"])


if __name__ == "__main__":
    unittest.main()
