"""Calibrate real-process bounds and independent file oracles before credit."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import adversarial_process
from adversarial_process import run
from adversarial_journey import check_state

class NativeHarnessControls(unittest.TestCase):
    def test_cleanup_failure_keeps_original_failure_and_finished_record(self):
        original_stop=adversarial_process.stop
        async def failing_cleanup(proc):
            await original_stop(proc)
            raise RuntimeError('synthetic cleanup fault after actual termination')
        with patch.object(adversarial_process,'stop',failing_cleanup):
            with self.assertRaisesRegex(RuntimeError,'expected exit 0, got 7') as raised:
                run([sys.executable,'-c','import sys;sys.exit(7)'],
                    'harness-controls','preserve-original-cleanup-failure',timeout=5)
        self.assertTrue(any('Separate cleanup failures' in note for note in raised.exception.__notes__))
        rows=[json.loads(line) for line in (adversarial_process.DOC/'attempts.jsonl').read_text(encoding='utf-8').splitlines()]
        finished=next(row for row in reversed(rows) if row['id']==raised.exception.evidence_id and row['event']=='finished')
        self.assertEqual(finished['category'],'exit_mismatch')
        self.assertEqual(finished['harness_cleanup'],'harness_cleanup_unconfirmed')
        self.assertEqual(len(finished['cleanup_errors']),1)

    def test_cleanup_failure_cannot_turn_into_success(self):
        original_stop=adversarial_process.stop
        async def failing_cleanup(proc):
            await original_stop(proc)
            raise RuntimeError('synthetic cleanup fault after actual termination')
        with patch.object(adversarial_process,'stop',failing_cleanup):
            with self.assertRaisesRegex(RuntimeError,'Separate cleanup failures'):
                run([sys.executable,'-c','pass'],'harness-controls','reject-green-cleanup-failure',timeout=5)

    def test_utf8_and_exact_nonzero(self):
        result=run([sys.executable,'-c',"import sys;sys.stdout.buffer.write('café\\n'.encode());sys.exit(7)"],
                   'harness-controls','unicode-exact-nonzero',expected=7,timeout=5)
        self.assertEqual(result['output'],'café\n')

    def test_real_timeout_is_bounded(self):
        with self.assertRaises(asyncio.TimeoutError):
            run([sys.executable,'-c','import time;time.sleep(30)'],
                'harness-controls','real-timeout',timeout=0.4)

    def test_real_flood_is_bounded(self):
        with self.assertRaisesRegex(RuntimeError,'output cap'):
            run([sys.executable,'-c',"import os\nwhile True: os.write(1,b'x'*16384)"],
                'harness-controls','real-flood',timeout=5,output_cap=32768)

    def test_wrong_and_missing_state_do_not_pass(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-oracle-') as root:
            working=Path(root)/'fixture'
            working.mkdir()
            target=working/'saved.txt'
            case=dict(expected_files={'saved.txt':'café\n'},absent_paths=['forbidden.txt'])
            target.write_bytes('café\n'.encode())
            self.assertTrue(check_state(working,case)['passed'])
            target.write_bytes(b'wrong state\n')
            with self.assertRaisesRegex(RuntimeError,'state mismatch'):
                check_state(working,case)
            target.unlink()
            with self.assertRaisesRegex(RuntimeError,'absent or unsafe'):
                check_state(working,case)
            target.write_bytes('café\n'.encode())
            (working/'forbidden.txt').write_bytes(b'exists')
            with self.assertRaisesRegex(RuntimeError,'absence mismatch'):
                check_state(working,case)

    def test_oversized_file_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-oracle-') as root:
            working=Path(root)/'fixture'
            working.mkdir()
            (working/'large').write_bytes(b'x'*(4*1024*1024+1))
            with self.assertRaisesRegex(RuntimeError,'size bound'):
                check_state(working,dict(expected_files={'large':'x'}))

    def test_escape_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-oracle-') as root:
            working=Path(root)/'fixture'
            working.mkdir()
            (Path(root)/'outside').write_bytes(b'x')
            with self.assertRaises(ValueError):
                check_state(working,dict(expected_files={'../outside':'x'}))

    def test_inside_workspace_symlink_does_not_pass(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-oracle-') as root:
            working=Path(root)/'fixture'
            working.mkdir()
            (working/'actual').write_bytes(b'approved')
            try:
                (working/'linked').symlink_to('actual')
            except OSError as error:
                self.skipTest('Native symlink prerequisite unavailable: '+str(error))
            with self.assertRaisesRegex(RuntimeError,'linked state'):
                check_state(working,dict(expected_files={'linked':'approved'}))

if __name__=='__main__':
    unittest.main()
