"""Historical admissions must never inflate the current candidate projection."""
import unittest
from next20_candidate_ledger import candidate_counters


class CandidateLedgerTests(unittest.TestCase):
    def test_current_candidate_excludes_earlier_and_requalification_counts_once(self):
        def admission(project,candidate):return dict(project=project,candidate=candidate,admitted=True,ordinary=480,calibrations=18,canonical_scenarios=20,real_source_faults=3,native_cells=[{},{}])
        old=admission('earlier','rc5');new=admission('new','rc6');requalified=admission('earlier','rc6')
        result=candidate_counters([old,new,requalified])
        self.assertEqual(result['rc5']['projects'],1);self.assertEqual(result['rc5']['ordinary'],480)
        self.assertEqual(result['rc6']['projects'],2);self.assertEqual(result['rc6']['ordinary'],960)
        with self.assertRaises(ValueError):candidate_counters([new,new])
        missing=dict(new);missing.pop('candidate')
        with self.assertRaises(ValueError):candidate_counters([missing])


if __name__=='__main__':unittest.main()
