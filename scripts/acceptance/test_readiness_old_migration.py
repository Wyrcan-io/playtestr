import base64
import copy
import unittest

from readiness_old_migration_prepare import migrate


class OldMigrationConversionTests(unittest.TestCase):
    def test_preserves_public_actions_and_exact_utf8_crlf_bytes(self):
        original=dict(version=2,command=['trusted-target'],workspace=dict(fixture='fixtures',cwd='.'),
            steps=[dict(text='save'),dict(exit=7),dict(snapshot='reviewed.txt')])
        unchanged=copy.deepcopy(original)
        case=dict(expected_exit=7,expected_files={'caf\u00e9.txt':'saved\x00\r\n'},absent_paths=['old.txt'])
        result=migrate(original,case)
        self.assertEqual(original,unchanged)
        self.assertEqual(result['version'],3)
        self.assertEqual(result['steps'][:3],original['steps'])
        self.assertEqual(result['command'],original['command'])
        self.assertEqual(base64.b64decode(result['steps'][3]['state']['bytes_base64']),b'saved\x00\r\n')
        self.assertEqual(result['steps'][4],dict(state=dict(kind='absent',path='old.txt')))

    def test_exact_tree_and_empty_directory_cover_collateral_entries(self):
        original=dict(version=2,command=['trusted-target'],steps=[dict(exit=0)])
        result=migrate(original,dict(expected_files={'nested/saved':'yes'},expected_directories=['empty'],
            empty_directories=['empty'],exact_tree=True))
        states=[s['state'] for s in result['steps'][1:]]
        entries={s['path']:s['entries'] for s in states if s['kind']=='entries'}
        self.assertEqual(entries,{'.':['empty','nested'],'empty':[],'nested':['saved']})
        self.assertIn(dict(kind='empty_directory',path='empty'),states)

    def test_rejects_unconfined_state_and_input_after_completion(self):
        for original,case in [
            (dict(version=2,steps=[dict(exit=0)]),dict(expected_files={'../outside':'no'})),
            (dict(version=2,steps=[dict(exit=0),dict(text='more')]),dict(expected_files={'saved':'no'})),
        ]:
            with self.subTest(original=original,case=case),self.assertRaises(ValueError):migrate(original,case)


if __name__=='__main__':unittest.main()
