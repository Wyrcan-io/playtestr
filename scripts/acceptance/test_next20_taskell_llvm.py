import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from next20_check import RAW
from next20_taskell_llvm import safe_extract,tool_inventory,verify_tool_inventory


class TaskellLLVMTests(unittest.TestCase):
    def setUp(self):
        (RAW/'tmp').mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=RAW/'tmp')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

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
