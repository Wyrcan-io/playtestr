"""Archive representation retains exact gzip bytes and rejects broken closure."""
import copy
import gzip
import unittest
from next20_archive_delta import encode,decode,digest


class ArchiveDeltaTests(unittest.TestCase):
    def test_archive_representation_restores_shifted_exact_compressed_bytes(self):
        base=gzip.compress(bytes(range(256))*1000,mtime=0)
        target=b'shifted-header'+base[:len(base)//2]+b'changed'+base[len(base)//2:]+b'tail'
        payload,record=encode(base,target)
        self.assertEqual(decode(base,payload,record),target)

    def test_archive_representation_refuses_wrong_dictionary_trailing_and_hash(self):
        base=bytes(range(256))*100;payload,record=encode(base,b'prefix'+base+b'tail')
        with self.assertRaises(ValueError):decode(b'wrong',payload,record)
        for changed in [payload[:-1],payload+b'trailing']:
            row=copy.deepcopy(record);row.update(delta_bytes=len(changed),delta_sha256=digest(changed))
            with self.assertRaises(ValueError):decode(base,changed,row)
        row=copy.deepcopy(record);row['target_sha256']='0'*64
        with self.assertRaises(ValueError):decode(base,payload,row)


if __name__=='__main__':unittest.main()
