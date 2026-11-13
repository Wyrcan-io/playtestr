"""Archive-bound controls for the independent fzy artifact auditor."""
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from next20_fzy_artifact_audit import inspect_zip


class FzyArtifactAuditTests(unittest.TestCase):
    def test_reads_a_digest_bound_bounded_zip(self):
        with tempfile.TemporaryDirectory(prefix="fzy-audit-control-") as temporary:
            path = Path(temporary) / "packet.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("fzy/report.json", b"{}")
            raw = path.read_bytes()
            files, summary = inspect_zip(path, len(raw), hashlib.sha256(raw).hexdigest(), "linux")
            self.assertEqual(files["fzy/report.json"], b"{}")
            self.assertEqual(summary["zip_entries"], 1)

    def test_refuses_provider_digest_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="fzy-audit-digest-") as temporary:
            path = Path(temporary) / "packet.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("fzy/report.json", b"{}")
            with self.assertRaisesRegex(ValueError, "provider ZIP bytes or SHA-256 differs"):
                inspect_zip(path, path.stat().st_size, "0" * 64, "linux")

    def test_refuses_path_traversal_member(self):
        with tempfile.TemporaryDirectory(prefix="fzy-audit-path-") as temporary:
            path = Path(temporary) / "packet.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../escape.json", b"{}")
            raw = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "unsafe ZIP member"):
                inspect_zip(path, len(raw), hashlib.sha256(raw).hexdigest(), "linux")


if __name__ == "__main__":
    unittest.main()
