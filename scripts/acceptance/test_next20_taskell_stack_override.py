import unittest

from next20_taskell_stack_override import parse_args


class TaskellStackOverrideTests(unittest.TestCase):
    def test_declared_arm_compilers_are_accepted(self):
        self.assertEqual(parse_args(['--compiler', 'ghc-9.2.8']).compiler, 'ghc-9.2.8')
        self.assertEqual(parse_args(['--compiler', 'ghc-9.0.2']).compiler, 'ghc-9.0.2')

    def test_unreviewed_compiler_is_rejected(self):
        with self.assertRaises(SystemExit):
            parse_args(['--compiler', 'ghc-9.4.8'])


if __name__ == '__main__':
    unittest.main()
