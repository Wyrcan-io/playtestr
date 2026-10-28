"""The native readiness remedy must add checks without weakening any oracle."""
import unittest
from next20_cargo_readiness_review import add_readiness,add_edit_readiness


class CargoReadinessTests(unittest.TestCase):
    def test_readiness_preserves_every_original_action_and_oracle(self):
        original=dict(version=3,steps=[dict(text='synthetic-notes'),dict(key='Enter'),dict(text='Ada'),dict(key='Enter'),dict(snapshot='same.rows.json'),dict(state=dict(path='profile',kind='file',text='exact'))])
        changed=add_readiness(original)
        self.assertEqual(changed['steps'][1],dict(expect='Project Name: synthetic-notes'))
        self.assertEqual(changed['steps'][4],dict(expect='Project owner: Ada'))
        self.assertEqual([s for s in changed['steps'] if 'expect' not in s],original['steps'])
        self.assertNotIn('expect',original['steps'][1])

    def test_readiness_refuses_missing_duplicate_or_moved_enter_anchors(self):
        good=[dict(text='synthetic-notes'),dict(key='Enter'),dict(text='Ada'),dict(key='Enter')]
        for steps in [good[:-2],good+good,good[:1]+[dict(key='Escape')]+good[2:]]:
            with self.assertRaises(ValueError):add_readiness(dict(steps=steps))

    def test_edit_readiness_preserves_real_backspace_resize_and_saved_oracle(self):
        original=dict(steps=[dict(text='synthetic-notes'),dict(key='Enter'),dict(resize=dict(width=100,height=30)),dict(text='Adx'),dict(key='Backspace'),dict(text='a'),dict(key='Enter'),dict(state=dict(path='profile',kind='file',text='Ada'))])
        changed=add_edit_readiness(original)
        self.assertEqual([s for s in changed['steps'] if 'expect' not in s and 'expect_not' not in s],original['steps'])
        self.assertIn(dict(expect_not='Project owner: Adx'),changed['steps'])
        self.assertIn(dict(expect='Project owner: Ada'),changed['steps'])
        self.assertEqual(len(changed['steps']),len(original['steps'])+5)

    def test_edit_readiness_refuses_missing_or_changed_edit_transition(self):
        steps=[dict(text='synthetic-notes'),dict(key='Enter'),dict(text='Adx'),dict(key='Escape'),dict(text='a'),dict(key='Enter')]
        with self.assertRaises(ValueError):add_edit_readiness(dict(steps=steps))


if __name__=='__main__':unittest.main()
