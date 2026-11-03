import unittest

from next20_harness_audit import expected_skip


class HarnessSkipPolicy(unittest.TestCase):
    def test_only_declared_opposite_platform_controls_have_exact_skip_reasons(self):
        unix='test_actual_readonly_module_cache_can_be_removed_after_preparation'
        windows='test_native_large_cleanup_requires_matching_explicit_bound'
        unix_line=unix+" (...) ... skipped 'native Unix read-only directory permissions'"
        windows_line=windows+" (...) ... skipped 'native Windows checked target removal control'"
        self.assertEqual(expected_skip('windows-2025',unix,unix_line),'native Unix read-only directory permissions')
        self.assertIsNone(expected_skip('windows-2025',windows,windows_line))
        for host in ['ubuntu-24.04','macos-15']:
            self.assertEqual(expected_skip(host,windows,windows_line),'native Windows checked target removal control')
            self.assertIsNone(expected_skip(host,unix,unix_line))

    def test_unknown_control_host_reason_and_failed_outcomes_remain_rejected(self):
        name='test_actual_readonly_module_cache_can_be_removed_after_preparation'
        line=name+" (...) ... skipped 'native Unix read-only directory permissions'"
        for host,test,text in [('windows-2025','test_unknown',line),('unknown',name,line),
            ('windows-2025',name,line.replace('permissions','permission')),('windows-2025',name,name+' (...) ... FAIL')]:
            with self.subTest(host=host,test=test,text=text):
                self.assertIsNone(expected_skip(host,test,text))


if __name__=='__main__':unittest.main()
