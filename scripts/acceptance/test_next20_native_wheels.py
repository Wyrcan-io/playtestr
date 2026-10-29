import copy
import unittest

from next20_native_wheels import validate_downloads


class NativeWheelTests(unittest.TestCase):
    def row(self):return dict(name='example-package',filename='example_package-1.0-py3-none-any.whl',sha256='a'*64,bytes=123,
        url='https://files.pythonhosted.org/packages/owned/example_package-1.0-py3-none-any.whl')

    def test_exact_frozen_filename_origin_size_and_digest_are_required(self):
        row=self.row();self.assertEqual(validate_downloads([row]),123)
        for change in [dict(filename='../escape.whl'),dict(name='../escape'),dict(sha256='x'*64),dict(bytes=True),dict(bytes=32*1024**2+1),
            dict(url='http://files.pythonhosted.org/packages/owned/example_package-1.0-py3-none-any.whl'),
            dict(url='https://example.invalid/example_package-1.0-py3-none-any.whl'),
            dict(url='https://user:secret@files.pythonhosted.org/example_package-1.0-py3-none-any.whl'),
            dict(url=row['url']+'?token=unused'),dict(url=row['url'].replace('example_package','other_package'))]:
            with self.subTest(change=change),self.assertRaises(ValueError):validate_downloads([dict(row,**change)])

    def test_duplicate_and_aggregate_forecasts_are_bounded(self):
        row=self.row()
        for rows in [[],[row,row],[row]*65]:
            with self.assertRaises(ValueError):validate_downloads(rows)
        rows=[]
        for i in range(3):
            item=copy.deepcopy(row);item.update(name='package-'+str(i),filename='package'+str(i)+'-1-py3-none-any.whl',bytes=32*1024**2)
            item['url']='https://files.pythonhosted.org/packages/'+item['filename'];rows.append(item)
        with self.assertRaises(ValueError):validate_downloads(rows)
