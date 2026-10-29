import base64
import copy
import unittest

from next20_python_host_profile import application_profile,wizard_profile


class ApplicationProfileTests(unittest.TestCase):
    def test_only_declared_generated_text_changes_without_wizard_arguments(self):
        original=dict(command=['python','-B','-m','owned'],steps=[dict(text='literal\r\ninput'),dict(exit=1),dict(snapshot='reviewed.txt'),
            dict(state=dict(path='generated.toml',kind='file',bytes_base64=base64.b64encode(b'a\r\nb\r\n').decode())),
            dict(state=dict(path='seed.txt',kind='file',bytes_base64=base64.b64encode(b'owned\r\nseed').decode()))])
        before=copy.deepcopy(original);case=dict(native_generated_text_paths=['generated.toml'])
        actual=application_profile(original,case,'linux')
        self.assertEqual(base64.b64decode(actual['steps'][3]['state']['bytes_base64']),b'a\nb\n')
        for i in [0,1,2,4]:self.assertEqual(actual['steps'][i],original['steps'][i])
        self.assertEqual(original,before);self.assertEqual(application_profile(original,case,'windows'),original)
        # Existing wizard strictness remains intact; an application profile does
        # not silently make a missing target interpreter option acceptable there.
        with self.assertRaises(ValueError):wizard_profile(original,case,'python','linux')

    def test_preservation_requires_declared_path_and_host(self):
        spec=dict(command=['python'],steps=[])
        with self.assertRaises(ValueError):application_profile(spec,dict(native_generated_text_paths=['a'],preserve_generated_newlines=['b']),'linux')
        with self.assertRaises(ValueError):application_profile(spec,dict(native_generated_text_paths=[]),'other')
