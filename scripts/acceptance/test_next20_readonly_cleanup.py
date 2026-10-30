import os
from pathlib import Path
import shutil
import stat
import unittest
import uuid

from next20_check import RAW
from next20_target_cleanup import prepare_native_directory_permissions


@unittest.skipIf(os.name=='nt','native Unix read-only directory permissions')
class ReadonlyCleanup(unittest.TestCase):
    def test_actual_readonly_module_cache_can_be_removed_after_preparation(self):
        boundary=RAW/'control-tests'/('readonly-'+uuid.uuid4().hex)
        target=boundary/'owned';module=target/'gopath/pkg/mod/example/module@v1.0.0'
        module.mkdir(parents=True);payload=module/'transport_go117_test.go'
        payload.write_bytes(b'package example\n');payload.chmod(0o444)
        module.chmod(0o555)
        try:
            if os.geteuid()!=0:
                with self.assertRaises(PermissionError):shutil.rmtree(target)
            self.assertEqual(prepare_native_directory_permissions(target,boundary),1)
            self.assertEqual(payload.read_bytes(),b'package example\n')
            self.assertEqual(stat.S_IMODE(payload.stat().st_mode),0o444)
            shutil.rmtree(target)
            self.assertFalse(target.exists())
        finally:
            if target.exists():
                prepare_native_directory_permissions(target,boundary);shutil.rmtree(target)
        boundary.rmdir()

    def test_foreign_root_and_link_are_refused_without_touching_destination(self):
        boundary=RAW/'control-tests'/('readonly-guard-'+uuid.uuid4().hex)
        owned=boundary/'owned';foreign=boundary/'foreign'
        owned.mkdir(parents=True);foreign.mkdir();(foreign/'keep.txt').write_bytes(b'keep')
        before=foreign.stat().st_mode
        try:
            with self.assertRaises(ValueError):prepare_native_directory_permissions(boundary,boundary)
            with self.assertRaises(ValueError):prepare_native_directory_permissions(foreign,owned)
            (owned/'alias').symlink_to(foreign,target_is_directory=True)
            with self.assertRaises(ValueError):prepare_native_directory_permissions(owned,boundary)
            self.assertEqual((foreign/'keep.txt').read_bytes(),b'keep')
            self.assertEqual(foreign.stat().st_mode,before)
        finally:
            (owned/'alias').unlink(missing_ok=True);shutil.rmtree(boundary)


if __name__=='__main__':unittest.main()
