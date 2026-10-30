import copy
import unittest

from next20_startup_profile import tight_startup


class StartupProfileTests(unittest.TestCase):
    def test_output_gate_default_and_quiet_exact_completion_both_keep_declared_boundary(self):
        ordinary=dict(steps=[dict(expect='ready')],timeout_ms=10000,run_timeout_ms=30000)
        self.assertEqual(tight_startup(ordinary,{},2000)['startup_timeout_ms'],2000)
        quiet=dict(steps=[dict(exit=1)],timeout_ms=2000,run_timeout_ms=2000,startup_timeout_ms=0)
        self.assertEqual(tight_startup(quiet,dict(startup_evidence='exact-first-exit'),2000),quiet)
        for changed in [dict(quiet,run_timeout_ms=2001),dict(quiet,timeout_ms=2001),dict(quiet,startup_timeout_ms=2000),dict(quiet,steps=[dict(expect='ready')])]:
            with self.assertRaises(ValueError):tight_startup(changed,dict(startup_evidence='exact-first-exit'),2000)
        with self.assertRaises(ValueError):tight_startup(quiet,dict(startup_evidence='unknown'),2000)
