"""Frozen-catalog checks for mg's exact-candidate final native series."""
import json
import unittest

from next20_check import DOC
from next20_mg_final_series import BATCHES, CASES
from readiness_evidence import sha256


class MgFinalSeriesTests(unittest.TestCase):
    def test_declared_catalog_is_eight_normal_and_twelve_canonical_edges(self):
        declaration = json.loads((DOC / "mg/final-qualification-declaration-v2.json").read_text())
        ids = {case for case, _ in CASES}
        self.assertEqual(len(ids), 20)
        self.assertEqual(len(CASES), 21)
        self.assertEqual(sum(case.startswith("N") for case, _ in CASES), 8)
        self.assertEqual(sum(case.startswith("E") for case, _ in CASES), 13)
        self.assertEqual(declaration["canonical_scenario_count"], 20)
        self.assertEqual(declaration["contract_executions_per_batch"], len(CASES))
        self.assertEqual(declaration["expected_total_contract_executions"], 504)

    def test_every_declared_native_batch_has_one_unique_variation(self):
        declaration = json.loads((DOC / "mg/final-qualification-declaration-v2.json").read_text())
        self.assertEqual(len(BATCHES), 12)
        self.assertEqual([row["index"] for row in declaration["batches"]], list(range(12)))
        self.assertEqual([row["variation"] for row in declaration["batches"]], BATCHES)
        self.assertEqual({cell["host"] for cell in declaration["native_cells"]}, {"linux", "darwin"})
        self.assertEqual({cell["architecture"] for cell in declaration["native_cells"]}, {"amd64", "arm64"})

    def test_case_list_matches_frozen_contract_hashes(self):
        declaration = json.loads((DOC / "mg/final-qualification-declaration-v2.json").read_text())
        first = json.loads((DOC / "mg/final-qualification-declaration-v1.json").read_text())
        self.assertEqual(declaration["supersedes_sha256"],
                         sha256(DOC / "mg/final-qualification-declaration-v1.json"))
        self.assertEqual(first["status"], "declared-not-yet-qualified")
        frozen = {(row["id"], row["contract"].rsplit("/", 1)[-1]) for row in declaration["scenarios"]}
        self.assertEqual(set(CASES), frozen)


if __name__ == "__main__":
    unittest.main()
