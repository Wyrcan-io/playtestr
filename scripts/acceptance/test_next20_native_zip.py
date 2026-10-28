"""Direct artifact retention must preserve bytes and refuse unsafe ZIP members."""
import io
import json
import stat
import unittest
import uuid
import zipfile

from next20_check import RAW
from next20_native_zip_packet import retain_zip
from next20_packet_archive import verify


class NativeZipTests(unittest.TestCase):
    def setUp(self):
        self.root=RAW/'control-tests'/('direct-zip-'+uuid.uuid4().hex);self.root.mkdir(parents=True)

    def packet(self,files):
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as stream:
            for name,value in files:stream.writestr(name,value)
        return output.getvalue()

    def test_direct_zip_preserves_logical_aliases_and_actual_report_restore(self):
        report=b'{"status":"actual synthetic report"}\n'
        for generation,(selected,compression) in enumerate([(name,encoding) for name in ['N01.report.json','report.json'] for encoding in ['tar.gz','tar.xz']],1):
            payload=self.packet([('app/'+selected,report),('app/copy.json',report),('app/fixture.txt',b'exact fixture\n')])
            root=self.root/('retained-native-v'+str(generation));index=retain_zip(payload,root,'control-tests','123','synthetic-native',1024**2,compression)
            self.assertEqual(len(index['files']),3);self.assertEqual(index['unique_payloads'],2)
            self.assertEqual((root/'selected-restore.bin').read_bytes(),report)
            verify(root/('packets.'+compression),index['files'])
            changed=json.loads(json.dumps(index['files']));next(iter(changed.values()))['sha256']='0'*64
            with self.assertRaises(ValueError):verify(root/('packets.'+compression),changed)

    def test_direct_zip_refuses_path_escape_link_duplicate_and_archive_overflow(self):
        link=zipfile.ZipInfo('owned/link');link.create_system=3;link.external_attr=(stat.S_IFLNK|0o777)<<16
        packets=[self.packet([('../escape.report.json',b'bad')]),self.packet([(link,b'../outside')]),
            self.packet([('A.report.json',b'one'),('a.report.json',b'two')])]
        for number,payload in enumerate(packets,1):
            with self.assertRaises(ValueError):retain_zip(payload,self.root/('retained-native-v'+str(number)),'control-tests','123','synthetic-native',1024**2)
        with self.assertRaises(ValueError):retain_zip(self.packet([('actual.report.json',b'bounded')]),self.root/'retained-native-v4','control-tests','123','synthetic-native',10)


if __name__=='__main__':unittest.main()
