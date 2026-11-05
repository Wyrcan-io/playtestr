"""Tests for deterministic pinned-source retention without external writes."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from next20_check import RAW
from next20_git_town_prepare import create_source_archive


class GitTownSourceArchiveTests(unittest.TestCase):
    def test_archive_is_reproducible_and_contains_exact_manifest_bytes(self):
        RAW.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as temporary:
            root = Path(temporary)
            source = root / 'src'
            first = root / 'first'
            second = root / 'second'
            source.mkdir()
            first.mkdir()
            second.mkdir()
            members = {
                'README.md': b'Pinned source fixture\n',
                'internal/module/file.go': b'package module\n',
                '.github/workflows/check.yml': b'name: check\n',
            }
            expected = {}
            for name, payload in members.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                expected[name] = hashlib.sha256(payload).hexdigest()

            first_sha, first_size = create_source_archive(source, expected, first)
            second_sha, second_size = create_source_archive(source, expected, second)

            self.assertEqual(first_sha, second_sha)
            self.assertEqual(first_size, second_size)
            self.assertEqual((first / 'source.tar.gz').read_bytes(),
                             (second / 'source.tar.gz').read_bytes())

    def test_archive_refuses_manifest_mismatch_and_removes_partial_output(self):
        RAW.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as temporary:
            root = Path(temporary)
            source = root / 'src'
            target = root / 'target'
            source.mkdir()
            target.mkdir()
            payload = b'actual pinned bytes\n'
            (source / 'README.md').write_bytes(payload)
            with self.assertRaisesRegex(ValueError, 'source archive input differs'):
                create_source_archive(source, {'README.md': '0' * 64}, target)
            self.assertFalse((target / 'source.tar.gz').exists())
            self.assertFalse((target / 'source.tar.gz.partial').exists())


if __name__ == '__main__':
    unittest.main()
