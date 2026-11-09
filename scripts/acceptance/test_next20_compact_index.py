"""Tests for lossless packed-index compatibility across retention readers."""
import hashlib
import json
import lzma
from pathlib import Path
import tempfile
import unittest

import next20_duplicate_evidence_compact as duplicate
import next20_retained_text_compact as retained_text
import next20_zip_exact_compact as exact_zip


class PackedIndexTests(unittest.TestCase):
    def test_all_readers_accept_plain_and_xz_json_indices(self):
        readers = (duplicate, retained_text, exact_zip)
        expected = {"schema_version": 1, "files": {"a": {"bytes": 1}}}
        source = json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()
        for reader in readers:
            with self.subTest(reader=reader.__name__), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "index.json").write_bytes(source)
                self.assertEqual(reader.read_index(root), expected)
                self.assertEqual(reader.logical_index_sha256(root), hashlib.sha256(source).hexdigest())
                (root / "index.json.xz").write_bytes(lzma.compress(source))
                (root / "index.json").unlink()
                self.assertEqual(reader.read_index(root), expected)
                self.assertEqual(reader.logical_index_sha256(root), hashlib.sha256(source).hexdigest())

    def test_rejects_invalid_packed_json(self):
        for reader in (duplicate, retained_text, exact_zip):
            with self.subTest(reader=reader.__name__), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "index.json.xz").write_bytes(lzma.compress(b"not-json"))
                with self.assertRaises(json.JSONDecodeError):
                    reader.read_index(root)


if __name__ == "__main__":
    unittest.main()
