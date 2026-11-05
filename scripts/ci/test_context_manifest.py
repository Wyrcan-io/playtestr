import json
from pathlib import Path
import tempfile
import unittest
from context_manifest import create


class ContextTests(unittest.TestCase):
    def test_exact_contract_identity_and_restricted_pr(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "target").write_bytes(b"target")
            (root / "spec.json").write_text(json.dumps(dict(command=["./target"], steps=[{"expect": "ready"}])))
            (root / "selected.txt").write_text("Selected 1 specs:\nspec.json\n")
            event = {"number": 1, "pull_request": {"head": {"sha": "a" * 40}, "base": {"sha": "b" * 40}}}
            env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_SHA": "c" * 40}
            data = create(root / "selected.txt", root / "target", event, env, "c" * 40, root)
            manifest = json.loads(data)
            self.assertEqual(manifest["checkout_strategy"], "github-merge")
            self.assertEqual(manifest["selected_specs"], ["spec.json"])
            self.assertIn("target", manifest["target_binaries"])
            with self.assertRaises(ValueError):
                create(root / "selected.txt", root / "target", event, env, "d" * 40, root)
            env["GITHUB_EVENT_NAME"] = "pull_request_target"
            with self.assertRaises(ValueError):
                create(root / "selected.txt", root / "target", event, env, "c" * 40, root)

    def test_empty_selection_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selection.txt"
            path.write_text("Selected 0 specs:\n")
            with self.assertRaises(ValueError):
                create(path, path, {}, {}, "a" * 40, path.parent)

    def test_push_uses_exact_checkout_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "target").write_bytes(b"target")
            (root / "spec.json").write_text(json.dumps(dict(command=["./target"], steps=[{"expect": "ready"}])))
            (root / "selected.txt").write_text("Selected 1 specs:\nspec.json\n")
            revision = "c" * 40
            env = {"GITHUB_EVENT_NAME": "push", "GITHUB_SHA": revision}
            manifest = json.loads(create(root / "selected.txt", root / "target", {}, env, revision, root))
            self.assertEqual(manifest["event"], "push")
            self.assertEqual(manifest["checkout_strategy"], "exact-checkout")
            self.assertIsNone(manifest["head_sha"])
            self.assertIsNone(manifest["base_sha"])
            env["GITHUB_SHA"] = "d" * 40
            with self.assertRaises(ValueError):
                create(root / "selected.txt", root / "target", {}, env, revision, root)


if __name__ == "__main__":
    unittest.main()
