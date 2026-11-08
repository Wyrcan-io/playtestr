import io
import base64
import hashlib
import os
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from next20_check import RAW
from next20_taskell_llvm import (PUBLIC_KEY,PUBLIC_KEY_GIT_BLOB,SIGNATURE_COMMENT,
    checked_version,decode_signify_signature,safe_extract,safe_extract_libffi,tool_inventory,verify_tool_inventory)


class TaskellLLVMTests(unittest.TestCase):
    def setUp(self):
        (RAW/'tmp').mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=RAW/'tmp')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_pinned_archive_key_matches_signify_envelope_and_mismatch_rejects(self):
        public=base64.b64decode(PUBLIC_KEY,validate=True)
        content=('untrusted comment: signify public key\n'+PUBLIC_KEY+'\n').encode()
        self.assertEqual(hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest(),
                         PUBLIC_KEY_GIT_BLOB)
        self.assertEqual(public[:2],b'Ed')
        self.assertEqual(public[2:10].hex(),'7e3e18ab04272542')
        self.assertEqual(SIGNATURE_COMMENT,'untrusted comment: verify with macports-archives-2025.pub')
        signature=self.root/'archive.sig'
        signature.write_text(SIGNATURE_COMMENT+'\n'+base64.b64encode(b'Ed'+public[2:10]+b'0'*64).decode()+'\n',encoding='ascii')
        parsed,decoded=decode_signify_signature(signature)
        self.assertEqual(parsed,public)
        self.assertEqual(decoded[2:10],public[2:10])
        signature.write_text('untrusted comment: verify with another-key.pub\n'+
            base64.b64encode(decoded).decode()+'\n',encoding='ascii')
        with self.assertRaisesRegex(ValueError,'unexpected signify envelope'):
            decode_signify_signature(signature)

    def test_failed_native_version_probe_preserves_bounded_diagnostics(self):
        with patch('next20_taskell_llvm.subprocess.run',return_value=type('Result',(),{
                'returncode':-6,'stdout':'short stdout','stderr':'LLVM abort detail'})()):
            with self.assertRaisesRegex(RuntimeError,'LLVM abort detail'):
                checked_version('owned/opt',{})

    def archive(self,entries):
        package=self.root/'fixture.tbz2'
        with tarfile.open(package,'w:bz2') as archive:
            for name,data in entries:
                member=tarfile.TarInfo(name)
                member.size=len(data)
                member.mode=0o755
                archive.addfile(member,io.BytesIO(data))
        return package

    def test_bounded_extraction_and_tool_inventory_bind_bytes(self):
        package=self.archive([
            ('opt/local/libexec/llvm-12/bin/opt',b'opt-fixture'),
            ('opt/local/libexec/llvm-12/bin/llc',b'llc-fixture'),
        ])
        prefix=self.root/'llvm-12'
        expanded,opt,llc=safe_extract(package,prefix)
        self.assertEqual(expanded,len(b'opt-fixture')+len(b'llc-fixture'))
        self.assertEqual(opt.read_bytes(),b'opt-fixture')
        self.assertEqual(llc.read_bytes(),b'llc-fixture')
        inventory=tool_inventory(prefix)
        verify_tool_inventory(prefix,inventory)
        opt.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'file changed'):
            verify_tool_inventory(prefix,inventory)

    def test_archive_path_escape_is_rejected_before_extraction(self):
        package=self.archive([('opt/local/libexec/llvm-12/../escape',b'no')])
        with self.assertRaisesRegex(ValueError,'Unsafe MacPorts LLVM archive member path'):
            safe_extract(package,self.root/'llvm-12')
        self.assertFalse((self.root/'escape').exists())

    def test_macports_layout_allows_only_bounded_ignored_versioned_bin_wrappers(self):
        package=self.root/'layout.tbz2'
        with tarfile.open(package,'w:bz2') as archive:
            for name in ('opt','opt/local','opt/local/bin','opt/local/libexec',
                         'opt/local/libexec/llvm-12','opt/local/libexec/llvm-12/bin'):
                member=tarfile.TarInfo(name);member.type=tarfile.DIRTYPE;archive.addfile(member)
            for name,data in [('opt/local/bin/opt-mp-12',b'#!/bin/sh\n'),
                              ('opt/local/bin/llc-mp-12',b'#!/bin/sh\n'),
                              ('opt/local/libexec/llvm-12/bin/opt',b'opt'),
                              ('opt/local/libexec/llvm-12/bin/llc',b'llc')]:
                member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o755
                archive.addfile(member,io.BytesIO(data))
        prefix=self.root/'selected-llvm'
        safe_extract(package,prefix)
        self.assertEqual((prefix/'bin/opt').read_bytes(),b'opt')
        self.assertEqual((prefix/'bin/llc').read_bytes(),b'llc')
        self.assertFalse((self.root/'opt').exists())

    @unittest.skipIf(os.name=='nt','native Windows symlink creation unavailable under this token')
    def test_signed_libffi_layout_selects_versioned_dylib_and_safe_alias(self):
        package=self.root/'libffi.tbz2'
        with tarfile.open(package,'w:bz2') as archive:
            for name,data in [('opt/local/lib/libffi.8.1.2.dylib',b'ffi-binary'),
                              ('opt/local/include/ffi.h',b'header')]:
                member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o755
                archive.addfile(member,io.BytesIO(data))
            alias=tarfile.TarInfo('opt/local/lib/libffi.8.dylib');alias.type=tarfile.SYMTYPE
            alias.linkname='libffi.8.1.2.dylib';archive.addfile(alias)
        prefix=self.root/'selected-llvm'
        expanded=safe_extract_libffi(package,prefix)
        self.assertEqual(expanded,len(b'ffi-binary'))
        self.assertEqual((prefix/'lib/libffi.8.dylib').read_bytes(),b'ffi-binary')
        self.assertEqual((prefix/'lib/libffi.8.dylib').resolve(),(prefix/'lib/libffi.8.1.2.dylib').resolve())

    def test_libffi_extraction_refuses_escaping_link(self):
        package=self.root/'libffi-escape.tbz2'
        with tarfile.open(package,'w:bz2') as archive:
            alias=tarfile.TarInfo('opt/local/lib/libffi.8.dylib');alias.type=tarfile.SYMTYPE
            alias.linkname='../../outside.dylib';archive.addfile(alias)
        with self.assertRaisesRegex(ValueError,'Escaping symlink'):
            safe_extract_libffi(package,self.root/'selected-llvm')


if __name__=='__main__':
    unittest.main()
