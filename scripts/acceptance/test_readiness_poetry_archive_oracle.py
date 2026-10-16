import base64
import gzip
import io
import json
import tarfile
import unittest

from readiness_poetry_cases import PACKAGE
from readiness_poetry_archive_oracle import reviewed_archive


class PoetryArchiveTests(unittest.TestCase):
    def test_independent_windows_archive_matches_reviewed_capture(self):
        spec=json.loads((PACKAGE/'normal-build-sdist.json').read_text())
        expected=base64.b64decode(spec['steps'][3]['state']['bytes_base64'])
        actual=reviewed_archive(PACKAGE/'project-fixture',windows=True)
        # Compression streams can differ across zlib versions; the independent
        # complete TAR content must equal the previously reviewed capture.
        self.assertEqual(gzip.decompress(actual),gzip.decompress(expected))

    def test_native_member_order_preserves_same_exact_payloads(self):
        values=[]
        for windows in [False,True]:
            raw=reviewed_archive(PACKAGE/'project-fixture',windows)
            with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as bundle:
                members=bundle.getmembers()
                self.assertEqual(members[0].name.split('/',1)[1],
                                 'fixture_app/__init__.py' if windows else 'README.md')
                values.append({m.name:bundle.extractfile(m).read() for m in members})
        self.assertEqual(values[0],values[1])


if __name__=='__main__':unittest.main()
