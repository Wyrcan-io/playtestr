"""Calibrate real-process bounds and independent file oracles before credit."""
import asyncio
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import adversarial_process
from adversarial_process import run
from adversarial_journey import check_state
from adversarial_fixture_directories import prepare
from adversarial_project_maintenance import copy_spec_fixture
from adversarial_setup_python import source_identity
from adversarial_final_audit import repetition_group

class NativeHarnessControls(unittest.TestCase):
    def test_final_repetition_group_excludes_initial_state_and_rejects_bad_parent(self):
        attempts={};positions={};ordinal=0
        def event(ident,kind,**fields):
            nonlocal ordinal
            attempts.setdefault(ident,{})[kind]=fields
            positions[(ident,kind)]=ordinal;ordinal+=1
        event('initial','started',project='sample',label='case-state-probe')
        event('initial','finished',category='passed')
        event('group','started',project='sample',label='native-repetitions-case')
        event('group','launched')
        ordinary=[];state=[]
        for index in range(10):
            child='ordinary-'+str(index);ordinary.append(child)
            event(child,'started');event(child,'finished',category='passed')
            if index==9:continue
            child='state-'+str(index);state.append(child)
            event(child,'started');event(child,'finished',category='passed')
        event('group','finished',category='passed',cleanup_errors=[])
        group,members=repetition_group(attempts,positions,'sample','case',ordinary)
        self.assertEqual(group,'group')
        self.assertNotIn('initial',members)
        self.assertEqual(len(set(state)|{'initial'}),10)
        self.assertEqual(len(members.intersection(set(state)|{'initial'})),9)
        for category in ['failed','harness_error']:
            with self.subTest(category=category):
                attempts['group']['finished']['category']=category
                with self.assertRaisesRegex(RuntimeError,'repetition group failed'):
                    repetition_group(attempts,positions,'sample','case',ordinary)

    def test_interpreted_identity_tracks_contained_links_and_rejects_escape(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-interpreted-source-') as directory:
            root=Path(directory);source=root/'source';source.mkdir()
            target=source/'actual.py';target.write_bytes(b'approved = True\n')
            link=source/'documented.py'
            try:link.symlink_to('actual.py')
            except OSError as error:self.skipTest('Native file-link prerequisite unavailable: '+str(error))
            before=source_identity(source)
            self.assertEqual(before['files_sha256']['actual.py'],before['files_sha256']['documented.py'])
            target.write_bytes(b'approved = False\n')
            self.assertNotEqual(before['digest'],source_identity(source)['digest'])
            outside=root/'outside.py';outside.write_bytes(b'private = True\n')
            link.unlink();link.symlink_to('../outside.py')
            with self.assertRaisesRegex(RuntimeError,'Unsafe interpreted source'):
                source_identity(source)

    def test_exact_tree_rejects_collateral_hidden_file(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-oracle-') as root:
            working=Path(root)/'fixture';working.mkdir()
            (working/'nested').mkdir()
            (working/'nested/saved.txt').write_bytes(b'approved')
            case=dict(expected_files={'nested/saved.txt':'approved'},exact_tree=True)
            self.assertTrue(check_state(working,case)['passed'])
            (working/'.unexpected').write_bytes(b'collateral write')
            with self.assertRaisesRegex(RuntimeError,'exact tree mismatch'):
                check_state(working,case)

    @unittest.skipIf(os.name=='nt','Unix signal fallback requires native process groups')
    def test_signal_permission_failure_still_stops_owned_group(self):
        import signal
        async def exercise():
            command='import signal,time; signal.signal(signal.SIGINT,signal.SIG_IGN); print("ready",flush=True); time.sleep(60)'
            proc=await asyncio.create_subprocess_exec(sys.executable,'-c',command,
                stdout=asyncio.subprocess.PIPE,start_new_session=True)
            actual_kill=os.kill
            def denied_direct_kill(pid,sig):
                if pid==proc.pid and sig==signal.SIGKILL:
                    raise PermissionError('injected native direct-PID permission failure')
                return actual_kill(pid,sig)
            try:
                self.assertEqual(await asyncio.wait_for(proc.stdout.readline(),timeout=3),b'ready\n')
                with patch.object(adversarial_process.os,'kill',side_effect=denied_direct_kill):
                    with self.assertRaisesRegex(RuntimeError,'Separate owned termination failures'):
                        await adversarial_process.stop(proc)
                await asyncio.wait_for(proc.wait(),timeout=2)
                self.assertEqual(proc.returncode,-signal.SIGKILL)
            finally:
                if proc.returncode is None:
                    os.killpg(proc.pid,signal.SIGKILL)
                    await asyncio.wait_for(proc.wait(),timeout=2)
                await adversarial_process.close_transport(proc)
        asyncio.run(exercise())

    def test_declared_empty_directory_rejects_hidden_contents(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-oracle-') as directory:
            working=Path(directory)/'fixture';working.mkdir();empty=working/'empty';empty.mkdir()
            case=dict(expected_directories=['empty'],empty_directories=['empty'])
            self.assertTrue(check_state(working,case)['passed'])
            (empty/'.unexpected').write_bytes(b'not empty')
            with self.assertRaisesRegex(RuntimeError,'expected empty directory'):
                check_state(working,case)

    def test_owned_source_refuses_unmarked_existing_files(self):
        from adversarial_owned_source import claim
        with tempfile.TemporaryDirectory(prefix='playtestr-owned-') as directory:
            root=Path(directory);app=root/'sample';app.mkdir()
            (app/'preserve.txt').write_bytes(b'preserve')
            with self.assertRaisesRegex(RuntimeError,'nonempty unmarked'):
                claim(root,'sample','a'*40)
            self.assertEqual((app/'preserve.txt').read_bytes(),b'preserve')
            self.assertFalse((app/'task-owned.json').exists())

    def test_owned_source_identity_and_single_application(self):
        from adversarial_owned_source import claim
        with tempfile.TemporaryDirectory(prefix='playtestr-owned-') as directory:
            root=Path(directory)
            app=claim(root,'sample','a'*40)
            self.assertEqual(claim(root,'sample','a'*40),app)
            with self.assertRaisesRegex(RuntimeError,'Unknown existing'):
                claim(root,'sample','b'*40)
            with self.assertRaisesRegex(RuntimeError,'Another owned application'):
                claim(root,'other','b'*40)
            self.assertFalse((root/'other').exists())

    @unittest.skipIf(os.name=='nt','Unix nested sessions require native process-group diagnosis')
    def test_outer_timeout_reaps_nested_helper_session(self):
        import signal
        with tempfile.TemporaryDirectory(prefix='playtestr-nested-cleanup-') as root:
            pidfile=Path(root)/'owned-child.pid'
            child='import os,pathlib,time; pathlib.Path('+repr(str(pidfile))+').write_text(str(os.getpid())); time.sleep(60)'
            helper=('import sys; sys.path.insert(0,'+repr(str(adversarial_process.ROOT/'scripts/acceptance'))+'); '
                    'from adversarial_process import run; run([sys.executable,"-c",'+repr(child)+'], '
                    '"harness-controls","owned-nested-child",timeout=60)')
            pid=None
            try:
                with self.assertRaises(asyncio.TimeoutError):
                    run([sys.executable,'-c',helper],'harness-controls','outer-nested-deadline',timeout=5)
                self.assertTrue(pidfile.is_file(),'Controlled nested child never launched')
                pid=int(pidfile.read_text(encoding='utf-8'))
                try:os.kill(pid,0)
                except ProcessLookupError:pass
                else:self.fail('Outer deadline left its owned nested child session alive')
            finally:
                if pid is None and pidfile.exists():pid=int(pidfile.read_text(encoding='utf-8'))
                if pid is not None:
                    try:os.killpg(pid,signal.SIGKILL)
                    except ProcessLookupError:pass

    def test_command_deadline_includes_contract_capture(self):
        def delayed_identity(project,argv):
            time.sleep(0.3)
            return {'synthetic_calibration':'bounded identity delay'}
        with patch.object(adversarial_process,'contract_identity',delayed_identity):
            with self.assertRaises(asyncio.TimeoutError):
                run([sys.executable,'-c','import time;time.sleep(0.3)'],
                    'harness-controls','deadline-includes-provenance',timeout=0.5)
            with tempfile.TemporaryDirectory(prefix='playtestr-deadline-control-') as root:
                marker=Path(root)/'launched.txt'
                with self.assertRaises(asyncio.TimeoutError):
                    run([sys.executable,'-c','import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes(b"launched")',marker],
                        'harness-controls','expired-provenance-never-launches',timeout=0.1)
                self.assertFalse(marker.exists())

    def test_maintenance_uses_declared_fixture_and_preserves_empty_directories(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-maintenance-control-') as root:
            package=Path(root)/'package'
            (package/'nested/reviewed/empty').mkdir(parents=True)
            (package/'nested/reviewed/file.txt').write_bytes(b'reviewed bytes')
            destination=Path(root)/'moved'
            copy_spec_fixture(package,destination,{'workspace':{'fixture':'nested/reviewed'}})
            self.assertEqual((destination/'nested/reviewed/file.txt').read_bytes(),b'reviewed bytes')
            self.assertTrue((destination/'nested/reviewed/empty').is_dir())
            with self.assertRaisesRegex(RuntimeError,'safe explicit relative fixture'):
                copy_spec_fixture(package,Path(root)/'unsafe',{'workspace':{'fixture':'../escape'}})
            self.assertFalse((Path(root)/'unsafe').exists())

    def test_directory_oracle_checks_real_type_missing_state_and_escape(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-workspace-') as root:
            working=Path(root)/'fixture'
            working.mkdir()
            (working/'created/sub').mkdir(parents=True)
            case={'expected_directories':['created','created/sub']}
            self.assertEqual(check_state(working,case)['directories'],case['expected_directories'])
            with self.assertRaisesRegex(RuntimeError,'absent or wrong type'):
                check_state(working,{'expected_directories':['missing']})
            (working/'wrong-type').write_bytes(b'not a directory')
            with self.assertRaisesRegex(RuntimeError,'absent or wrong type'):
                check_state(working,{'expected_directories':['wrong-type']})
            with self.assertRaises(ValueError):
                check_state(working,{'expected_directories':['../../escape']})

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

    def test_ledger_transient_missing_lock_requires_existing_parent_and_deadline(self):
        with tempfile.TemporaryDirectory(prefix='playtestr-ledger-controls-') as root:
            raw=Path(root)/'raw'
            raw.mkdir()
            original=Path.mkdir
            calls=[]
            def transient(path,*args,**kwargs):
                if path.name=='.attempts-lock':
                    calls.append(path)
                    if len(calls)==1:raise FileNotFoundError('synthetic delete-pending lock')
                return original(path,*args,**kwargs)
            with patch.object(adversarial_process,'RAW',raw),patch.object(Path,'mkdir',transient):
                with adversarial_process.ledger_lock():
                    self.assertTrue((raw/'.attempts-lock').is_dir())
                self.assertEqual(len(calls),2)
            def persistent(path,*args,**kwargs):
                if path.name=='.attempts-lock':raise FileNotFoundError('persistent missing lock')
                return original(path,*args,**kwargs)
            with patch.object(adversarial_process,'RAW',raw),patch.object(Path,'mkdir',persistent),patch.object(adversarial_process.time,'monotonic',side_effect=[0,11]):
                with self.assertRaisesRegex(RuntimeError,'ledger lock deadline'):
                    with adversarial_process.ledger_lock():self.fail('persistent fault acquired lock')
            def removed_parent(path,*args,**kwargs):
                if path.name=='.attempts-lock':
                    raw.rmdir()
                    raise FileNotFoundError('actual parent disappeared')
                return original(path,*args,**kwargs)
            with patch.object(adversarial_process,'RAW',raw),patch.object(Path,'mkdir',removed_parent):
                with self.assertRaisesRegex(FileNotFoundError,'actual parent disappeared'):
                    with adversarial_process.ledger_lock():self.fail('missing parent acquired lock')
            self.assertFalse(raw.exists())

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
