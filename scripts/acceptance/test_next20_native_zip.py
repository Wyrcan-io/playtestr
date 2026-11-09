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

    def test_explicit_gzip_bounds_are_recorded_and_unsupported_bounds_refused(self):
        payload=self.packet([('N01.report.json',b'{"status":"actual"}\n')])
        for generation,limit in [(1,24),(2,48)]:
            result=retain_zip(payload,self.root/('retained-native-v'+str(generation)),'control-tests','123','synthetic-native',limit*1024**2)
            self.assertEqual(result['max_archive_bytes'],limit*1024**2)
        with self.assertRaises(ValueError):retain_zip(payload,self.root/'retained-native-v3','control-tests','123','synthetic-native',49*1024**2)
        with self.assertRaises(ValueError):retain_zip(payload,self.root/'retained-native-v4','control-tests','123','synthetic-native',48*1024**2,'tar.xz')

    def test_selected_prefix_retains_actual_provider_evidence_and_binds_full_zip(self):
        import hashlib
        payload=self.packet([
            ('taskell/summary.json',b'{"passed":true}\n'),
            ('taskell/report.json',b'{"status":"passed"}\n'),
            ('events/launch.json',b'{"launched":true}\n'),
            ('toolchain/large-cache.bin',b'unselected cache payload'),
        ])
        expected=hashlib.sha256(payload).hexdigest()
        output=self.root/'retained-native-v5'
        index=retain_zip(payload,output,'control-tests','456','filtered-native',1024**2,
            selection_prefixes=['taskell/','events/'],expected_provider_sha256='sha256:'+expected)
        self.assertEqual(index['provider_zip_sha256'],expected)
        self.assertEqual(index['provider_zip_bytes'],len(payload))
        self.assertEqual(index['selection_prefixes'],['taskell/','events/'])
        self.assertEqual(index['excluded_provider_files'],1)
        self.assertEqual(index['excluded_provider_bytes'],len(b'unselected cache payload'))
        self.assertEqual(len(index['files']),3)
        self.assertEqual((output/'selected-restore.bin').read_bytes(),b'{"status":"passed"}\n')
        verify(output/'packets.tar.gz',index['files'])

        with self.assertRaisesRegex(ValueError,'digest differs'):
            retain_zip(payload,self.root/'retained-native-v6','control-tests','456','filtered-native',1024**2,
                selection_prefixes=['taskell/'],expected_provider_sha256='0'*64)

    def test_selected_runtime_member_uses_explicit_32_mib_bound_and_xz_readback(self):
        body=b'0123456789abcdef'*(17*1024**2//16)
        payload=self.packet([('taskell/runtime.bin',body),('taskell/N01.report.json',b'{"status":"passed"}\n')])
        output=self.root/'retained-native-v7'
        index=retain_zip(payload,output,'control-tests','789','bounded-native',24*1024**2,
            compression='tar.xz',selection_prefixes=['taskell/'],max_file_bytes=32*1024**2)
        self.assertEqual(index['max_file_bytes'],32*1024**2)
        self.assertLessEqual(index['archive_bytes'],24*1024**2)
        verify(output/'packets.tar.xz',index['files'])

    def test_selected_runtime_member_uses_explicit_128_mib_bound(self):
        body=b'0123456789abcdef'*(94*1024**2//16)
        payload=self.packet([('taskell/runtime.bin',body),('taskell/N01.report.json',b'{"status":"passed"}\n')])
        output=self.root/'retained-native-v8'
        index=retain_zip(payload,output,'control-tests','790','bounded-native',24*1024**2,
            compression='tar.xz',selection_prefixes=['taskell/'],max_file_bytes=128*1024**2)
        self.assertEqual(index['max_file_bytes'],128*1024**2)
        self.assertLessEqual(index['archive_bytes'],24*1024**2)
        verify(output/'packets.tar.xz',index['files'])

    def test_selected_packet_records_an_exact_deliberate_binary_exclusion(self):
        output=self.root/'retained-native-v9'
        payload=self.packet([('taskell/runtime/taskell',b'binary bytes'),
            ('taskell/runtime/runtime-identity.json',b'{"sha256":"recorded"}\n'),
            ('taskell/N01.report.json',b'{"status":"passed"}\n')])
        index=retain_zip(payload,output,'control-tests','791','bounded-native',1024**2,
            selection_prefixes=['taskell/'],excluded_members=['taskell/runtime/taskell'])
        self.assertEqual(index['excluded_selected_members'],['taskell/runtime/taskell'])
        self.assertEqual(index['excluded_selected_files'],1)
        self.assertEqual(index['excluded_selected_bytes'],len(b'binary bytes'))
        self.assertNotIn('native/791/bounded-native/taskell/runtime/taskell',index['files'])
        with self.assertRaisesRegex(ValueError,'absent'):
            retain_zip(payload,self.root/'retained-native-v10','control-tests','791','bounded-native',1024**2,
                selection_prefixes=['taskell/'],excluded_members=['taskell/missing'])


if __name__=='__main__':unittest.main()
