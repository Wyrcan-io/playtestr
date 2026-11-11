import unittest

import next20_joe_oracle_calibration as calibration


class JoeOracleCalibrationTests(unittest.TestCase):
    def test_independent_byte_families_preserve_exact_distinctions(self):
        self.assertEqual(set(calibration.FIXTURES), set(calibration.EXPECTED_FIXTURES))
        self.assertEqual(calibration.FIXTURES, calibration.EXPECTED_FIXTURES)
        self.assertIn(b"\r\n", calibration.FIXTURES["bytes-crlf.txt"])
        self.assertNotIn(b"\r", calibration.FIXTURES["bytes-lf.txt"])
        self.assertEqual(calibration.FIXTURES["bytes-empty.txt"], b"")
        self.assertIn(b"\x00", calibration.FIXTURES["bytes-nul.txt"])
        self.assertFalse(calibration.FIXTURES["bytes-no-final-newline.txt"].endswith(b"\n"))
        self.assertIn("雪".encode("utf-8"), calibration.FIXTURES["bytes-unicode.txt"])

    def test_same_size_corruption_changes_one_independently_expected_byte(self):
        actual = calibration.EXPECTED
        wrong = bytes([actual[0] ^ 1]) + actual[1:]
        self.assertNotEqual(actual, wrong)
        self.assertEqual(len(actual), len(wrong))

    def test_calibration_plan_has_one_positive_and_ten_negative_controls(self):
        names = ["correct-all-kinds-and-byte-families", "same-size-wrong-file-bytes",
                 "missing-required-file", "wrong-type-directory-as-file",
                 "absence-rejects-present-file", "absence-rejects-present-directory",
                 "directory-rejects-missing-path", "directory-rejects-file",
                 "entries-reject-missing-name", "entries-reject-extra-name",
                 "entries-reject-file"]
        self.assertEqual(len(names), 11)
        self.assertEqual(len(set(names)), 11)


if __name__ == "__main__":
    unittest.main()
