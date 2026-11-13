"""ZIP safety tests for fzy fault artifact readback."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

import next20_fzy_fault_artifact_audit as audit


class FzyFaultArtifactAuditTests(unittest.TestCase):
    def make_zip(self, path, name="fzy/fault-calibration-v1/member.json"):
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(name, b"{}\n")
        data = path.read_bytes()
        return len(data), hashlib.sha256(data).hexdigest()

    def test_reads_exact_bounded_provider_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.zip"
            size, digest = self.make_zip(path)
            files, stats = audit.inspect_zip(path, size, digest, "linux")
        self.assertIn("fzy/fault-calibration-v1/member.json", files)
        self.assertEqual(stats["zip_sha256"], digest)

    def test_rejects_provider_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.zip"
            size, _ = self.make_zip(path)
            with self.assertRaisesRegex(ValueError, "provider artifact"):
                audit.inspect_zip(path, size, "0" * 64, "linux")

    def test_rejects_path_traversal_member(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.zip"
            size, digest = self.make_zip(path, "../outside.json")
            with self.assertRaisesRegex(ValueError, "unsafe ZIP member"):
                audit.inspect_zip(path, size, digest, "linux")


if __name__ == "__main__":
    unittest.main()
