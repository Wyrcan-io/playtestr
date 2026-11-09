"""Bind the Taskell native v3 scenario revision to its exact public contracts."""
import hashlib
import json
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[2]
TASKELL = REPO / "docs/validation/runner-readiness-next-twenty-project-pass/taskell"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TaskellContractRevisionTests(unittest.TestCase):
    def test_v3_declaration_and_scenarios_bind_every_contract(self):
        contracts = TASKELL / "host-contracts-native-exit-v3"
        scenarios_path = contracts / "scenarios.json"
        scenarios = read_json(scenarios_path)
        declaration_path = TASKELL / "final-series-declaration-native-exit-v1-v3.json"
        declaration = read_json(declaration_path)
        revision_path = TASKELL / "scenario-revision-native-exit-v3.json"
        revision = read_json(revision_path)

        self.assertEqual(declaration["canonical_contracts"], contracts.name)
        self.assertEqual(declaration["canonical_test_freeze_sha256"], digest(scenarios_path))
        self.assertEqual(revision["revised_declaration_sha256"], digest(declaration_path))
        self.assertEqual(revision["revised_scenarios_sha256"], digest(scenarios_path))
        self.assertEqual(revision["base_declaration_sha256"],
                         digest(TASKELL / revision["base_declaration"]))
        self.assertEqual(len(scenarios["cases"]), 21)

        for case in scenarios["cases"]:
            spec_path = contracts / case["spec"]
            self.assertEqual(case["spec_sha256"], digest(spec_path), case["id"])
            self.assertEqual(case["canonical_sha256"], digest(spec_path), case["id"])

    def test_only_n04_gains_positive_post_escape_navigation(self):
        old_root = TASKELL / "host-contracts-native-exit-v2"
        new_root = TASKELL / "host-contracts-native-exit-v3"
        old_spec_path = old_root / "taskell-n04-rename-task.json"
        new_spec_path = new_root / "taskell-n04-rename-task.json"
        old = read_json(old_spec_path)
        new = read_json(new_spec_path)

        old_steps = old["steps"]
        new_steps = new["steps"]
        marker = {"expect_not": "INSERT"}
        old_index = old_steps.index(marker)
        new_index = new_steps.index(marker)
        self.assertEqual(new_steps[:new_index], old_steps[:old_index])
        self.assertEqual(new_steps[new_index + 1:new_index + 5], [
            {"text": "j"}, {"expect": "3/3"},
            {"text": "k"}, {"expect": "2/3"},
        ])
        self.assertEqual(new_steps[new_index + 5:], old_steps[old_index + 1:])
        self.assertEqual(new["steps"][-1], old["steps"][-1])

        ignored = {"taskell-n04-rename-task.json", "scenarios.json"}
        old_files = {p.relative_to(old_root).as_posix(): p for p in old_root.rglob("*") if p.is_file()}
        new_files = {p.relative_to(new_root).as_posix(): p for p in new_root.rglob("*") if p.is_file()}
        self.assertEqual(set(new_files), set(old_files))
        for name in old_files.keys() - ignored:
            self.assertEqual(old_files[name].read_bytes(), new_files[name].read_bytes(), name)


if __name__ == "__main__":
    unittest.main()
