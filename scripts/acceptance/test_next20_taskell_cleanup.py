import tempfile
import unittest
from pathlib import Path

from next20_taskell_cleanup import inventory_work_directory


class TaskellCleanupInventoryTests(unittest.TestCase):
    def test_inventories_regular_stack_work_files_by_bytes_and_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'target'
            source = root / 'src'
            work = source / '.stack-work'
            work.mkdir(parents=True)
            payload = work / 'build' / 'cache.bin'
            payload.parent.mkdir()
            payload.write_bytes(b'bounded compiler output')
            result = inventory_work_directory(work, source)
            self.assertEqual(result['file_count'], 1)
            self.assertEqual(result['total_bytes'], len(b'bounded compiler output'))
            self.assertEqual(result['files']['build/cache.bin']['bytes'], len(b'bounded compiler output'))
            self.assertEqual(len(result['files']['build/cache.bin']['sha256']), 64)

    def test_refuses_stack_work_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            source = parent / 'target' / 'src'
            work = source / '.stack-work'
            work.mkdir(parents=True)
            outside = parent / 'outside.bin'
            outside.write_bytes(b'outside owned root')
            try:
                (work / 'linked.bin').symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest('host does not permit symlink creation in the test temp directory')
            with self.assertRaisesRegex(ValueError, 'link/reparse point'):
                inventory_work_directory(work, source)


if __name__ == '__main__':
    unittest.main()
