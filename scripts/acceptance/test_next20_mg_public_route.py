"""Focused validation of the mg public-route evidence boundary."""
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

from next20_mg_pilot import ensure_executable
from next20_mg_public_route import report_result


class PublicRouteReportTests(unittest.TestCase):
    def write_report(self, root, result):
        path = Path(root) / "report.json"
        path.write_text(json.dumps({"results": [result]}), encoding="utf-8")
        return path

    def test_passing_report_requires_positive_steps_and_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.write_report(root, {
                "status": "passed",
                "workspace": {"cleaned": True},
                "cleanup": {"confirmed_exited": True},
                "steps": [{"status": "passed"}],
            })
            self.assertEqual(report_result(path, "passed")["status"], "passed")

    def test_passing_report_rejects_unconfirmed_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.write_report(root, {
                "status": "passed",
                "workspace": {"cleaned": False},
                "cleanup": {"confirmed_exited": True},
                "steps": [{"status": "passed"}],
            })
            with self.assertRaisesRegex(ValueError, "cleanup"):
                report_result(path, "passed")

    def test_passing_report_rejects_missing_positive_step(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.write_report(root, {
                "status": "passed",
                "workspace": {"cleaned": True},
                "cleanup": {"confirmed_exited": True},
                "steps": [{"status": "failed"}],
            })
            with self.assertRaisesRegex(ValueError, "non-passing step"):
                report_result(path, "passed")

    def test_wrong_result_count_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "report.json"
            path.write_text('{"results": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "one ordinary result"):
                report_result(path, "passed")

    @unittest.skipIf(os.name == "nt", "execute-bit restoration applies to native Unix targets")
    def test_artifact_permission_restore_is_local_and_byte_preserving(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "mg"
            path.write_bytes(b"owned target bytes")
            path.chmod(0o644)
            before = path.read_bytes()
            mode = ensure_executable(path)
            self.assertEqual(mode, {"mode_before": "0o644", "mode_after": "0o744"})
            self.assertTrue(path.stat().st_mode & stat.S_IXUSR)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
