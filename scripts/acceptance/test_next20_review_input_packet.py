import unittest
import uuid

from next20_check import RAW
from next20_review_input_packet import read,write


class ReviewInputPacketTests(unittest.TestCase):
    def test_original_bytes_restore_and_packet_tampering_and_path_escape_refused(self):
        root=RAW/'control-tests'/('review-inputs-'+uuid.uuid4().hex);root.mkdir(parents=True)
        original={'primary/distribution.json':b'{"exact":"bytes"}\r\n','review/source.txt':'reviewed caf\u00e9 \u96ea'.encode()}
        write(root,original);self.assertEqual(read(root),original)
        archive=root/'review-inputs.tar.xz';archive.write_bytes(archive.read_bytes()+b'changed')
        with self.assertRaises(ValueError):read(root)
        other=root/'unsafe';other.mkdir()
        with self.assertRaises(ValueError):write(other,{'../escape.json':b'{}'})


if __name__=='__main__':unittest.main()
