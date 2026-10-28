"""The native readiness remedy must add checks without weakening any oracle."""
import unittest
from next20_cargo_readiness_review import add_readiness


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


if __name__=='__main__':unittest.main()
