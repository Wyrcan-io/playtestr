import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

import report_summary as summary


def report(status="passed", version=1):
    result = {
        "spec_path": "tests/menu.json", "status": status, "duration_ms": 12,
        "cleanup": {"attempted": True, "graceful": True, "forced": False,
                    "confirmed_exited": True}, "evidence": {},
        "steps": [{"number": 1, "action": "exit", "status": "passed", "duration_ms": 12}],
    }
    if status == "failed":
        result["failure"] = {"category": "snapshot_mismatch", "message": "private error"}
    return {"report_version": version, "runner_version": "v0.4.0-rc.3",
            "os": "windows", "arch": "amd64", "results": [result],
            "summary": {"total": 1, **{s: int(s == status) for s in summary.STATUSES}}}


class SummaryTests(unittest.TestCase):
    def test_state_same_execution_identity_and_failure_category(self):
        document=report('failed',3)
        result=document['results'][0]
        result.update(spec_version=3,invocation_id='execution-a',workspace={'id':'execution-a'})
        result['failure']={'category':'state_assertion_failure','message':'private payload must not appear'}
        result['steps']=[dict(number=1,action='state',status='failed',duration_ms=1,
            state=dict(invocation_id='execution-a',workspace_id='execution-a',path='saved.bin',kind='file',outcome='rejected'))]
        summary.validate(document)
        for change in ['invocation','workspace','outcome','missing','old-version']:
            altered=copy.deepcopy(document)
            step=altered['results'][0]['steps'][0]
            if change=='invocation':step['state']['invocation_id']='another-execution'
            elif change=='workspace':step['state']['workspace_id']='another-workspace'
            elif change=='outcome':step['state']['outcome']='matched'
            elif change=='missing':del step['state']
            else:altered['report_version']=2
            with self.subTest(change=change),self.assertRaises(summary.InvalidReport):
                summary.validate(altered)

    def invoke(self, root, document=None, raw=None, extra=()):
        source, destination = root / "results.json", root / "summary.md"
        if document is not None:
            source.write_text(json.dumps(document), encoding="utf-8")
        if raw is not None:
            source.write_bytes(raw)
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            code = summary.main(["--input", str(source), "--output", str(destination),
                                 "--evidence-root", str(root), *extra])
        return code, destination.read_text(encoding="utf-8"), stderr.getvalue()

    def test_captured_outcomes_and_versions(self):
        for version in (1, 2, 3):
            for status in summary.STATUSES:
                with self.subTest(version=version, status=status), tempfile.TemporaryDirectory() as tmp:
                    document = report(status, version)
                    if version >= 2:
                        document["results"][0]["workspace"] = {"cleaned": True}
                    code, text, _ = self.invoke(Path(tmp), document)
                    self.assertEqual(code, 0)
                    self.assertIn(f"report v{version}", text)
                    self.assertIn(f"{int(status == 'passed')} passed", text)
                    if status != "passed":
                        self.assertIn("tests&#47;menu&#46;json", text)
                    self.assertNotIn("private error", text)

    def test_unusable_reports_never_claim_success(self):
        cases = [None, b"{", b"null", b"{}", b'[{"a":1}]',
                 b'{"report_version":1,"report_version":2}',
                 b'{"number":NaN}', b"[" * 1200 + b"]" * 1200]
        documents = []
        for field, value in (("report_version", 999), ("report_version", True),
                             ("results", []), ("summary", {"total": 0})):
            document = report()
            document[field] = value
            documents.append(document)
        for raw in cases:
            with self.subTest(raw=str(raw)[:20]), tempfile.TemporaryDirectory() as tmp:
                code, text, _ = self.invoke(Path(tmp), raw=raw)
                self.assertEqual(code, 2)
                self.assertIn("No usable test report", text)
                self.assertNotIn("Captured results:", text)
        for document in documents:
            with self.subTest(document=document), tempfile.TemporaryDirectory() as tmp:
                code, text, _ = self.invoke(Path(tmp), document)
                self.assertEqual(code, 2)
                self.assertIn("No usable test report", text)

    def test_contradictory_pass_and_summary_rejected(self):
        for change in ("counts", "failure", "cleanup", "steps", "empty_steps", "category", "duration", "duplicate"):
            document = report()
            result = document["results"][0]
            if change == "counts":
                document["summary"]["passed"] = 0
            elif change == "failure":
                result["failure"] = {"category": "unexpected_exit", "message": "private"}
            elif change == "cleanup":
                result["cleanup"]["confirmed_exited"] = False
            elif change == "steps":
                result["steps"] = [{"number": 1, "duration_ms": 1, "status": "running"}]
            elif change == "empty_steps":
                result["steps"] = []
            elif change == "category":
                result["failure"] = {"category": [], "message": "private"}
            elif change == "duration":
                result["duration_ms"] = True
            else:
                document["results"].append(copy.deepcopy(result))
                document["summary"].update(total=2, passed=2)
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                code, text, _ = self.invoke(Path(tmp), document)
                self.assertEqual(code, 2)
                self.assertIn("No usable test report", text)

    def test_workflow_outcome_overrides_all_pass_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text, _ = self.invoke(Path(tmp), report(), extra=(
                "--setup-outcome", "failure", "--test-outcome", "skipped",
                "--html-outcome", "failure"))
            self.assertEqual(code, 0)
            self.assertIn("| Installation | failure |", text)
            self.assertIn("did not complete successfully", text)

    def test_injection_and_private_messages_are_not_rendered(self):
        document = report("failed")
        attack = "\n::error::bad | <script>x</script> [click](https://evil.test) `code`\u202e"
        document["results"][0]["spec_path"] = attack
        document["runner_version"] = attack
        document["results"][0]["failure"]["message"] = "SECRET must not be shown"
        with tempfile.TemporaryDirectory() as tmp:
            _, text, stderr = self.invoke(Path(tmp), document)
            for forbidden in ("::error", "<script>", "https://evil.test", "`code`", "\u202e", "SECRET"):
                self.assertNotIn(forbidden, text + stderr)
            self.assertIn("&#60;script&#62;", text)

    def test_evidence_root_and_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "evidence"
            root.mkdir()
            outside = Path(tmp) / "private.txt"
            outside.write_text("PRIVATE SCREEN", encoding="utf-8")
            inside = root / "test.actual.txt"
            inside.write_text("PRIVATE SCREEN", encoding="utf-8")
            document = report("failed")
            document["results"][0]["evidence"] = {
                "screen_path": str(inside), "diff_path": str(outside)}
            _, text, _ = self.invoke(root, document)
            self.assertIn("available locally / outside evidence root", text)
            self.assertNotIn("PRIVATE SCREEN", text)
            self.assertNotIn(str(outside), text)
            inside.unlink()
            (root / "summary.md").unlink()
            _, text, _ = self.invoke(root, document)
            self.assertIn("missing locally", text)

    def test_size_row_and_append_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text, _ = self.invoke(Path(tmp), raw=b" " * (summary.MAX_REPORT_BYTES + 1))
            self.assertEqual(code, 2)
            self.assertIn("8 MiB", text)
        document = report("failed")
        original = document["results"][0]
        document["results"] = [{**original, "spec_path": f"tests/{i}.json"} for i in range(101)]
        document["summary"].update(total=101, failed=101)
        with tempfile.TemporaryDirectory() as tmp:
            code, text, _ = self.invoke(Path(tmp), document)
            self.assertEqual(code, 0)
            self.assertIn("1 further problem results", text)
            destination = Path(tmp) / "summary.md"
            destination.write_bytes(b"x" * summary.MAX_SUMMARY_BYTES)
            code, text, _ = self.invoke(Path(tmp), document)
            self.assertEqual(code, 2)
            self.assertEqual(len(text), summary.MAX_SUMMARY_BYTES)

    def test_input_alias_and_untrusted_run_url_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "results.json"
            source.write_text(json.dumps(report()), encoding="utf-8")
            before = source.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    summary.main(["--input", str(source), "--output", str(source),
                                  "--evidence-root", tmp])
                with self.assertRaises(SystemExit):
                    self.invoke(Path(tmp), report(), extra=("--run-url", "https://evil.test/"))
            self.assertEqual(before, source.read_bytes())


if __name__ == "__main__":
    unittest.main()
