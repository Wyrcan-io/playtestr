"""Contract checks for Pick's exact-candidate technical authoring route."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import next20_pick_technical_route as route


class PickTechnicalRouteTests(unittest.TestCase):
    def test_fixture_has_unique_query_and_exact_description_column(self):
        rows = route.FIXTURE.decode("ascii").splitlines()
        self.assertEqual(len(rows), 30)
        self.assertEqual(rows[-1], "tail-choice:Tail unique description")
        self.assertEqual(route.PIN, "caae95938359b2e814b3e7406f396f486c9d99fb")

    def test_native_route_is_scoped_to_supported_host_matrix(self):
        self.assertEqual(route.HOSTS, {"linux": "Linux", "darwin": "Darwin"})
        self.assertEqual(route.PROJECT, "pick")


if __name__ == "__main__":
    unittest.main()
