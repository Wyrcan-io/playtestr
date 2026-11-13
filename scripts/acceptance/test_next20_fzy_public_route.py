"""Contract checks for fzy's public authoring and maintenance route."""
import base64
import json
import unittest

from next20_check import DOC


class FzyPublicRouteTests(unittest.TestCase):
    def test_first_use_and_maintenance_fixtures_have_exact_output_bytes(self):
        declaration = json.loads((DOC / "fzy/public-route-declaration-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(base64.b64decode(declaration["first_use_fixture_base64"], validate=True),
                         b"apple\nbanana\n")
        self.assertEqual(base64.b64decode(declaration["maintenance_fixture_base64"], validate=True),
                         b"banana\napple\n")
        self.assertEqual(base64.b64decode(declaration["first_use_output_base64"], validate=True), b"apple\n")
        self.assertEqual(base64.b64decode(declaration["maintenance_output_base64"], validate=True),
                         b"banana\n")

    def test_route_controls_bind_review_replay_save_and_exact_state_update(self):
        declaration = json.loads((DOC / "fzy/public-route-declaration-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(declaration["record_controls"], [
            "/expect apple", "/key Enter", "/exit 0", "/file result.txt",
            "/review", "/replay", "/save"])
        self.assertEqual(declaration["maintenance_controls"], [
            "/update-state 4", "/review", "/replay", "/save"])
        self.assertEqual(declaration["diagnosis"], {
            "mutate": "the exact result.txt byte expectation",
            "failure_category": "state_assertion_failure", "failed_step": 4})

    def test_public_route_keeps_saved_state_and_human_credit_zero(self):
        declaration = json.loads((DOC / "fzy/public-route-declaration-v1.json").read_text(encoding="utf-8"))
        self.assertIn("does not demonstrate target-managed persistent state",
                      declaration["saved_state_scope"])
        self.assertEqual(declaration["human_participants"], 0)
        self.assertEqual(declaration["admission_credit"], 0)


if __name__ == "__main__":
    unittest.main()
