import hashlib
import json
from pathlib import Path
import stat
import tarfile
import tempfile
import unittest

import next20_control_duplicate_compact as compact
from readiness_evidence import immutable_json, sha256


class ControlDuplicateReadbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="control-duplicate-test-", dir=compact.ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original_raw = compact.RAW
        compact.RAW = self.root
        self.addCleanup(setattr, compact, "RAW", self.original_raw)
        self.source = self.root / "control-tests"
        self.source.mkdir()
        self.data = b"same exact synthetic evidence\n" * 400
        self.paths = [self.source / "a" / "report.json", self.source / "b" / "report.json"]
        for path in self.paths:
            path.parent.mkdir()
            path.write_bytes(self.data)
        self.packet = self.root / "packet"
        self.packet.mkdir()
        digest = hashlib.sha256(self.data).hexdigest()
        rows = []
        for path in self.paths:
            st = path.stat()
            rows.append({
                "path": path.relative_to(self.root).as_posix(), "sha256": digest,
                "bytes": len(self.data), "mode": stat.S_IMODE(st.st_mode), "mtime_ns": st.st_mtime_ns,
            })
        archive_path = self.packet / "payload.tar.xz"
        with tarfile.open(archive_path, "w:xz", preset=1) as archive:
            info = tarfile.TarInfo("blobs/" + digest)
            info.size = len(self.data)
            info.mode = rows[0]["mode"]
            info.mtime = rows[0]["mtime_ns"] // 1_000_000_000
            archive.addfile(info, __import__("io").BytesIO(self.data))
        immutable_json(self.packet / "index.json", {
            "schema_version": 1,
            "groups": [{"sha256": digest, "bytes": len(self.data), "paths": rows}],
            "alias_path_count": len(rows), "expanded_alias_bytes": len(self.data) * len(rows),
            "archive_sha256": sha256(archive_path),
        })

    def test_complete_payload_and_every_alias_read_back(self):
        self.assertEqual(compact.readback(self.packet)["alias_path_count"], 2)

    def test_tampered_payload_rejected(self):
        archive = self.packet / "payload.tar.xz"
        archive.write_bytes(archive.read_bytes() + b"tamper")
        with self.assertRaises(ValueError):
            compact.readback(self.packet)

    def test_changed_source_metadata_rejected(self):
        path = self.paths[0]
        path.write_bytes(self.data + b"changed")
        with self.assertRaises(ValueError):
            compact.readback(self.packet)

    def test_unsafe_or_non_campaign_alias_rejected(self):
        for name in ("../escape", "other/project/file", "control-tests/../escape", "control-tests/a\\b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                compact.safe_path(name)


if __name__ == "__main__":
    unittest.main()
