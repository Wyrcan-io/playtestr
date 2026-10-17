import base64
import copy
import json
import unittest

from readiness_edit_profiles import native_profile
from readiness_evidence import ROOT


class EditorProfilesTests(unittest.TestCase):
    def test_reviewed_unix_newline_changes_only_new_document_bytes(self):
        source=ROOT/'docs/validation/runner-readiness-ten-project-pass/edit/contracts'
        for path in sorted(source.glob('*.json')):
            original=json.loads(path.read_text(encoding='utf-8-sig'));saved=copy.deepcopy(original)
            self.assertEqual(native_profile(original,path.name,True),original)
            unix=native_profile(original,path.name,False)
            expected=copy.deepcopy(original);expected.pop('inherit_env',None)
            if path.name=='N02.json':
                expected['steps'][8]['state']['bytes_base64']=base64.b64encode(b'fresh document\n').decode()
            self.assertEqual(unix,expected)
            self.assertEqual(original,saved)
        absent_newline=json.loads((source/'E07.json').read_text())
        self.assertEqual(native_profile(absent_newline,'E07.json',False)['steps'],absent_newline['steps'])

    def test_changed_frozen_new_document_rejects_profile_instead_of_normalizing(self):
        source=ROOT/'docs/validation/runner-readiness-ten-project-pass/edit/contracts/N02.json'
        changed=json.loads(source.read_text());changed['steps'][8]['state']['bytes_base64']=''
        with self.assertRaisesRegex(RuntimeError,'unexpected frozen'):native_profile(changed,'N02.json',False)
