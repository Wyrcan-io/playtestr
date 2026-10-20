import json
from pathlib import Path
import tempfile
import unittest

from readiness_evidence import RAW, sha256
from readiness_old_superfile_verify import canonical_archive


class CanonicalOriginalSourceTests(unittest.TestCase):
    def test_requires_actual_matching_canonical_archive_and_exact_reference(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as directory:
            root=Path(directory);canonical=root/'old-superfile/retained-source/source.tar.gz'
            canonical.parent.mkdir(parents=True);canonical.write_bytes(b'original bounded archive')
            target=root/'native-packet/old-superfile';reference=target/'build-receipts/canonical-source-reference.json'
            reference.parent.mkdir(parents=True)
            approved=dict(archive_sha256=sha256(canonical),archive_bytes=canonical.stat().st_size,
                canonical_campaign_path='old-superfile/retained-source/source.tar.gz')
            reference.write_text(json.dumps(approved))
            review=dict(archive_sha256=approved['archive_sha256'])
            self.assertEqual(canonical_archive(target,review,root),canonical)
            canonical.write_bytes(b'corrupt! bounded archive')
            with self.assertRaisesRegex(RuntimeError,'source reference missing or changed'):
                canonical_archive(target,review,root)
            canonical.write_bytes(b'original bounded archive')
            reference.write_text(json.dumps(dict(approved,canonical_campaign_path='../unrelated.tar.gz')))
            with self.assertRaisesRegex(RuntimeError,'reference path differs'):
                canonical_archive(target,review,root)
            reference.write_text(json.dumps(approved));canonical.unlink()
            with self.assertRaisesRegex(RuntimeError,'archive missing'):
                canonical_archive(target,review,root)


if __name__=='__main__':unittest.main()
