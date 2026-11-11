"""Focused validation of the mg public-route evidence boundary."""
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

from next20_mg_pilot import ensure_executable
from next20_mg_oracle_calibration import TARGET_SHA, report_result as oracle_report_result
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


class OracleCalibrationReportTests(unittest.TestCase):
    def test_target_identity_is_a_full_sha256(self):
        self.assertEqual(len(TARGET_SHA), 64)

    def write_report(self, root, result):
        path = Path(root) / "report.json"
        path.write_text(json.dumps({"runner_version": "v0.4.0-rc.6", "results": [result]}), encoding="utf-8")
        return path

    def base_result(self, status, state_status):
        result = {"status": status, "cleanup": {"confirmed_exited": True},
                  "workspace": {"cleaned": True}, "steps": [{"action": "state", "status": state_status}]}
        if status == "failed":
            result["failure"] = {"category": "state_assertion_failure"}
        return result

    def test_positive_state_oracle_requires_exit_and_workspace_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.write_report(root, self.base_result("passed", "passed"))
            self.assertEqual(oracle_report_result(path, "passed", "passed")["status"], "passed")

    def test_negative_state_oracle_requires_final_state_failure_category(self):
        with tempfile.TemporaryDirectory() as root:
            result = self.base_result("failed", "failed")
            path = self.write_report(root, result)
            self.assertEqual(oracle_report_result(path, "failed", "failed")["status"], "failed")
            result["failure"]["category"] = "assertion_timeout"
            path = self.write_report(root, result)
            with self.assertRaisesRegex(ValueError, "state-oracle rejection"):
                oracle_report_result(path, "failed", "failed")


if __name__ == "__main__":
    unittest.main()
