from pathlib import Path
import tempfile
import unittest

from readiness_evidence import RAW, sha256
from readiness_old_copier_git import metadata, restore


class OriginalCopierGitTests(unittest.TestCase):
    def test_restores_all_original_metadata_and_preserves_working_files(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory);file=root/'fixtures/updated/README.md'
            file.parent.mkdir(parents=True);file.write_bytes(b'preserve reviewed working tree\r\n')
            expected=metadata();actual=restore(root)
            self.assertEqual(set(expected),set(actual))
            self.assertEqual(actual,{name:sha256(root/name) for name in expected})
            self.assertEqual(file.read_bytes(),b'preserve reviewed working tree\r\n')
            self.assertEqual(len([n for n in expected if n.endswith('/.git/config')]),4)

    def test_refuses_existing_metadata_before_writing_other_files(self):
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory);name=next(iter(metadata()))
            path=root/name;path.parent.mkdir(parents=True);path.write_bytes(b'existing evidence')
            with self.assertRaisesRegex(RuntimeError,'refuse existing'):
                restore(root)
            self.assertEqual({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()},{name})
            self.assertEqual(path.read_bytes(),b'existing evidence')


if __name__=='__main__':unittest.main()
