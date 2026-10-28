"""Preserve segmented text and existing oracles while checking consumed chunks."""
import unittest
from next20_jrnl_final import segmented_steps


class SegmentedInputTests(unittest.TestCase):
    def test_checkpoints_preserve_text_unicode_and_final_oracles(self):
        original=[dict(text='café雪abcdef'),dict(expect='Name: café雪abcdef'),dict(key='Enter'),dict(state=dict(path='saved',kind='file',text='exact'))]
        result=segmented_steps(original,readiness=True)
        self.assertEqual(''.join(s['text'] for s in result if 'text' in s),original[0]['text'])
        self.assertEqual(result[-3:],original[-3:])
        self.assertIn(dict(expect='Name: caf'),result)
        self.assertIn(dict(expect='Name: café雪a'),result)
        self.assertEqual(original[0]['text'],'café雪abcdef')

    def test_no_invented_checkpoint_without_explicit_matching_full_input(self):
        for tail in [dict(key='Enter'),dict(expect='Unrelated screen')]:
            original=[dict(text='abcdefg'),tail]
            self.assertEqual(segmented_steps(original,readiness=True),[dict(text='abc'),dict(text='def'),dict(text='g'),tail])
        self.assertEqual(segmented_steps([dict(text='abcdef'),dict(expect='Name: abcdef')]),[dict(text='abc'),dict(text='def'),dict(expect='Name: abcdef')])


if __name__=='__main__':unittest.main()
