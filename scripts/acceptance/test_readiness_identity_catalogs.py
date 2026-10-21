import json
from pathlib import Path
import tempfile
import unittest

from readiness_evidence import Campaign, RAW, ROOT, sha256
from readiness_identity_manifest import load_manifest


class IdentityCatalogTests(unittest.TestCase):
    def setUp(self):
        RAW.mkdir(parents=True,exist_ok=True)
        self.folder=tempfile.TemporaryDirectory(dir=RAW)
        self.addCleanup(self.folder.cleanup)
        self.base=Path(self.folder.name)
        self.campaign=Campaign(self.base,phase='final-archive',catalog_project='rclone')
        self.source=self.base/'active/rclone/src/main.go'
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b'original source\n')
        (self.source.parents[1]/'task-owned.json').write_text('{}')

    def test_actual_source_mutation_is_rehashed_and_prior_catalog_remains(self):
        original=self.campaign.identity('rclone',['must-not-launch'])
        initial=load_manifest(self.base,original)
        name=self.source.relative_to(ROOT).as_posix()
        before=sha256(self.source)
        self.assertEqual(initial['files'][name],before)
        self.assertEqual(len(list((self.base/'identities/catalogs').glob('*.json'))),2)
        self.assertEqual(self.campaign.identity('rclone',['must-not-launch']),original)
        self.source.write_bytes(b'actual source mutation\n')
        changed=self.campaign.identity('rclone',['must-not-launch'])
        self.assertNotEqual(changed['sha256'],original['sha256'])
        self.assertEqual(load_manifest(self.base,changed)['files'][name],sha256(self.source))
        self.assertEqual(load_manifest(self.base,original)['files'][name],before)
        self.assertEqual(len(list((self.base/'identities/catalogs').glob('*.json'))),3)

    def test_missing_or_modified_catalog_cannot_supply_identity(self):
        reference=self.campaign.identity('rclone',['must-not-launch'])
        value=json.loads((self.base/reference['manifest']).read_text())
        path=self.base/value['file_catalogs'][0]['manifest']
        before=path.read_bytes()
        path.write_bytes(before+b' ')
        with self.assertRaisesRegex(ValueError,'catalog checksum'):
            load_manifest(self.base,reference)
        path.unlink()
        with self.assertRaisesRegex(RuntimeError,'missing file'):
            load_manifest(self.base,reference)

    def test_catalog_cannot_shadow_invocation_input(self):
        reference=self.campaign.identity('rclone',['must-not-launch'])
        value=json.loads((self.base/reference['manifest']).read_text())
        value['files'][self.source.relative_to(ROOT).as_posix()]='0'*64
        path=self.base/'identities/overlap.json'
        path.write_text(json.dumps(value),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'overlapping identity catalog'):
            load_manifest(self.base,dict(manifest=path.relative_to(self.base).as_posix(),sha256=sha256(path)))

    def test_tracked_javascript_is_rehashed_in_hygen_catalog(self):
        target=self.base/'active/hygen'
        source=target/'src/dist/index.js'
        source.parent.mkdir(parents=True)
        source.write_bytes(b'original tracked JavaScript\n')
        (target/'task-owned.json').write_text('{}')
        (target/'src/package.json').write_text('{}')
        (target/'src/yarn.lock').write_text('locked')
        campaign=Campaign(self.base,phase='final-archive',catalog_project='hygen')
        original=campaign.identity('hygen',['must-not-launch'])
        name=source.relative_to(ROOT).as_posix()
        before=sha256(source)
        source.write_bytes(b'actual tracked JavaScript mutation\n')
        changed=campaign.identity('hygen',['must-not-launch'])
        self.assertNotEqual(original['sha256'],changed['sha256'])
        self.assertEqual(load_manifest(self.base,original)['files'][name],before)
        self.assertEqual(load_manifest(self.base,changed)['files'][name],sha256(source))


if __name__=='__main__':unittest.main()
