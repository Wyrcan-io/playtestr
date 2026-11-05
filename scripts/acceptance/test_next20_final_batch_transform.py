import unittest

from next20_jrnl_final import widen_viewport


class FinalBatchTransformTests(unittest.TestCase):
    def test_uses_public_spec_defaults_when_viewport_is_omitted(self):
        spec = {'version': 3, 'command': ['tool'], 'steps': [{'exit': 0}]}

        result = widen_viewport(spec)

        self.assertEqual(result['width'], 90)
        self.assertEqual(result['height'], 26)
        self.assertIs(result, spec)

    def test_preserves_and_increments_explicit_dimensions(self):
        self.assertEqual(widen_viewport({'width': 64, 'height': 16}),
                         {'width': 74, 'height': 18})

    def test_rejects_invalid_explicit_dimensions(self):
        for spec in ({'width': True}, {'height': 0}, {'width': '80'}):
            with self.subTest(spec=spec), self.assertRaisesRegex(ValueError, 'positive integers'):
                widen_viewport(spec)


if __name__ == '__main__':
    unittest.main()
