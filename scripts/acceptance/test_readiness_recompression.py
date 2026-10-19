import gzip
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from readiness_compact_native import compact
from readiness_evidence import RAW, sha256
from readiness_recompress_native import reencode


class RecompressionTests(unittest.TestCase):
    def packet(self,root):
        (root/'fixture').mkdir()
        packet=root/'native/123';packet.mkdir(parents=True)
        value=b'exact\x00\r\n'+bytes(range(256))*100
        (packet/'caf\u00e9.bin').write_bytes(value)
        (packet/'same.bin').write_bytes(value)
        return compact(root,'fixture',['123']),value

    def test_exact_tar_payload_aliases_and_selected_restore_survive_reencoding(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            output,value=self.packet(Path(folder))
            old_index=sha256(output/'index.json')
            with gzip.open(output/'packets.tar.gz','rb') as source:original=source.read()
            reencode(output)
            import lzma
            with lzma.open(output/'packets.tar.xz','rb') as source:self.assertEqual(source.read(),original)
            self.assertFalse((output/'packets.tar.gz').exists())
            self.assertEqual(sha256(output/'index.json'),old_index)
            receipt=json.loads((output/'reencoded.json').read_text())
            self.assertEqual(receipt['physical_members_verified'],1)
            self.assertEqual(receipt['logical_members_retained'],2)
            with tarfile.open(output/'packets.tar.xz','r:xz') as archive:
                self.assertEqual(archive.extractfile(archive.getmembers()[0]).read(),value)
            restored=next((output/'selected-restore').rglob('*.bin'))
            self.assertEqual(restored.read_bytes(),value)

    def test_changed_original_is_refused_without_deleting_it(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            output,_=self.packet(Path(folder))
            original=output/'packets.tar.gz'
            original.write_bytes(original.read_bytes()+b'changed')
            with self.assertRaisesRegex(RuntimeError,'original archive changed'):reencode(output)
            self.assertTrue(original.exists())
            self.assertFalse((output/'packets.tar.xz').exists())


if __name__=='__main__':unittest.main()
