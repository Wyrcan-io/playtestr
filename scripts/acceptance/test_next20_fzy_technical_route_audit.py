"""Provider-archive safety checks for fzy technical-route audit inputs."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
import zipfile

sys.path.insert(0, str(Path(__file__).parent))
import next20_fzy_technical_route_audit as audit


class FzyTechnicalRouteAuditTests(unittest.TestCase):
    def make_zip(self, members):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "packet.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in members.items():
                archive.writestr(name, data)
        raw = path.read_bytes()
        return path, len(raw), hashlib.sha256(raw).hexdigest()

    def test_provider_size_digest_and_crc_are_bound(self):
        path, size, digest = self.make_zip({"receipt.json": b"{}"})
        members, observed = audit.read_provider(path, size, digest)
        self.assertEqual(members["receipt.json"], b"{}")
        self.assertEqual(observed["artifact_sha256"], digest)
        with self.assertRaisesRegex(ValueError, "byte count/digest"):
            audit.read_provider(path, size, "0" * 64)

    def test_path_traversal_is_rejected(self):
        path, size, digest = self.make_zip({"../escape": b"x"})
        with self.assertRaisesRegex(ValueError, "unsafe ZIP member"):
            audit.read_provider(path, size, digest)


if __name__ == "__main__":
    unittest.main()
