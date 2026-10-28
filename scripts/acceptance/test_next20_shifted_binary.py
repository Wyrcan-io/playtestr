"""Relocated executable evidence must reconstruct exactly and reject corruption."""
import copy
import random
import unittest
from next20_shifted_binary import encode,decode,digest


class ShiftedBinaryTests(unittest.TestCase):
    def test_shifted_binary_restores_inserted_removed_and_changed_bytes(self):
        base=random.Random(71).randbytes(100000);target=b'new header'*31+base[:40000]+b'inserted'+base[40009:]+b'tail'
        payload,record=encode(base,target)
        self.assertEqual(decode(base,payload,record),target)
        self.assertLess(len(payload),len(target)//2)

    def test_shifted_binary_refuses_missing_dictionary_and_rehashed_truncation(self):
        base=random.Random(8).randbytes(10000);payload,record=encode(base,b'prefix'+base)
        with self.assertRaises(ValueError):decode(b'wrong',payload,record)
        for changed in [payload[:-1],payload+b'trailing']:
            row=copy.deepcopy(record);row.update(delta_bytes=len(changed),delta_sha256=digest(changed))
            with self.assertRaises(ValueError):decode(base,changed,row)
        row=copy.deepcopy(record);row['target_sha256']='0'*64
        with self.assertRaises(ValueError):decode(base,payload,row)


if __name__=='__main__':unittest.main()
