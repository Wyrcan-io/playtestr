"""Calibrate real-process bounds and independent file oracles before credit."""
import asyncio
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import adversarial_process
from adversarial_process import run
from adversarial_journey import check_state
from adversarial_fixture_directories import prepare

class NativeHarnessControls(unittest.TestCase):
    def test_empty_fixture_directory_reconstruction_is_owned_and_prevalidated(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-fixture-dirs-') as root:
            package=Path(root)/'package'
            package.mkdir()
            (package/'scenarios.json').write_text(json.dumps({'fixture':'fixtures','cases':[{}]}))
            manifest=package/'fixture-directories.json'
            manifest.write_text(json.dumps(['fixtures/empty','../escape']))
            with self.assertRaisesRegex(RuntimeError,'Unsafe fixture directory path'):
                prepare(package)
            self.assertFalse((package/'fixtures').exists())
            self.assertFalse((Path(root)/'escape').exists())
            manifest.write_text(json.dumps(['fixtures/empty']))
            prepare(package)
            self.assertEqual(list((package/'fixtures/empty').iterdir()),[])
            (package/'fixtures/empty/protected.txt').write_bytes(b'protected')
            with self.assertRaisesRegex(RuntimeError,'not empty'):
                prepare(package)
            self.assertEqual((package/'fixtures/empty/protected.txt').read_bytes(),b'protected')

    def test_semantic_rejection_is_recorded_before_process_success(self):
        def reject(code,output,evidence):
            self.assertEqual(code,0)
            self.assertIn(b'actual final marker',output)
            raise RuntimeError('synthetic final semantic rejection')
        with self.assertRaisesRegex(RuntimeError,'synthetic final semantic rejection') as caught:
            run([sys.executable,'-c',"print('actual final marker')"],
                'harness-controls','final-semantic-rejection',timeout=5,on_complete=reject)
        rows=[r for r in adversarial_process.read_attempts() if r['id']==caught.exception.evidence_id]
        finished=next(r for r in rows if r['event']=='finished')
        self.assertNotEqual(finished['category'],'passed')
        self.assertEqual(finished['exit_code'],0)
        self.assertFalse(finished['cleanup_errors'])

    def test_concurrent_ledger_writers_preserve_every_record(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-ledger-controls-') as root:
            directory=Path(root)/'doc'
            raw=Path(root)/'raw'
            program="import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import adversarial_process as a;a.DOC=Path(sys.argv[2]);a.RAW=Path(sys.argv[3]);writer=sys.argv[4]\nfor i in range(20): a.append({'id':writer+'-'+str(i),'event':'synthetic','payload':'x'*4096})"
            processes=[]
            try:
                for writer in range(4):
                    processes.append(subprocess.Popen([sys.executable,'-c',program,
                        str(Path(__file__).parent),str(directory),str(raw),str(writer)],
                        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT))
                for process in processes:
                    output,_=process.communicate(timeout=15)
                    self.assertLessEqual(len(output),4096)
                    self.assertEqual(process.returncode,0,output.decode(errors='replace'))
                with patch.object(adversarial_process,'DOC',directory),patch.object(adversarial_process,'RAW',raw):
                    rows=adversarial_process.read_attempts()
                self.assertEqual(len(rows),80)
                self.assertEqual({r['id'] for r in rows},{str(w)+'-'+str(i) for w in range(4) for i in range(20)})
                self.assertTrue(all(r['payload']=='x'*4096 for r in rows))
                self.assertFalse((raw/'.attempts-lock').exists())
            finally:
                for process in processes:
                    if process.poll() is None: process.kill()
                    process.wait(timeout=5)
                    if process.stdout: process.stdout.close()

    def test_unknown_ledger_damage_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-ledger-controls-') as root:
            directory=Path(root)
            ledger=directory/'attempts.jsonl'
            ledger.write_bytes(b'{"id":"valid","event":"synthetic"}\ntruncated unknown fragment\n')
            with patch.object(adversarial_process,'DOC',directory):
                with self.assertRaisesRegex(RuntimeError,'Unknown campaign ledger damage'):
                    adversarial_process.read_ledger(ledger)

    @unittest.skipUnless(os.name=='nt','Windows delete-pending directory convention')
    def test_ledger_delete_pending_retry_is_bounded(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-ledger-controls-') as root:
            raw=Path(root)/'raw'
            raw.mkdir()
            original=Path.mkdir
            transient=PermissionError('synthetic native delete-pending directory')
            transient.winerror=5
            calls=[]
            def mkdir(path,*args,**kwargs):
                if path.name=='.attempts-lock':
                    calls.append(path)
                    if len(calls)==1: raise transient
                return original(path,*args,**kwargs)
            with patch.object(adversarial_process,'RAW',raw),patch.object(Path,'mkdir',mkdir):
                with adversarial_process.ledger_lock():
                    self.assertTrue((raw/'.attempts-lock').is_dir())
                self.assertEqual(len(calls),2)
                self.assertFalse((raw/'.attempts-lock').exists())
            def denied(path,*args,**kwargs):
                if path.name=='.attempts-lock': raise transient
                return original(path,*args,**kwargs)
            with patch.object(adversarial_process,'RAW',raw),patch.object(Path,'mkdir',denied),patch.object(adversarial_process.time,'monotonic',side_effect=[0,11]):
                with self.assertRaisesRegex(RuntimeError,'ledger lock deadline'):
                    with adversarial_process.ledger_lock():
                        self.fail('persistent denial acquired lock')
            self.assertFalse((raw/'.attempts-lock').exists())

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
        rows=adversarial_process.read_attempts()
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

    def test_expected_absence_rejects_dangling_symlink(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-oracle-') as root:
            working=Path(root)/'fixture'
            working.mkdir()
            try:
                (working/'ghost').symlink_to('missing')
            except OSError as error:
                self.skipTest('Native symlink prerequisite unavailable: '+str(error))
            with self.assertRaisesRegex(RuntimeError,'linked state'):
                check_state(working,dict(absent_paths=['ghost']))

    @unittest.skipUnless(os.name=='nt','Windows junction control')
    def test_inside_workspace_junction_does_not_pass(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-oracle-') as root:
            working=Path(root)/'fixture'
            working.mkdir()
            actual=working/'actual-dir'
            actual.mkdir()
            (actual/'saved.txt').write_bytes(b'approved')
            link=working/'linked-dir'
            result=subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(link),str(actual)],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=5)
            if result.returncode!=0:
                self.skipTest('Native junction prerequisite unavailable')
            try:
                with self.assertRaisesRegex(RuntimeError,'linked state'):
                    check_state(working,dict(expected_files={'linked-dir/saved.txt':'approved'}))
            finally:
                if link.is_junction(): os.rmdir(link) # Exact nonrecursive unlink.

if __name__=='__main__':
    unittest.main()
