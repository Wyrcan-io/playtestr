import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import next20_storage as storage
from next20_check import RAW
from readiness_evidence import sha256
from readiness_storage import measure


class LiveShortCacheStorage(unittest.TestCase):
    def setUp(self):
        (RAW/'control-tests').mkdir(exist_ok=True)
        self.temporary=tempfile.TemporaryDirectory(prefix='owned-short-cache-',dir=RAW/'control-tests')
        self.workspace=Path(self.temporary.name)
        self.raw=self.workspace/'artifacts/campaign';self.target=self.raw/'active/cargo-generate';self.cache=self.raw/'r'
        self.target.mkdir(parents=True);self.cache.mkdir()
        self.catalog=self.target/'dependency-source-catalog.json';self.catalog.write_text('{"files":{}}')
        self.materialized=self.cache/'materialized.json'
        self.materialized.write_text(json.dumps(dict(original_source_catalog_sha256=sha256(self.catalog))))
        self.owner=self.cache/'task-owned.json'
        self.owner.write_text(json.dumps(dict(workspace=str(self.workspace),project='cargo-generate',source_target=str(self.target),catalog_sha256=sha256(self.catalog))))
        self.reference=self.target/'short-cache-reference.json'
        self.reference.write_text(json.dumps(dict(root=str(self.cache),owner_sha256=sha256(self.owner),materialized_sha256=sha256(self.materialized))))
        (self.cache/'compiler-input.bin').write_bytes(b'actual synthetic compiler input')
        self.patch_raw=patch.object(storage,'RAW',self.raw);self.patch_root=patch.object(storage,'ROOT',self.workspace)
        self.patch_raw.start();self.patch_root.start()

    def tearDown(self):
        self.patch_root.stop();self.patch_raw.stop();self.temporary.cleanup()

    def test_real_owned_cache_size_and_foreign_owner_refusal(self):
        observed=measure(self.raw)
        result=storage.owned_short_cache(observed)
        self.assertEqual(result['bytes'],measure(self.cache)['total_bytes'])
        self.assertEqual(result['project'],'cargo-generate')
        owner=json.loads(self.owner.read_text());owner['workspace']=str(self.workspace/'foreign');self.owner.write_text(json.dumps(owner))
        reference=json.loads(self.reference.read_text());reference['owner_sha256']=sha256(self.owner);self.reference.write_text(json.dumps(reference))
        with self.assertRaises(ValueError):storage.owned_short_cache(measure(self.raw))

    def test_retired_target_or_changed_source_cannot_hide_retained_cache(self):
        observed=measure(self.raw)
        self.target.rename(self.target.with_name('retired'))
        with self.assertRaises(ValueError):storage.owned_short_cache(observed)
        self.target.with_name('retired').rename(self.target)
        self.catalog.write_text('{"files":{"changed":"source"}}')
        with self.assertRaises(ValueError):storage.owned_short_cache(measure(self.raw))


if __name__=='__main__':unittest.main()
