import unittest

from next20_joe_final_qualification_audit import attempt_identity_from_path
from next20_joe_build import validate_source_fault_maps


class AttemptIdentityPathTests(unittest.TestCase):
    def test_extracts_ids_for_each_repetition_number_shape(self):
        attempt_id = "0123456789abcdef0123456789abcdef"
        for repetition in (0, 1, 9, 10, 11):
            with self.subTest(repetition=repetition):
                path = f"joe/final-qualification/linux/N01/r{repetition:02d}-{attempt_id}/attempt.json"
                self.assertEqual(attempt_identity_from_path(path, repetition), attempt_id)

    def test_rejects_a_path_for_another_repetition(self):
        path = "joe/final-qualification/linux/N01/r01-0123456789abcdef0123456789abcdef/attempt.json"
        with self.assertRaisesRegex(ValueError, "repetition prefix"):
            attempt_identity_from_path(path, 0)

    def test_rejects_malformed_attempt_ids(self):
        path = "joe/final-qualification/linux/N01/r11-not-a-valid-attempt/attempt.json"
        with self.assertRaisesRegex(ValueError, "lowercase 128-bit hex ID"):
            attempt_identity_from_path(path, 11)


class SourceFaultMapTests(unittest.TestCase):
    def test_accepts_only_the_one_declared_changed_source_file(self):
        pristine = {"joe/b.c": "a" * 64, "joe/ufile.c": "b" * 64}
        actual = {"joe/b.c": "c" * 64, "joe/ufile.c": "b" * 64}
        declaration = {"source_file": "joe/b.c", "baseline_source_sha256": "a" * 64,
                       "mutated_source_sha256": "c" * 64}
        self.assertEqual(validate_source_fault_maps(pristine, actual, declaration), "joe/b.c")

    def test_rejects_an_undeclared_second_change(self):
        pristine = {"joe/b.c": "a" * 64, "joe/ufile.c": "b" * 64}
        actual = {"joe/b.c": "c" * 64, "joe/ufile.c": "d" * 64}
        declaration = {"source_file": "joe/b.c", "baseline_source_sha256": "a" * 64,
                       "mutated_source_sha256": "c" * 64}
        with self.assertRaisesRegex(ValueError, "exactly one"):
            validate_source_fault_maps(pristine, actual, declaration)

    def test_rejects_added_or_removed_source_paths(self):
        pristine = {"joe/b.c": "a" * 64}
        declaration = {"source_file": "joe/b.c", "baseline_source_sha256": "a" * 64,
                       "mutated_source_sha256": "c" * 64}
        with self.assertRaisesRegex(ValueError, "exactly one"):
            validate_source_fault_maps(pristine, {"joe/b.c": "c" * 64, "joe/new.c": "d" * 64}, declaration)


if __name__ == "__main__":
    unittest.main()
