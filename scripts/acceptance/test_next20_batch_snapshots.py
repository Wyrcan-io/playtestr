import hashlib
from pathlib import Path
import tempfile
import unittest

from next20_batch_snapshots import apply


class BatchSnapshots(unittest.TestCase):
    def test_only_declared_copy_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, canonical = root/'copy', root/'canonical'
            for p in [package, canonical]:
                (p/'snapshots').mkdir(parents=True)
            old, new = b'Prompt    Status\n', b'Prompt              Status\n'
            (package/'snapshots/screen.txt').write_bytes(old)
            (canonical/'snapshots/wide.txt').write_bytes(new)
            h = lambda body: hashlib.sha256(body).hexdigest()
            profiles = {'4': {'snapshots/screen.txt': dict(reviewed_input='snapshots/wide.txt', original_sha256=h(old), reviewed_sha256=h(new))}}
            self.assertEqual(apply(package, canonical, profiles, 3), {})
            self.assertEqual((package/'snapshots/screen.txt').read_bytes(), old)
            self.assertIn('snapshots/screen.txt', apply(package, canonical, profiles, 4))
            self.assertEqual((package/'snapshots/screen.txt').read_bytes(), new)
            self.assertEqual((canonical/'snapshots/wide.txt').read_bytes(), new)
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                apply(package, canonical, profiles, 4)

    def test_escape_and_unreviewed_replacement_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'snapshots').mkdir()
            (root/'snapshots/screen.txt').write_bytes(b'old')
            (root/'snapshots/wide.txt').write_bytes(b'new')
            rule = dict(reviewed_input='snapshots/wide.txt', original_sha256='0'*64, reviewed_sha256='0'*64)
            for name in ['../screen.txt', 'snapshots/../screen.txt', 'snapshots\\screen.txt', '/snapshots/screen.txt', 'snapshots/screen.txt']:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    apply(root, root, {'4': {name: rule}}, 4)
            self.assertEqual((root/'snapshots/screen.txt').read_bytes(), b'old')


if __name__ == '__main__':
    unittest.main()
