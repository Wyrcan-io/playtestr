import os
import tempfile
import unittest
from pathlib import Path

import next20_skim_cache_cleanup
from next20_skim_cache_cleanup import inventory_cache, prune


class SkimCacheCleanupTests(unittest.TestCase):
    def test_inventory_hashes_files_then_prune_removes_only_allowlisted_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'active' / 'skim'
            (target / 'cargo-home' / 'registry').mkdir(parents=True)
            (target / 'cargo-home' / 'registry' / 'index').write_bytes(b'pinned-cache-data')
            (target / 'src').mkdir()
            (target / 'src' / 'main.rs').write_bytes(b'preserve source')

            measured = inventory_cache(target / 'cargo-home', target)
            self.assertEqual(measured['files'], 1)
            self.assertEqual(measured['bytes'], len(b'pinned-cache-data'))
            result = prune(target, roots=('cargo-home',))

            self.assertEqual(result['cargo-home'], measured)
            self.assertFalse((target / 'cargo-home').exists())
            self.assertEqual((target / 'src' / 'main.rs').read_bytes(), b'preserve source')

    def test_prune_rejects_roots_outside_fixed_allowlist_before_removal(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'active' / 'skim'
            target.mkdir(parents=True)
            protected = target / 'src'
            protected.mkdir()
            (protected / 'main.rs').write_bytes(b'preserve')

            with self.assertRaisesRegex(ValueError, 'undeclared'):
                prune(target, roots=('src',))
            self.assertEqual((protected / 'main.rs').read_bytes(), b'preserve')

    def test_prune_removes_read_only_cache_files_after_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'active' / 'skim'
            cache = target / 'go-mod-cache' / 'module'
            cache.mkdir(parents=True)
            file = cache / 'readonly.go'
            file.write_bytes(b'pinned-cache-data')
            file.chmod(0o444)
            if os.name != 'nt':
                cache.chmod(0o555)
                (cache.parent).chmod(0o555)
            measured = inventory_cache(target / 'go-mod-cache', target)
            result = prune(target, roots=('go-mod-cache',))
            self.assertEqual(result['go-mod-cache'], measured)
            self.assertFalse((target / 'go-mod-cache').exists())

    def test_inventory_enforces_per_file_byte_bound_with_path_diagnostic(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'active' / 'skim'
            cache = target / 'cargo-home'
            cache.mkdir(parents=True)
            (cache / 'large-toolchain-file').write_bytes(b'12345')
            original = next20_skim_cache_cleanup.MAX_FILE_BYTES
            try:
                next20_skim_cache_cleanup.MAX_FILE_BYTES = 4
                with self.assertRaisesRegex(ValueError, 'large-toolchain-file'):
                    inventory_cache(cache, target)
            finally:
                next20_skim_cache_cleanup.MAX_FILE_BYTES = original

    @unittest.skipUnless(hasattr(os, 'symlink'), 'native symlink support unavailable')
    def test_inventory_refuses_cache_link_that_escapes_owned_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / 'active' / 'skim'
            cache = target / 'cargo-home'
            outside = base / 'outside'
            cache.mkdir(parents=True)
            outside.mkdir()
            (outside / 'secret').write_bytes(b'outside')
            try:
                (cache / 'escape').symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f'native symlink creation unavailable: {error}')
            with self.assertRaisesRegex(ValueError, 'escapes'):
                inventory_cache(cache, target)


if __name__ == '__main__':
    unittest.main()
