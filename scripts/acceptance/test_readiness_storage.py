import os
from pathlib import Path
import tempfile
import unittest

from readiness_evidence import RAW
from readiness_storage import measure


class LogicalStorageTests(unittest.TestCase):
    def test_empty_and_nested_binary_unicode_files_have_exact_totals(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory)
            self.assertEqual(measure(root),dict(total_bytes=0,files=0,top_level_bytes={},unfollowed_links=[]))
            for name,value in {'alpha.bin':b'\x00A','nested/caf\u00e9.txt':b'abc','nested/deeper/data':b'\r\n\xff'}.items():
                path=root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(value)
            (root/'empty').mkdir()
            self.assertEqual(measure(root),dict(total_bytes=8,files=3,
                top_level_bytes={'alpha.bin':2,'nested':6},unfollowed_links=[]))

    def test_directory_link_counts_only_its_metadata_without_traversal(self):
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            base=Path(directory)
            root=base/'measured'
            root.mkdir()
            outside=base/'outside'
            outside.mkdir()
            (outside/'not-counted.bin').write_bytes(b'x'*1024**2)
            link=root/'alias'
            try:os.symlink(outside,link,target_is_directory=True)
            except OSError as error:self.skipTest('Native directory symlink prerequisite unavailable: '+str(error))
            (root/'kept').write_bytes(b'keep')
            size=link.lstat().st_size
            self.assertEqual(measure(root),dict(total_bytes=4+size,files=1,
                top_level_bytes={'alias':size,'kept':4},unfollowed_links=['alias']))


if __name__=='__main__':unittest.main()
