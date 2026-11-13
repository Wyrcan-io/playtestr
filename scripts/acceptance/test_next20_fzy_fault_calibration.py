"""Contract checks for fzy's real-source-fault calibration."""
import json
from pathlib import Path
import tempfile
import unittest

import next20_fzy_fault_calibration as calibration


class FzyFaultCalibrationTests(unittest.TestCase):
    def test_each_phase_uses_a_unique_bounded_cleanup_receipt_window(self):
        windows = {calibration.cleanup_window(fault, phase, host)
                   for fault in ("F01", "F02", "F03")
                   for phase in ("baseline", "fault", "restored")
                   for host in ("linux", "darwin")}
        self.assertEqual(len(windows), 18)
        self.assertTrue(all(len(window) <= 64 and window.startswith("rebuild-")
                            for window in windows))

    def test_three_distinct_reviewed_mutations_bind_public_scenarios(self):
        declaration, scenario, freeze, rows = calibration.load_contract()
        self.assertEqual(declaration["distinct_detected_faults"], 3)
        self.assertEqual(freeze["version"], "v0.4.0-rc.8")
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({fault["source_file"] + fault["mutated_source_sha256"]
                              for fault, _, _ in rows}), 3)
        self.assertEqual({case["id"] for _, case, _ in rows}, {"N01", "N02", "N05"})
        self.assertEqual({fault["id"]: (fault["expected_failure_category"],
                                        fault["expected_failure_step"])
                          for fault, _, _ in rows}, {
                              "F01": ("state_assertion_failure", 4),
                              "F02": ("state_assertion_failure", 6),
                              "F03": ("state_assertion_failure", 4),
                          })
        self.assertTrue(all(spec.is_file() for _, _, spec in rows))
        self.assertEqual(scenario["saved_state_coverage_credit"], 0)

    def test_fault_must_fail_at_the_declared_category_and_step(self):
        fault = {"expected_failure_category": "assertion_timeout",
                 "expected_failure_step": 3}
        report = {"report_version": 3, "runner_version": "v0.4.0-rc.8",
                  "summary": {"total": 1, "failed": 1},
                  "results": [{"status": "failed", "failure": {"category": "assertion_timeout"},
                               "target": {"exited": True, "exit_code": 1},
                               "cleanup": {"confirmed_exited": True},
                               "workspace": {"cleaned": True},
                               "steps": [{"number": 3, "status": "failed"}]}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            _, failed_step, classification = calibration.verify_case_report(path, fault, "fault", 0)
        self.assertEqual(failed_step["number"], 3)
        self.assertEqual(classification, "expected-target-fault-rejection")

    def test_unrelated_failure_cannot_receive_fault_detection_credit(self):
        fault = {"expected_failure_category": "assertion_timeout",
                 "expected_failure_step": 3}
        report = {"report_version": 3, "runner_version": "v0.4.0-rc.8",
                  "summary": {"total": 1, "failed": 1},
                  "results": [{"status": "failed", "failure": {"category": "harness_error"},
                               "target": {"exited": True, "exit_code": 1},
                               "cleanup": {"confirmed_exited": True},
                               "workspace": {"cleaned": True},
                               "steps": [{"number": 3, "status": "failed"}]}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escaped its public scenario"):
                calibration.verify_case_report(path, fault, "fault", 0)

    def test_pristine_and_restored_scenario_must_pass_every_step(self):
        fault = {"expected_failure_category": "state_assertion_failure",
                 "expected_failure_step": 4}
        report = {"report_version": 3, "runner_version": "v0.4.0-rc.8",
                  "summary": {"total": 1, "failed": 0},
                  "results": [{"status": "passed", "failure": None,
                               "target": {"exited": True, "exit_code": 0},
                               "cleanup": {"confirmed_exited": True},
                               "workspace": {"cleaned": True},
                               "steps": [{"number": 1, "status": "passed"}]}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            _, failed_step, classification = calibration.verify_case_report(
                path, fault, "restored", 0)
        self.assertIsNone(failed_step)
        self.assertEqual(classification, "passed")


if __name__ == "__main__":
    unittest.main()
