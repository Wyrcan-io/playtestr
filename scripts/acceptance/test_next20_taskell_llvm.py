import io
import base64
import hashlib
import tarfile
import tempfile
import unittest
from pathlib import Path

from next20_check import RAW
from next20_taskell_llvm import (PUBLIC_KEY,PUBLIC_KEY_GIT_BLOB,SIGNATURE_COMMENT,
    decode_signify_signature,safe_extract,tool_inventory,verify_tool_inventory)


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


if __name__=='__main__':
    unittest.main()
