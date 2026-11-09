import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from next20_taskell_faults import (generated_cabal_identity,source_files,source_snapshot,
    stack_build_environment,target_environment,verify_generated_cabal)


class TaskellFaultSourceTests(unittest.TestCase):
    def test_sdk_ffi_header_path_is_limited_to_stack_build_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            include=Path(temporary)
            (include/'ffitarget_arm64.h').write_bytes(b'owned SDK header')
            source={'PATH':'owned-tools','TASKELL_FFI_INCLUDE_PATH':temporary,'C_INCLUDE_PATH':'prior'}
            build=stack_build_environment(source,temporary)
            self.assertEqual(build['C_INCLUDE_PATH'],str(include.resolve())+os.pathsep+'prior')
            self.assertNotIn('TASKELL_FFI_INCLUDE_PATH',build)
            target=target_environment(source)
            self.assertNotIn('C_INCLUDE_PATH',target)
            self.assertNotIn('TASKELL_FFI_INCLUDE_PATH',target)

    def test_sdk_ffi_directory_without_arm64_header_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError,'ARM64 target header'):
                stack_build_environment({},temporary)

    def test_hpack_output_is_separately_bound_while_stack_cache_is_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)
            (source/'Taskell.hs').write_bytes(b'module Taskell where\n')
            (source/'package.yaml').write_bytes(b'name: taskell\n')
            (source/'taskell.cabal').write_bytes(b'name: taskell\nversion: 1.11.4\n')
            (source/'.stack-work').mkdir()
            (source/'.stack-work/cache').write_bytes(b'generated compiler cache')
            task=source/'Taskell.hs';package=source/'package.yaml'
            provenance={'files':{'Taskell.hs':hashlib.sha256(task.read_bytes()).hexdigest(),
                                 'package.yaml':hashlib.sha256(package.read_bytes()).hexdigest()},
                'git_modes':{'Taskell.hs':'100644','package.yaml':'100644'}}
            self.assertEqual(source_files(source,provenance),provenance['files'])
            identity=generated_cabal_identity(source)
            self.assertEqual(verify_generated_cabal(source,identity),identity)
            (source/'taskell.cabal').write_bytes(b'name: altered\n')
            with self.assertRaisesRegex(ValueError,'Hpack output differs'):
                verify_generated_cabal(source,identity)

    def test_unexpected_non_generated_source_entry_still_fails_exact_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)
            (source/'tracked.txt').write_bytes(b'pinned')
            expected={'tracked.txt':hashlib.sha256(b'pinned').hexdigest()}
            provenance={'files':expected,'git_modes':{'tracked.txt':'100644'}}
            (source/'taskell.cabal').write_bytes(b'generated')
            (source/'unreviewed.tmp').write_bytes(b'unexpected')
            with self.assertRaisesRegex(ValueError,'unexpected.*unreviewed.tmp'):
                source_files(source,provenance)


if __name__=='__main__':unittest.main()
