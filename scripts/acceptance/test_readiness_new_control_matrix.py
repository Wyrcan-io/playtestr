import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from readiness_evidence import RAW
import readiness_new_control_matrix as matrix


class NativeControlEvidenceTests(unittest.TestCase):
    def test_rejects_changed_manifest_and_unsuccessful_native_run(self):
        RAW.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW) as folder:
            root=Path(folder);run=root/'native/123'
            metadata=run/'run-metadata.json';run.mkdir(parents=True)
            metadata.write_text(json.dumps({'status':'completed','conclusion':'success','headSha':'a'*40}))
            for name in ['ubuntu-24.04','macos-15','windows-2025']:
                host=run/('control-'+name);(host/'events').mkdir(parents=True)
                (host/'core/attempt').mkdir(parents=True);(host/'identities').mkdir()
                manifest=host/'identities/known.json';manifest.write_text(json.dumps({'files':{}}))
                (host/'events/attempt-started.json').write_text(json.dumps({'expected_exit':0}))
                (host/'events/attempt-launched.json').write_text(json.dumps({'pid':123}))
                (host/'events/attempt-finished.json').write_text(json.dumps({'category':'passed','exit_code':0,
                    'cleanup_errors':[],'harness_cleanup':'harness_process_reaped'}))
                (host/'events/attempt-identified.json').write_text(json.dumps({'identity':{
                    'manifest':'identities/known.json','sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}}))
                (host/'core/attempt/console.log').write_text(json.dumps({'Action':'pass','Package':'owned/fixture','Test':'TestWholeControl'})+'\n')
            with patch.object(matrix,'RAW',root):
                self.assertEqual(len(matrix.packet_observations('123')),3)
                changed=run/'control-windows-2025/identities/known.json';original=changed.read_bytes()
                changed.write_bytes(original+b' ')
                with self.assertRaisesRegex(RuntimeError,'manifest changed'):matrix.packet_observations('123')
                changed.write_bytes(original)
                reference=run/'control-windows-2025/events/attempt-identified.json'
                approved=reference.read_bytes()
                for unsafe in ['../outside.json','/outside.json','C:/outside.json','identities/../../outside.json']:
                    reference.write_text(json.dumps({'identity':{'manifest':unsafe,'sha256':'0'*64}}))
                    with self.assertRaisesRegex(RuntimeError,'unsafe native packet reference'):
                        matrix.packet_observations('123')
                reference.write_bytes(approved)
                metadata.write_text(json.dumps({'status':'completed','conclusion':'failure','headSha':'a'*40}))
                with self.assertRaisesRegex(RuntimeError,'not successful'):matrix.packet_observations('123')


if __name__=='__main__':unittest.main()
