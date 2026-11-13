"""Contract checks for Pick's exact-candidate public authoring route."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import next20_pick_public_route as route


class PickPublicRouteTests(unittest.TestCase):
    def test_first_use_records_query_selection_and_exact_exit_without_handwritten_spec(self):
        declaration = json.loads(route.DECLARATION.read_text(encoding="utf-8"))
        self.assertEqual(route.RECORDER_CONTROLS, declaration["record_controls"])
        self.assertEqual(route.RECORDER_CONTROLS[:6], [
            "/expect item00", "/snapshot initial-menu.txt", '/text "item29"',
            "/expect item29", "/key Enter", "/exit 0",
        ])
        self.assertEqual(route.INITIAL_FIXTURE.splitlines()[0], b"item00")
        self.assertEqual(route.INITIAL_FIXTURE.splitlines()[-1], b"item29")
        self.assertEqual(len(route.INITIAL_FIXTURE.splitlines()), 30)
        self.assertEqual(declaration["admission_credit"], 0)

    def test_selective_maintenance_pairs_query_with_both_screen_oracles(self):
        declaration = json.loads(route.DECLARATION.read_text(encoding="utf-8"))
        self.assertEqual(route.MAINTENANCE_CONTROLS, declaration["maintenance_controls"])
        self.assertEqual(len([line for line in route.MAINTENANCE_CONTROLS if line.startswith("/replace")]), 2)
        self.assertIn('{"text":"item28"}', route.MAINTENANCE_CONTROLS[0])
        self.assertIn('{"expect":"item28"}', route.MAINTENANCE_CONTROLS[1])
        self.assertEqual(route.MAINTENANCE_CONTROLS[-3:], ["/review", "/replay", "/save"])

    def test_route_binds_the_private_candidate_and_keeps_human_status_separate(self):
        declaration = json.loads(route.DECLARATION.read_text(encoding="utf-8"))
        self.assertEqual(declaration["candidate_series"], "native-exit-v3")
        self.assertEqual(declaration["candidate"], "v0.4.0-rc.8")
        self.assertEqual(declaration["hosts"], ["linux", "darwin"])
        self.assertEqual(declaration["human_participants"], 0)
        self.assertEqual(declaration["usability_status"], "unmeasured")


if __name__ == "__main__":
    unittest.main()
