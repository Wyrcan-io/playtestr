"""Adversarial controls for the retained Pick provider-artifact auditor."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from next20_pick_artifact_audit import audit_host


class PickArtifactAuditTests(unittest.TestCase):
    def test_rejects_path_traversal_even_with_matching_provider_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "packet.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../outside.json", "{}")
            raw = path.read_bytes()
            row = {"host": "linux", "artifact_bytes": len(raw),
                   "artifact_sha256": hashlib.sha256(raw).hexdigest()}
            with self.assertRaisesRegex(ValueError, "unsafe or oversized ZIP member"):
                audit_host(row, path, {}, {})

    def test_rejects_provider_digest_mismatch_before_reading_members(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "packet.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("safe.json", "{}")
            raw = path.read_bytes()
            row = {"host": "linux", "artifact_bytes": len(raw),
                   "artifact_sha256": "0" * 64}
            with self.assertRaisesRegex(ValueError, "provider artifact size/digest differs"):
                audit_host(row, path, {}, {})


if __name__ == "__main__":
    unittest.main()
