"""Native checked deletion of a tiny owned synthetic diagnostic workspace."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import uuid

from readiness_evidence import RAW, ROOT


class DiagnosticCleanupTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','native PowerShell cleanup is Windows only')
    def test_changed_marker_refuses_then_exact_owned_workspace_is_removed(self):
        reports=RAW/'experimental/native-root-diagnosis';reports.mkdir(parents=True,exist_ok=True)
        temporary=RAW/'tmp';temporary.mkdir(exist_ok=True)
        target=temporary/('playtestr-workspace-'+str(uuid.uuid4().int));target.mkdir()
        marker=target/'.playtestr-owner';marker.write_text('a'*32,encoding='ascii')
        (target/'fixture').mkdir();(target/'fixture/synthetic.txt').write_bytes(b'owned synthetic bytes')
        with tempfile.TemporaryDirectory(dir=reports) as folder:
            folder=Path(folder);canary=folder/'preserved.txt';canary.write_bytes(b'outside selected removal')
            report=folder/'report.json'
            report.write_text(json.dumps({'results':[{'cleanup':{'confirmed_exited':True},
                'workspace':{'retained':True,'retained_path':str(target)}}]}))
            command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                str(ROOT/'scripts/acceptance/readiness_remove_diagnostic_workspace.ps1'),'-Report',str(report),'-MarkerSHA256']
            wrong=subprocess.run(command+['0'*64],cwd=ROOT,capture_output=True,timeout=20)
            self.assertNotEqual(wrong.returncode,0);self.assertTrue((target/'fixture/synthetic.txt').is_file())
            actual=hashlib.sha256(marker.read_bytes()).hexdigest()
            correct=subprocess.run(command+[actual],cwd=ROOT,capture_output=True,timeout=20)
            self.assertEqual(correct.returncode,0,correct.stderr.decode(errors='replace'))
            self.assertFalse(target.exists());self.assertEqual(canary.read_bytes(),b'outside selected removal')


if __name__=='__main__':unittest.main()
