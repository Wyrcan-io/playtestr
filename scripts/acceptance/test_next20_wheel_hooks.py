import hashlib
import io
import unittest
import zipfile

from next20_wheel_hooks import reviewed_hooks


class WheelHookTests(unittest.TestCase):
    def test_unapproved_changed_or_extra_hooks_are_refused(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            archive.writestr('startup.pth',b'import owned_hook\n')
            archive.writestr('tool.data/scripts/tool.exe',b'synthetic native review input')
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
            digest=hashlib.sha256(stream.getvalue()).hexdigest()
            scripts={'tool.data/scripts/tool.exe':hashlib.sha256(b'synthetic native review input').hexdigest()}
            startup={'startup.pth':hashlib.sha256(b'import owned_hook\n').hexdigest()}
            good=dict(wheel_sha256=digest,scripts=scripts,startup_hooks=startup)
            self.assertEqual(reviewed_hooks(archive,digest,good),(scripts,startup))
            for bad in [{},dict(good,wheel_sha256='0'*64),dict(good,startup_hooks={}),dict(good,scripts={}),dict(good,startup_hooks=dict(startup,extra='0'*64))]:
                with self.assertRaises(ValueError):reviewed_hooks(archive,digest,bad)

    def test_script_only_historical_approval_and_no_hook_default(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:archive.writestr('ordinary.py',b'pass\n')
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:self.assertEqual(reviewed_hooks(archive,'digest',{}),({},{}))
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:archive.writestr('x.data/scripts/tool',b'tool')
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
            scripts={'x.data/scripts/tool':hashlib.sha256(b'tool').hexdigest()}
            self.assertEqual(reviewed_hooks(archive,'digest',dict(wheel_sha256='digest',scripts=scripts)),(scripts,{}))
