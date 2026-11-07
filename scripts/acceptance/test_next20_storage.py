import os
import socket
import tempfile
import unittest
from pathlib import Path

from readiness_storage import measure


class StorageMeasureTests(unittest.TestCase):
    def test_records_fifo_metadata_without_following_it(self):
        if not hasattr(os,'mkfifo'):
            self.skipTest('native FIFO accounting is not available on this host')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'payload').write_bytes(b'abc')
            os.mkfifo(root/'runner-pipe')
            result=measure(root)
            self.assertEqual(result['top_level_bytes']['payload'],3)
            self.assertEqual(result['top_level_bytes']['runner-pipe'],0)
            self.assertEqual(result['special_entries'],[
                {'path':'runner-pipe','kind':'fifo','metadata_bytes':0}])

    def test_records_bound_unix_socket_metadata_without_reading_payload(self):
        if not hasattr(socket,'AF_UNIX'):
            self.skipTest('filesystem-backed Unix sockets are unavailable on this host')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);endpoint=root/'runner.sock'
            listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            try:
                listener.bind(str(endpoint))
                result=measure(root)
                self.assertEqual(result['top_level_bytes']['runner.sock'],0)
                self.assertEqual(result['special_entries'],[
                    {'path':'runner.sock','kind':'socket','metadata_bytes':0}])
            finally:
                listener.close()


if __name__=='__main__':
    unittest.main()
