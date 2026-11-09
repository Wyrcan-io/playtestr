import hashlib
import unittest

from next20_skim_artifact_readback import DOC, find_hash_bound_document


class HashBoundDocumentTests(unittest.TestCase):
    def test_selects_document_using_frozen_hash_not_highest_version(self):
        old = b'{"version": 35}\n'
        current = b'{"version": 36}\n'
        payloads = {
            DOC + 'final-series-declaration-native-exit-v35.json': old,
            DOC + 'final-series-declaration-native-exit-v36.json': current,
        }
        name, data = find_hash_bound_document(
            payloads, 'final-series-declaration-native-exit-v',
            hashlib.sha256(current).hexdigest())
        self.assertEqual(name, 'final-series-declaration-native-exit-v36.json')
        self.assertEqual(data, current)

    def test_rejects_missing_hash_match(self):
        with self.assertRaisesRegex(ValueError, 'uniquely hash-bound'):
            find_hash_bound_document(
                {DOC + 'scenario-declaration-v5.json': b'{}'},
                'scenario-declaration-v', '0' * 64)

    def test_rejects_ambiguous_identical_documents(self):
        data = b'{"same": true}\n'
        digest = hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError, 'uniquely hash-bound'):
            find_hash_bound_document({
                DOC + 'scenario-declaration-v5.json': data,
                DOC + 'scenario-declaration-v6.json': data,
            }, 'scenario-declaration-v', digest)


if __name__ == '__main__':
    unittest.main()
