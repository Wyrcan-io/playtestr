"""Corrupted executable evidence must fail closed before native qualification."""
import copy
import unittest
from next20_binary_delta import encode,decode,digest


class BinaryDeltaTests(unittest.TestCase):
    def test_actual_length_changes(self):
        base=bytes(range(256))*512
        for target in [base[:70001],base+b'tail',base[:65535]+b'changed'+base[65542:]]:
            payload,record=encode(base,target)
            self.assertEqual(decode(base,payload,record),target)

    def test_wrong_dictionary_and_payload(self):
        base=b'a'*90000;payload,record=encode(base,b'a'*80000+b'b')
        for dictionary,changed in [(b'',payload),(b'b'*len(base),payload),(base,payload[:-1]),(base,payload+b'trailing')]:
            with self.assertRaises(ValueError):decode(dictionary,changed,record)

    def test_rehashed_truncation_trailing_and_false_target(self):
        base=b'a'*90000;payload,record=encode(base,b'a'*80000+b'b')
        for changed in [payload[:-1],payload+b'trailing',payload+payload]:
            row=copy.deepcopy(record);row.update(delta_bytes=len(changed),delta_sha256=digest(changed))
            with self.assertRaises(ValueError):decode(base,changed,row)
        row=copy.deepcopy(record);row['target_sha256']='0'*64
        with self.assertRaises(ValueError):decode(base,payload,row)


if __name__=='__main__':unittest.main()
