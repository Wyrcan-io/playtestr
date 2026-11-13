"""Contract checks for Pick's exact-candidate public authoring route."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import next20_pick_public_route as route


class PickPublicRouteTests(unittest.TestCase):
    def test_first_use_records_offscreen_selection_and_exact_exit_without_handwritten_spec(self):
        declaration = json.loads(route.DECLARATION.read_text(encoding="utf-8"))
        self.assertEqual(route.RECORDER_CONTROLS, declaration["record_controls"])
        self.assertEqual(route.RECORDER_CONTROLS[:6], [
            "/expect item00", "/snapshot initial-menu.txt", "/key End",
            "/expect tail-choice", "/key Enter", "/exit 0",
        ])
        self.assertEqual(route.INITIAL_FIXTURE.splitlines()[0], b"item00")
        self.assertEqual(route.INITIAL_FIXTURE.splitlines()[-1], b"tail-choice")
        self.assertEqual(len(route.INITIAL_FIXTURE.splitlines()), 30)
        self.assertEqual(declaration["admission_credit"], 0)

    def test_selective_maintenance_updates_the_terminal_screen_oracle(self):
        declaration = json.loads(route.DECLARATION.read_text(encoding="utf-8"))
        self.assertEqual(route.MAINTENANCE_CONTROLS, declaration["maintenance_controls"])
        self.assertEqual(len([line for line in route.MAINTENANCE_CONTROLS if line.startswith("/replace")]), 1)
        self.assertIn('{"expect":"revised-tail-choice"}', route.MAINTENANCE_CONTROLS[0])
        self.assertEqual(route.MAINTENANCE_CONTROLS,
                         ['/replace 4 {"expect":"revised-tail-choice"}', "/review", "/replay", "/save"])

    def test_route_binds_the_private_candidate_and_keeps_human_status_separate(self):
        declaration = json.loads(route.DECLARATION.read_text(encoding="utf-8"))
        self.assertEqual(declaration["candidate_series"], "native-exit-v3")
        self.assertEqual(declaration["candidate"], "v0.4.0-rc.8")
        self.assertEqual(declaration["hosts"], ["linux", "darwin"])
        self.assertEqual(declaration["human_participants"], 0)
        self.assertEqual(declaration["usability_status"], "unmeasured")


if __name__ == "__main__":
    unittest.main()
