import unittest

from next20_taskell_stack_override import parse_args


class TaskellStackOverrideTests(unittest.TestCase):
    def test_frozen_arm_compiler_is_accepted(self):
        self.assertEqual(parse_args(['--compiler', 'ghc-9.0.2']).compiler, 'ghc-9.0.2')

    def test_unreviewed_compiler_is_rejected(self):
        for compiler in ('ghc-9.2.8', 'ghc-9.4.8'):
            with self.subTest(compiler=compiler), self.assertRaises(SystemExit):
                parse_args(['--compiler', compiler])


if __name__ == '__main__':
    unittest.main()
