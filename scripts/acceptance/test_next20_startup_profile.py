import copy
import unittest

from next20_startup_profile import startup_deadline, tight_startup


class StartupProfileTests(unittest.TestCase):
    def test_explicit_candidate_startup_deadline_overrides_legacy_shared_declaration(self):
        legacy={'startup_timeout_ms_by_host': {'linux': 2000, 'windows': 2000}}
        candidate={'linux': 5000, 'windows': 2000}
        self.assertEqual(startup_deadline('linux', legacy, candidate), 5000)
        self.assertEqual(startup_deadline('windows', legacy, candidate), 2000)
        self.assertEqual(startup_deadline('linux', legacy), 2000)
        with self.assertRaisesRegex(ValueError, 'host mapping'):
            startup_deadline('linux', legacy, [5000])
        self.assertEqual(tight_startup(dict(steps=[dict(expect='ready')], timeout_ms=20000,
                                             run_timeout_ms=60000), {}, 6000)['startup_timeout_ms'], 6000)
        with self.assertRaisesRegex(ValueError, 'deadline'):
            tight_startup(dict(steps=[dict(expect='ready')], timeout_ms=20000,
                               run_timeout_ms=60000), {}, 6001)

    def test_output_gate_default_and_quiet_exact_completion_both_keep_declared_boundary(self):
        ordinary=dict(steps=[dict(expect='ready')],timeout_ms=10000,run_timeout_ms=30000)
        self.assertEqual(tight_startup(ordinary,{},2000)['startup_timeout_ms'],2000)
        quiet=dict(steps=[dict(exit=1)],timeout_ms=2000,run_timeout_ms=2000,startup_timeout_ms=0)
        self.assertEqual(tight_startup(quiet,dict(startup_evidence='exact-first-exit'),2000),quiet)
        for changed in [dict(quiet,run_timeout_ms=2001),dict(quiet,timeout_ms=2001),dict(quiet,startup_timeout_ms=2000),dict(quiet,steps=[dict(expect='ready')])]:
            with self.assertRaises(ValueError):tight_startup(changed,dict(startup_evidence='exact-first-exit'),2000)
        with self.assertRaises(ValueError):tight_startup(quiet,dict(startup_evidence='unknown'),2000)
