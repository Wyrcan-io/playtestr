import json
from pathlib import Path
import tempfile
import unittest

from readiness_cleanup_plop import verify_retained_report_cleanup
from readiness_evidence import RAW


class RetainedCleanupReportTests(unittest.TestCase):
    def test_legacy_v2_report_cleanup_is_checked_in_explicit_mode(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory);report=root/'legacy-results.json'
            for confirmed in [True,False]:
                report.write_text(json.dumps(dict(report_version=2,results=[dict(cleanup=dict(
                    attempted=True,confirmed_exited=confirmed),workspace=dict(prepared=True,cleaned=True))])))
                if confirmed:verify_retained_report_cleanup(root,[report])
                else:
                    with self.assertRaisesRegex(RuntimeError,'unconfirmed process cleanup'):
                        verify_retained_report_cleanup(root,[report])

    def test_explicit_report_selection_does_not_parse_template_json_but_rejects_bad_report(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory);report=root/'results.json'
            (root/'template.json').write_text('{{ intentionally unrendered template }}')
            report.write_text(json.dumps(dict(report_version=3,results=[dict(
                cleanup=dict(attempted=True,confirmed_exited=True),workspace=dict(prepared=True,cleaned=True))])))
            verify_retained_report_cleanup(root,[report])
            report.write_text('truncated actual report')
            with self.assertRaisesRegex(RuntimeError,'invalid retained JSON'):
                verify_retained_report_cleanup(root,[report])

    def fixture(self, root, snapshot='saved-config.json'):
        (root/'snapshots').mkdir()
        (root/'spec.json').write_text(json.dumps(dict(version=3, command=['trusted-target'],
            steps=[dict(snapshot=snapshot)])))
        (root/'snapshots/saved-config.json').write_text('Current remotes:\n\ndemo local\n')
        (root/'ordinary-results.json').write_text(json.dumps(dict(report_version=3, results=[
            dict(cleanup=dict(attempted=True, confirmed_exited=True), workspace=dict(prepared=True, cleaned=True))])))

    def test_plain_text_snapshot_with_json_suffix_is_not_a_report(self):
        RAW.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory)
            self.fixture(root)
            verify_retained_report_cleanup(root)

    def test_malformed_actual_report_is_still_rejected(self):
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory)
            self.fixture(root)
            (root/'ordinary-results.json').write_text('truncated report')
            with self.assertRaisesRegex(RuntimeError, 'invalid retained JSON'):
                verify_retained_report_cleanup(root)

    def test_failed_actual_cleanup_is_still_rejected(self):
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory)
            self.fixture(root)
            (root/'ordinary-results.json').write_text(json.dumps(dict(report_version=3, results=[
                dict(cleanup=dict(attempted=True, confirmed_exited=False))])))
            with self.assertRaisesRegex(RuntimeError, 'unconfirmed process cleanup'):
                verify_retained_report_cleanup(root)

    def test_snapshot_cannot_hide_a_report_outside_its_baseline_directory(self):
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory)
            self.fixture(root, '../ordinary-results.json')
            with self.assertRaisesRegex(RuntimeError, 'snapshot reference escapes'):
                verify_retained_report_cleanup(root)


if __name__ == '__main__':
    unittest.main()
