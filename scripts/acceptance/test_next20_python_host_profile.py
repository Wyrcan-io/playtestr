import base64
import unittest

from next20_python_host_profile import wizard_profile


class PythonWizardProfileTests(unittest.TestCase):
    def test_explicit_readiness_is_additive_and_existing_file_newlines_survive(self):
        encoded=base64.b64encode(b'parent\r\n').decode()
        original=dict(command=['python','--python','python'],env={},steps=[{'key':'Enter'},
            {'state':{'path':'parent','bytes_base64':encoded}}])
        case=dict(native_generated_text_paths=['parent'],preserve_generated_newlines=['parent'],
            readiness_before_step={'1':'Version'})
        actual=wizard_profile(original,case,'/owned/python','linux')
        self.assertEqual(actual['steps'],[{'expect':'Version'},*original['steps']])
        with self.assertRaises(ValueError):wizard_profile(original,dict(case,preserve_generated_newlines=['unknown']),'/owned/python','linux')

    def test_native_wizard_changes_only_declared_text_and_controls(self):
        encoded=base64.b64encode(b'owned\r\n').decode()
        value=dict(command=['old','--python','old'],env={'GIT_CONFIG_GLOBAL':'nul'},steps=[
            {'state':{'path':'generated','bytes_base64':encoded}},
            {'state':{'path':'preserved','bytes_base64':encoded}},
            {'key':'CtrlZ'},{'key':'Enter'},{'exit':3221225786}])
        actual=wizard_profile(value,{'native_generated_text_paths':['generated']},'/owned/python','linux')
        self.assertEqual(actual['command'],['old','--python','/owned/python'])
        self.assertEqual(base64.b64decode(actual['steps'][0]['state']['bytes_base64']),b'owned\n')
        self.assertEqual(actual['steps'][1],value['steps'][1])
        self.assertEqual(actual['steps'][2:],[{'key':'CtrlD'},{'exit':130}])
        self.assertEqual(value['steps'][2],{'key':'CtrlZ'})

    def test_native_wizard_refuses_ambiguous_interpreter_and_eof(self):
        for value in [dict(command=['old'],env={},steps=[]),
                      dict(command=['old','--python','old'],env={},steps=[{'key':'CtrlZ'},{'text':'x'}])]:
            with self.assertRaises(ValueError):wizard_profile(value,{'native_generated_text_paths':[]},'/owned/python','linux')
