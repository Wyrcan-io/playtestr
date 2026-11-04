import unittest

from next20_git_town_faults import validate_case_observation


def fault(identifier, category='unexpected_exit', target_exit=0):
    return dict(id=identifier, expected_failure_category=category,
                expected_target_exit_code=target_exit)


def result(steps, exit_code=None):
    failure = next((step.get('failure') for step in steps if step.get('status') == 'failed'), None)
    return dict(exit_code=exit_code, steps=steps, failure=failure,
                cleanup=dict(confirmed_exited=True), workspace=dict(cleaned=True))


def contract(code=0):
    return dict(steps=[dict(expect='ready'), dict(exit=code), dict(state={})])


class GitTownFaultValidatorTests(unittest.TestCase):
    def test_pristine_baseline_uses_passed_exit_step_when_aggregate_is_null(self):
        observed = result([
            dict(action='expect', status='passed'),
            dict(action='exit', status='passed'),
            dict(action='state', status='passed'),
        ])
        self.assertIsNone(validate_case_observation(
            fault('F01-parent-output'), 0, 0, 'completed',
            dict(passed=1, failed=0, total=1), observed, contract()))

    def test_f01_requires_unexpected_exit_after_target_zero(self):
        observed = result([
            dict(action='expect', status='failed', failure=dict(
                category='unexpected_exit',
                message='process exited with code 0 before assertion matched')),
            dict(action='exit', status='not_run'),
            dict(action='state', status='not_run'),
        ])
        observed['failure'] = dict(category='unexpected_exit',
                                   message='process exited with code 0 before assertion matched')
        self.assertIsNone(validate_case_observation(
            fault('F01-parent-output'), 1, 1, 'completed',
            dict(passed=0, failed=1, total=1), observed, contract()))

    def test_f02_requires_unexpected_exit_after_target_one(self):
        observed = result([
            dict(action='expect', status='failed', failure=dict(
                category='unexpected_exit',
                message='process exited with code 1 before assertion matched')),
            dict(action='exit', status='not_run'),
            dict(action='state', status='not_run'),
        ])
        observed['failure'] = dict(category='unexpected_exit',
                                   message='process exited with code 1 before assertion matched')
        self.assertIsNone(validate_case_observation(
            fault('F02-feature-refusal', target_exit=1), 1, 1, 'completed',
            dict(passed=0, failed=1, total=1), observed, contract()))

    def test_f03_requires_state_failure_after_passed_exit(self):
        observed = result([
            dict(action='expect', status='passed'),
            dict(action='exit', status='passed'),
            dict(action='state', status='failed', failure=dict(category='state_assertion_failure')),
        ])
        self.assertIsNone(validate_case_observation(
            fault('F03-prototype-persistence', 'state_assertion_failure'), 1, 1,
            'completed', dict(passed=0, failed=1, total=1), observed, contract()))

    def test_rejects_wrong_fault_category_and_missing_cleanup(self):
        bad_fault = result([dict(action='expect', status='failed', failure=dict(
            category='assertion_timeout', message='timed out'))])
        self.assertIn('declared observable failure', validate_case_observation(
            fault('F01-parent-output'), 1, 1, 'completed',
            dict(passed=0, failed=1, total=1), bad_fault, contract()))
        bad_cleanup = result([dict(action='expect', status='passed'),
                              dict(action='exit', status='passed'),
                              dict(action='state', status='passed')])
        bad_cleanup['cleanup']['confirmed_exited'] = False
        self.assertIn('cleanup', validate_case_observation(
            fault('F01-parent-output'), 0, 0, 'completed',
            dict(passed=1, failed=0, total=1), bad_cleanup, contract()))


if __name__ == '__main__':
    unittest.main()
