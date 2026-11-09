import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from next20_taskell_public_route_cleanup import COPIES, cleanup


class TaskellPublicRouteCleanupTests(unittest.TestCase):
    def test_removes_only_the_four_exact_owned_executable_copies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root/'artifacts/taskell/public-route'
            payload = b'reviewed Taskell target bytes'
            digest = hashlib.sha256(payload).hexdigest()
            binary_name = 'taskell.exe' if os.name == 'nt' else 'taskell'
            binaries = []
            for name in COPIES:
                binary = output/name/'bin'/binary_name
                binary.parent.mkdir(parents=True)
                binary.write_bytes(payload)
                binaries.append(binary)
            removed = cleanup(output, digest, root=root)
            self.assertEqual(len(removed), 4)
            self.assertTrue(all(not path.exists() for path in binaries))
            self.assertTrue((output/'project/fixtures').parent.is_dir())

    def test_changed_binary_is_preserved_and_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root/'artifacts/taskell/public-route'
            binary = output/'project/bin'/('taskell.exe' if os.name == 'nt' else 'taskell')
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'changed target')
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                cleanup(output, hashlib.sha256(b'reviewed target').hexdigest(), root=root)
            self.assertTrue(binary.is_file())


if __name__ == '__main__':
    unittest.main()
