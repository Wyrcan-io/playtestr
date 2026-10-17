import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from readiness_acquire_plop import extract_source
from readiness_vis_source import materialize_archive
from readiness_evidence import RAW


def bundle(entries):
    result=io.BytesIO()
    with tarfile.open(fileobj=result,mode='w:gz') as archive:
        for name,value in entries:
            entry=tarfile.TarInfo(name);entry.size=len(value)
            archive.addfile(entry,io.BytesIO(value))
    return result.getvalue()


class AcquisitionTests(unittest.TestCase):
    def test_reviewed_archive_alias_is_materialized_without_host_links(self):
        RAW.mkdir(parents=True,exist_ok=True)
        def linked(target):
            output=io.BytesIO()
            with tarfile.open(fileobj=output,mode='w:gz') as stream:
                value=b'\x00reviewed\xff';entry=tarfile.TarInfo('repo/data');entry.size=len(value)
                stream.addfile(entry,io.BytesIO(value))
                alias=tarfile.TarInfo('repo/sub/alias');alias.type=tarfile.SYMTYPE;alias.linkname=target;stream.addfile(alias)
            return output.getvalue()
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            output=Path(folder)/'source'
            data=materialize_archive(linked('../data'),{'sub/alias':'../data'})
            extract_source(data,output,expanded_limit=1024,entry_limit=10,member_limit=1024)
            self.assertEqual((output/'sub/alias').read_bytes(),b'\x00reviewed\xff')
            self.assertFalse((output/'sub/alias').is_symlink())
            for target in ['../../outside','/outside','../missing']:
                with self.assertRaises(RuntimeError):materialize_archive(linked(target),{'sub/alias':target})
            with self.assertRaisesRegex(RuntimeError,'profile differs'):materialize_archive(linked('../data'),{})

    def test_rejected_archive_plan_creates_no_partial_tree_or_canary_write(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            root=Path(folder);canary=root/'canary';canary.write_bytes(b'reviewed')
            for entries in [[('repo/good',b'ok'),('repo/huge',b'1234')],
                            [('repo/good',b'ok'),('repo/../../canary',b'bad')],
                            [('repo/a',b'x'),('repo/a/child',b'y')],
                            [('repo/a',b'x'),('repo/a',b'y')]]:
                output=root/'source'
                with self.assertRaises(RuntimeError):
                    extract_source(bundle(entries),output,expanded_limit=10,entry_limit=10,member_limit=3)
                self.assertFalse(output.exists())
                self.assertEqual(canary.read_bytes(),b'reviewed')

    def test_valid_source_archive_preserves_binary_bytes(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            output=Path(folder)/'source'
            count,size=extract_source(bundle([('repo/nested/file',b'\x00\xff')]),output,
                expanded_limit=10,entry_limit=10,member_limit=3)
            self.assertEqual((count,size),(1,2))
            self.assertEqual((output/'nested/file').read_bytes(),b'\x00\xff')


if __name__=='__main__':unittest.main()
