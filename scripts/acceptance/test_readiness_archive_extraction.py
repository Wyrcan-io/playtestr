import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

from readiness_windows_archive_experience import extract


class NativeArchiveExtractionTests(unittest.TestCase):
    def test_native_archive_layout_checksum_and_existing_installation_refusal(self):
        payload=b'reviewed standalone binary'
        for windows in [True,False]:
            with self.subTest(windows=windows), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);archive=root/('candidate.zip' if windows else 'candidate.tar.gz')
                name='playtestr.exe' if windows else 'playtestr'
                files={'package/'+name:payload,**{'package/'+n:b'reviewed document' for n in ['LICENSE','README.md','THIRD_PARTY_NOTICES.md']}}
                if windows:
                    with zipfile.ZipFile(archive,'w') as stream:
                        for n,data in files.items():stream.writestr(n,data)
                else:
                    with tarfile.open(archive,'w:gz') as stream:
                        for n,data in files.items():
                            member=tarfile.TarInfo(n);member.size=len(data);member.mode=0o755 if n.endswith('/playtestr') else 0o644
                            stream.addfile(member,io.BytesIO(data))
                expected=dict(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(payload).hexdigest())
                installed=extract(archive,expected,root/'installed')
                self.assertEqual(installed.read_bytes(),payload)
                self.assertEqual(len(list(installed.parent.iterdir())),4)
                with self.assertRaisesRegex(RuntimeError,'existing private installation'):
                    extract(archive,expected,root/'installed')
                altered=bytearray(archive.read_bytes());altered[0]^=1;archive.write_bytes(altered)
                with self.assertRaisesRegex(RuntimeError,'checksum mismatch'):
                    extract(archive,expected,root/'rejected')
                self.assertFalse((root/'rejected').exists())


if __name__=='__main__':unittest.main()
