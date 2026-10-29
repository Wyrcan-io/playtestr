"""Runtime revisions must select their own files and never escape the target."""
from pathlib import Path
import unittest
import uuid
from next20_check import RAW
from next20_python_runtime import python_runtime_root


class PythonRuntimeTests(unittest.TestCase):
    def test_declared_python_revision_selects_new_runtime_and_refuses_old_or_escaped(self):
        target=RAW/'control-tests'/('python-runtime-'+uuid.uuid4().hex)
        for name in ['venv','venv-v2']:
            root=target/name;root.mkdir(parents=True);(root/'python').write_bytes(name.encode())
        old=dict(python=str(target/'venv/python'));new=dict(python=str(target/'venv-v2/python'),runtime_directory='venv-v2')
        self.assertEqual(python_runtime_root(target,old),target.resolve()/'venv')
        self.assertEqual(python_runtime_root(target,new),target.resolve()/'venv-v2')
        for directory,python in [('../outside',new['python']),('venv',new['python']),('C:/elsewhere',old['python'])]:
            with self.assertRaises(ValueError):python_runtime_root(target,dict(runtime_directory=directory,python=python))


if __name__=='__main__':unittest.main()
