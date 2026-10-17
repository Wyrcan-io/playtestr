import gzip
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid

from readiness_evidence import RAW, ROOT
from readiness_compact_native import compact,inventory,verify


class NativeCompactionTests(unittest.TestCase):
    def test_rejected_inventory_creates_no_partial_archive(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            root=Path(folder);(root/'fixture').mkdir();packet=root/'native/123';packet.mkdir(parents=True)
            (packet/'large.log').write_bytes(b'x'*(4*1024**2+1))
            with self.assertRaisesRegex(ValueError,'file bound'):compact(root,'fixture',['123'])
            self.assertFalse((root/'fixture/retained-native-v1').exists())

    def test_exact_binary_unicode_restore_and_changed_archive_rejects(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            root=Path(folder);(root/'fixture').mkdir()
            packet=root/'native/123/playtestr-Linux';packet.mkdir(parents=True)
            value=packet/'synthetic caf\u00e9.json';value.write_bytes(b'\x00exact\r\nbytes\xff')
            output=compact(root,'fixture',['123']);files,_=inventory(root,['123'])
            self.assertEqual((output/'selected-restore/native/123/playtestr-Linux'/value.name).read_bytes(),value.read_bytes())
            archive_bytes=(output/'packets.tar.gz').read_bytes()
            with self.assertRaises(FileExistsError):compact(root,'fixture',['123'])
            second=compact(root,'fixture',['123'],generation=2)
            self.assertEqual((output/'packets.tar.gz').read_bytes(),archive_bytes)
            self.assertEqual((second/'selected-restore/native/123/playtestr-Linux'/value.name).read_bytes(),value.read_bytes())
            changed=output/'changed.tar.gz'
            with gzip.open(changed,'wb') as stream:stream.write(b'not the retained tar payload')
            with self.assertRaises(Exception):verify(changed,files)

    @unittest.skipUnless(os.name=='nt','native checked removal is Windows only')
    def test_native_removal_refuses_changed_payload_then_removes_exact_packet(self):
        RAW.mkdir(parents=True,exist_ok=True)
        run=str(uuid.uuid4().int)[:18];project='compaction-control-'+uuid.uuid4().hex[:8]
        root=RAW/project;packet=RAW/'native'/run;owned=[]
        try:
            root.mkdir();owned.append(root)
            packet.mkdir(parents=True);owned.append(packet)
            value=packet/'owned.json';original=b'{"owned":true}\n';value.write_bytes(original)
            output=compact(RAW,project,[run],generation=2)
            command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                str(ROOT/'scripts/acceptance/readiness_remove_native_packets.ps1'),'-Project',project,'-Generation','2']
            wrong=subprocess.run(command[:-1]+['1'],cwd=ROOT,capture_output=True,timeout=20)
            self.assertNotEqual(wrong.returncode,0);self.assertTrue(value.is_file())
            value.write_bytes(b'changed bytes')
            refused=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=20)
            self.assertNotEqual(refused.returncode,0);self.assertTrue(value.is_file())
            value.write_bytes(original)
            removed=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=20)
            self.assertEqual(removed.returncode,0,removed.stderr.decode(errors='replace'))
            self.assertFalse(packet.exists());self.assertTrue((output/'packets.tar.gz').is_file())
        finally:
            for selected in owned:
                selected.resolve().relative_to(RAW.resolve())
                if selected.exists():shutil.rmtree(selected)


if __name__=='__main__':unittest.main()
