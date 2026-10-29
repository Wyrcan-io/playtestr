import unittest
from next20_generated_source import restored_source_inventory


class GeneratedSourceTests(unittest.TestCase):
    def test_generated_source_keeps_primary_and_requires_safe_distinct_paths(self):
        primary={'source.py':'a'*64};generated={'build/VERSION':{'sha256':'b'*64}}
        self.assertEqual(restored_source_inventory(primary,generated),{'source.py':'a'*64,'build/VERSION':'b'*64})
        for name in ['source.py','../escape','/absolute','C:/escape','build\\escape','build/../escape']:
            with self.assertRaises(ValueError):restored_source_inventory(primary,{name:{'sha256':'b'*64}})
        self.assertEqual(primary,{'source.py':'a'*64})
