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
                '-Project','jrnl'],'core',label,cwd=ROOT,env=owned_environment(),timeout=30,
                expected=expected,campaign=self.campaign)
        rejected=asyncio.run(run(1,'native-removal-changed-payload-refusal'))
        self.assertTrue(target.is_dir());self.assertIn('changed after checked retention',rejected['output'])
        data.write_bytes(original)
        asyncio.run(run(0,'native-removal-exact-owned-fixture'))
        self.assertFalse(target.exists())
        self.assertTrue(json.loads((retained/'removed.json').read_text(encoding='utf-8-sig'))['removed'])


if __name__=='__main__':unittest.main()
