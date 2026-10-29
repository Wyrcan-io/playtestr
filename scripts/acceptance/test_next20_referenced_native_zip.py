import io
import unittest
from unittest.mock import patch
import uuid
import zipfile

from next20_check import RAW
import next20_native_packet_reader as reader
import next20_native_zip_packet as ordinary
import next20_referenced_native_zip as referenced


class ReferencedZipTests(unittest.TestCase):
    def zip(self,files):
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as stream:
            for name,body in files:stream.writestr(name,body)
        return output.getvalue()

    def test_direct_original_members_restore_with_real_standalone_dictionary(self):
        root=RAW/'control-tests'/('reference-zip-'+uuid.uuid4().hex);(root/'sample').mkdir(parents=True)
        old=self.zip([('app/N01.report.json',b'{"original":"earlier"}\n'),('app/shared.whl',b'exact reviewed wheel bytes')])
        new=self.zip([('app/N01.report.json',b'{"original":"new"}\n'),('app/shared.whl',b'exact reviewed wheel bytes'),('app/alias.whl',b'exact reviewed wheel bytes')])
        with patch.object(reader,'RAW',root),patch.object(ordinary,'RAW',root),patch.object(referenced,'RAW',root):
            ordinary.retain_zip(old,root/'sample/retained-native-v1','sample','123','old-artifact',1024**2)
            current=referenced.retain(new,root/'sample/retained-native-v2','sample','456','new-artifact',1)
            self.assertEqual(current['schema_version'],3);self.assertEqual(len(current['external_exact_payloads']),2)
            payloads=reader.read_packet('sample',2)[1]
            self.assertEqual(payloads['native/456/new-artifact/app/N01.report.json'],b'{"original":"new"}\n')
            self.assertEqual(payloads['native/456/new-artifact/app/shared.whl'],b'exact reviewed wheel bytes')
            self.assertFalse(current['expanded_payload_created'])
            with self.assertRaises(ValueError):referenced.retain(new,root/'sample/retained-native-v3','sample','789','chained-artifact',2)
            with self.assertRaises(ValueError):referenced.retain(self.zip([('../escape',b'bad')]),root/'sample/retained-native-v4','sample','789','unsafe-artifact',1)
