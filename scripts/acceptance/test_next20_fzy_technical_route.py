"""Contract checks for fzy's exact-candidate technical authoring route."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import next20_fzy_technical_route as route


class FzyTechnicalRouteTests(unittest.TestCase):
    def test_route_is_native_and_tied_to_audited_source_and_candidate(self):
        self.assertEqual(route.PROJECT, "fzy")
        self.assertEqual(route.PIN, "34b88869d022e861da4846c4463aea3ddfb3ff30")
        self.assertEqual(route.HOSTS, {"linux": "Linux", "darwin": "Darwin"})
        receipt = route.PUBLIC_RECEIPT.read_text(encoding="utf-8")
        self.assertIn('"status": "passed-and-independently-audited"', receipt)

    def test_exact_input_output_fixture_and_declared_credit_boundary(self):
        import json
        import base64
        declaration = json.loads(route.DECLARATION.read_text(encoding="utf-8"))
        self.assertEqual(base64.b64decode(declaration["first_use_fixture_base64"]), b"apple\nbanana\n")
        self.assertEqual(base64.b64decode(declaration["first_use_output_base64"]), b"apple\n")
        self.assertEqual(declaration["admission_credit"], 0)

    def test_route_labels_cover_all_technical_milestones(self):
        import inspect
        source = inspect.getsource(route.main_async)
        for label in ("fzy-technical-suite-selection", "fzy-technical-manual-edit-selected-test",
                      "fzy-technical-machine-to-html-report", "fzy-technical-version-2-before-migration",
                      "fzy-technical-version-3-after-migration", "fzy-technical-suffix-rerecord",
                      "fzy-technical-suffix-rerecord-ordinary-test"):
            self.assertIn(label, source)


if __name__ == "__main__":
    unittest.main()
