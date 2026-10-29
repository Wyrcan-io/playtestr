import copy
import unittest

from next20_local_native_references import reference_for,resolve


class LocalNativeReferenceTests(unittest.TestCase):
    def test_exact_bytes_required_and_changed_missing_unsafe_inputs_refused(self):
        body=b'reviewed binary\x00\r\n';records={'native/1/base/hatch/wheels/exact.whl':body}
        row=reference_for('wheels/exact.whl',body,records)
        manifest=dict(schema_version=1,files={'wheels/exact.whl':row})
        self.assertEqual(resolve('wheels/exact.whl',manifest,records),body)
        self.assertIsNone(reference_for('wheels/exact.whl',body+b'x',records))
        self.assertIsNone(reference_for('../exact.whl',body,records))
        self.assertIsNone(reference_for('runtime.json',body,records))
        for changed in [{},{'native/1/base/hatch/wheels/exact.whl':body+b'x'}]:
            with self.assertRaises(ValueError):resolve('wheels/exact.whl',manifest,changed)
        altered=copy.deepcopy(manifest);altered['files']['wheels/exact.whl']['sha256']='0'*64
        with self.assertRaises(ValueError):resolve('wheels/exact.whl',altered,records)
        with self.assertRaises(ValueError):resolve('../exact.whl',manifest,records)


if __name__=='__main__':unittest.main()
