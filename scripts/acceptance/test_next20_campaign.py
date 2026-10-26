"""Campaign root separation and actual bounded command outcome controls."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
import uuid

sys.dont_write_bytecode=True
from adversarial_process import execute
from next20_check import NAME, RAW, ROOT, NextCampaign, owned_environment
from readiness_evidence import Campaign, RAW as ORIGINAL_RAW
from readiness_evidence import immutable_json,sha256


class NextCampaignTests(unittest.TestCase):
    def setUp(self):
        self.root=RAW/'control-tests'/uuid.uuid4().hex
        self.campaign=NextCampaign(self.root)

    def test_malformed_fixture_is_retained_but_corrupt_report_still_refused(self):
        import io
        import tarfile
        from next20_target_cleanup import report_documents
        from next20_verify_jrnl import json_payloads
        from readiness_compact_native import verify
        fixture=self.root/'fixture/.yo-rc.json';fixture.parent.mkdir(parents=True)
        fixture.write_bytes(b'{invalid json\n')
        report=self.root/'E12.report.json'
        report.write_bytes(b'{"runner_version":"synthetic-control","results":[]}\n')
        self.assertEqual([p for p,_ in report_documents(self.root)],[report])
        names={'native/123/yo/host-contracts/fixtures/e12/.yo-rc.json':fixture.read_bytes(),
               'native/123/yo/final-series/0/E12.report.json':report.read_bytes()}
        import hashlib
        files={n:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for n,data in names.items()}
        archive=self.root/'packets.tar.gz'
        with tarfile.open(archive,'w:gz') as bundle:
            for name,data in names.items():
                member=tarfile.TarInfo(name);member.size=len(data);bundle.addfile(member,io.BytesIO(data))
        verify(archive,files)
        parsed=json_payloads(self.root,dict(files=files))
        self.assertEqual(set(parsed),{'native/123/yo/final-series/0/E12.report.json'})
        self.assertEqual(fixture.read_bytes(),b'{invalid json\n')
        report.write_bytes(b'{invalid report\n')
        with self.assertRaises(json.JSONDecodeError):list(report_documents(self.root))

    def test_registry_reference_refuses_changed_bytes_before_duplicate_removal(self):
        import gzip
        from unittest.mock import patch
        import next20_yo_registry_reference as registry
        raw=self.root/'raw';doc=self.root/'docs';retained=raw/'yo/retained-source'
        cache=retained/'npm-cache';payload=cache/'_cacache/content-v2/sha512/aa/bb/payload'
        payload.parent.mkdir(parents=True);original=gzip.compress(b'synthetic package source control',mtime=0)
        payload.write_bytes(original);relative=payload.relative_to(cache).as_posix()
        row=dict(bytes=len(original),sha256=sha256(payload));files={relative:row}
        (doc/'yo').mkdir(parents=True)
        immutable_json(doc/'yo/registry-payloads.json',dict(files=files,total_bytes=len(original)))
        immutable_json(retained/'cleanup-inventory.json',dict(files={'npm-cache/'+relative:row},retained={'npm-cache/'+relative:row['sha256']}))
        immutable_json(retained/'removed.json',dict(removed=True,cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json')))
        with patch.object(registry,'RAW',raw),patch.object(registry,'DOC',doc),patch.object(sys,'argv',['registry-reference-control']):
            payload.write_bytes(gzip.compress(b'changed synthetic source',mtime=0))
            with self.assertRaisesRegex(ValueError,'differ from retained canonical'):registry.main()
            self.assertTrue(payload.is_file());self.assertFalse((retained/'registry-source-reference.json').exists())
            payload.write_bytes(original);registry.main()
            self.assertFalse(payload.exists())
            reference=json.loads((retained/'registry-source-reference.json').read_text())
            self.assertEqual(reference['files'],files)

    def test_cleanup_inventory_default_and_explicit_large_tree_bound(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from next20_target_cleanup import target_inventory
        class Entry:
            name='payload'
            def __init__(self,index):self.index=index
            def relative_to(self,root):return Path(str(self.index))
            def is_symlink(self):return False
            def is_dir(self):return False
            def is_file(self):return True
            def stat(self):return SimpleNamespace(st_size=0)
        class Tree:
            def __init__(self,count):self.count=count
            def iterdir(self):return (Entry(i) for i in range(self.count))
        with patch('next20_target_cleanup.sha256',return_value='0'*64):
            self.assertEqual(len(target_inventory(Tree(40000))['files']),40000)
            with self.assertRaisesRegex(ValueError,'inventory bound'):target_inventory(Tree(40001))
            self.assertEqual(len(target_inventory(Tree(60000),max_files=60000)['files']),60000)
            with self.assertRaisesRegex(ValueError,'inventory bound'):target_inventory(Tree(60001),max_files=60000)
            with self.assertRaisesRegex(ValueError,'unreviewed'):target_inventory(Tree(0),max_files=60001)

    def test_uppercase_compiler_identity_binds_actual_source_and_tool_bytes(self):
        from next20_archive_controls import ArchiveControlCampaign
        compiler=self.root/'compiler/go.EXE';compiler.parent.mkdir(parents=True)
        compiler.write_bytes(b'synthetic identity-only compiler control\n')
        campaign=ArchiveControlCampaign(self.root)
        reference=campaign.identity('core',[compiler,'version'])
        value=json.loads((self.root/reference['manifest']).read_text())
        self.assertEqual(value['runtime_executables']['go'],sha256(compiler))
        self.assertEqual(value['files']['cmd/fixture/main.go'],sha256(ROOT/'cmd/fixture/main.go'))
        self.assertEqual(value['read_only_compiler_path'],str(compiler.resolve()))

    def test_sdk_root_argument_preserves_default_and_uses_explicit_owned_root(self):
        from unittest.mock import patch
        import readiness_bootstrap_go as bootstrap
        class StopBeforeNetwork(Exception):pass
        historical_root=bootstrap.RAW
        default_root=self.root/'default-campaign'
        explicit=self.root/'explicit-campaign/toolchain'
        with patch.object(bootstrap,'RAW',default_root),patch.object(bootstrap.urllib.request,'urlopen',side_effect=StopBeforeNetwork):
            with self.assertRaises(StopBeforeNetwork):bootstrap.main()
            self.assertTrue((default_root/'toolchain').is_dir())
            with self.assertRaises(StopBeforeNetwork):bootstrap.main(owned=explicit)
            self.assertTrue(explicit.is_dir())
        self.assertEqual(bootstrap.RAW,historical_root)

    def test_exclusive_events_have_new_campaign_without_changing_historical_default(self):
        self.assertNotEqual(RAW,ORIGINAL_RAW)
        self.assertEqual(Campaign.__init__.__defaults__,(ORIGINAL_RAW,))
        row=dict(id=uuid.uuid4().hex,event='started',project='core',label='exclusive-event-control')
        self.campaign.append(row)
        path=self.root/'events'/(row['id']+'-started.json')
        self.assertEqual(json.loads(path.read_text())['campaign'],NAME)
        original=path.read_bytes()
        with self.assertRaises(FileExistsError):self.campaign.append(dict(row,label='overwrite'))
        self.assertEqual(path.read_bytes(),original)

    def test_rejects_cross_campaign_destination(self):
        with self.assertRaises(ValueError):NextCampaign(ORIGINAL_RAW)
        with self.assertRaises(ValueError):NextCampaign(ROOT)

    def test_actual_target_source_change_gets_new_prelaunch_identity(self):
        target=self.root/'active'/'synthetic-control'
        source=target/'src';source.mkdir(parents=True)
        path=source/'implementation.py';path.write_bytes(b'VALUE = 1\n')
        first=self.campaign.identity('synthetic-control',[sys.executable,'-B','-c','pass'])
        path.write_bytes(b'VALUE = 2\n')
        second=self.campaign.identity('synthetic-control',[sys.executable,'-B','-c','pass'])
        self.assertNotEqual(first['sha256'],second['sha256'])
        manifest=json.loads((self.root/'identities'/ (second['sha256']+'.json')).read_text())
        catalog=json.loads((self.root/manifest['target_catalog']['manifest']).read_text())
        import hashlib
        self.assertEqual(catalog['files'][path.relative_to(ROOT).as_posix()],hashlib.sha256(path.read_bytes()).hexdigest())

    def test_owned_node_runtime_catalog_rejects_changed_executable(self):
        # Identity-only synthetic bytes; this does not claim Node execution.
        legacy=self.root/'active/python-control';legacy.mkdir(parents=True)
        python=legacy/'python.exe';python.write_bytes(b'synthetic legacy identity\n')
        immutable_json(legacy/'runtime.json',dict(python=str(python),python_sha256=sha256(python)))
        old=self.campaign.identity('python-control',[sys.executable,'-B','-c','pass'])
        old_manifest=json.loads((self.root/old['manifest']).read_text())
        old_catalog=json.loads((self.root/old_manifest['target_catalog']['manifest']).read_text())
        self.assertEqual(old_catalog['files'][python.relative_to(ROOT).as_posix()],sha256(python))
        target=self.root/'active/runtime-control';target.mkdir(parents=True)
        executable=target/'node.exe';executable.write_bytes(b'synthetic runtime identity\n')
        immutable_json(target/'runtime.json',dict(kind='node',node=str(executable),node_sha256=sha256(executable)))
        reference=self.campaign.identity('runtime-control',[sys.executable,'-B','-c','pass'])
        manifest=json.loads((self.root/reference['manifest']).read_text())
        catalog=json.loads((self.root/manifest['target_catalog']['manifest']).read_text())
        self.assertEqual(catalog['files'][executable.relative_to(ROOT).as_posix()],sha256(executable))
        executable.write_bytes(b'changed synthetic runtime\n')
        with self.assertRaisesRegex(ValueError,'executable changed'):
            self.campaign.identity('runtime-control',[sys.executable,'-B','-c','pass'])

    def test_actual_success_and_expected_nonzero_keep_distinct_execution_ids(self):
        async def check():
            first=await execute([sys.executable,'-B','-c','print("positive child output")'],
                'core','adapter-success',cwd=ROOT,env=owned_environment(),timeout=15,campaign=self.campaign)
            second=await execute([sys.executable,'-B','-c','raise SystemExit(7)'],
                'core','adapter-expected-nonzero',cwd=ROOT,env=owned_environment(),timeout=15,
                expected=7,campaign=self.campaign)
            return first,second
        first,second=asyncio.run(check())
        self.assertIn('positive child output',first['output'])
        self.assertNotEqual(first['id'],second['id'])
        rows=self.campaign.attempts()
        for result in [first,second]:
            events=rows[result['id']]
            self.assertEqual(set(events),{'started','identified','launched','finished'})
            self.assertEqual(events['finished']['category'],'passed')
            self.assertEqual(events['finished']['harness_cleanup'],'harness_process_reaped')
        self.assertEqual(rows[second['id']]['finished']['exit_code'],7)

    def test_actual_timeout_is_failed_and_process_is_reaped(self):
        async def check():
            with self.assertRaises(TimeoutError):
                await execute([sys.executable,'-B','-c','import time; time.sleep(20)'],
                    'core','adapter-timeout',cwd=ROOT,env=owned_environment(),timeout=1,
                    campaign=self.campaign)
        asyncio.run(check())
        rows=self.campaign.attempts()
        self.assertEqual(len(rows),1)
        finish=next(iter(rows.values()))['finished']
        self.assertEqual(finish['category'],'harness_timeout')
        self.assertEqual(finish['harness_cleanup'],'harness_process_reaped')

    def test_failed_engineering_command_exposes_its_retained_console(self):
        marker='synthetic-failed-command-output-visible'
        async def check():
            return await execute([sys.executable,'-B',ROOT/'scripts/acceptance/next20_check.py',
                '--label','failed-console-regression-'+uuid.uuid4().hex,'--timeout','15','--',
                sys.executable,'-B','-c','import sys; print('+repr(marker)+'); sys.exit(3)'],
                'core','failed-console-visibility-control',cwd=ROOT,env=owned_environment(),timeout=30,
                expected=1,campaign=self.campaign)
        result=asyncio.run(check())
        self.assertIn(marker,result['output'])
        self.assertIn('expected exit 0, got 3',result['output'])

    @unittest.skipUnless(os.name=='nt','native Windows checked target removal control')
    def test_native_large_cleanup_requires_matching_explicit_bound(self):
        workspace=self.root/'fixture-workspace'
        script=workspace/'scripts/acceptance/next20_remove_target.ps1';script.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/'scripts/acceptance/next20_remove_target.ps1',script)
        raw=workspace/'artifacts'/NAME;target=raw/'active/yo';target.mkdir(parents=True)
        marker=target/'task-owned.json';marker.write_bytes(b'{"project":"synthetic-large-cleanup"}\n')
        retained=raw/'yo/retained-source';retained.mkdir(parents=True)
        immutable_json(retained/'cleanup-inventory.json',dict(owned_target=str(target),source_restored_exact=True,
            max_files=60000,owner_sha256=sha256(marker),owned_links={},
            files={marker.name:dict(bytes=marker.stat().st_size,sha256=sha256(marker))}))
        immutable_json(retained/'prepared.json',dict(cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json')))
        async def run(expected,extra,label):
            return await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',script,
                '-Project','yo',*extra],'core',label,cwd=ROOT,env=owned_environment(),timeout=90,
                expected=expected,campaign=self.campaign)
        refused=asyncio.run(run(1,[],'native-large-cleanup-default-bound-refusal'))
        self.assertIn('bound differs from prepared inventory',refused['output']);self.assertTrue(target.exists())
        asyncio.run(run(0,['-MaxFiles','60000'],'native-large-cleanup-explicit-bound'))
        self.assertFalse(target.exists())

    @unittest.skipUnless(os.name=='nt','native Windows checked target removal control')
    def test_native_target_removal_refuses_changed_payload_then_removes_exact_owned_fixture(self):
        # This is an actual native filesystem/process-observer guard control,
        # not target restoration or application compatibility evidence.
        workspace=self.root/'fixture-workspace'
        script=workspace/'scripts/acceptance/next20_remove_target.ps1'
        script.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/'scripts/acceptance/next20_remove_target.ps1',script)
        raw=workspace/'artifacts'/NAME;target=raw/'active/jrnl';target.mkdir(parents=True)
        marker=target/'task-owned.json';marker.write_bytes(b'{"project":"synthetic-cleanup-control"}\n')
        data=target/'payload.txt';data.write_bytes(b'approved owned payload\n')
        retained=raw/'jrnl/retained-source';retained.mkdir(parents=True)
        record=dict(owned_target=str(target),source_restored_exact=True,owner_sha256=sha256(marker),
            files={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in [marker,data]},owned_links={})
        immutable_json(retained/'cleanup-inventory.json',record)
        immutable_json(retained/'prepared.json',dict(cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json')))
        original=data.read_bytes();data.write_bytes(b'unknown changed payload\n')
        async def run(expected,label):
            return await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',script,
                '-Project','jrnl'],'core',label,cwd=ROOT,env=owned_environment(),timeout=90,
                expected=expected,campaign=self.campaign)
        rejected=asyncio.run(run(1,'native-removal-changed-payload-refusal'))
        self.assertTrue(target.is_dir());self.assertIn('changed after checked retention',rejected['output'])
        data.write_bytes(original)
        asyncio.run(run(0,'native-removal-exact-owned-fixture'))
        self.assertFalse(target.exists())
        self.assertTrue(json.loads((retained/'removed.json').read_text(encoding='utf-8-sig'))['removed'])


if __name__=='__main__':unittest.main()
