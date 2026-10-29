import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import random
import shutil
import tarfile
import unittest
from unittest.mock import patch
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,NextCampaign,owned_environment
import next20_native_packet_reader as reader
from readiness_evidence import immutable_json,sha256


class StagedNativeTests(unittest.TestCase):
    def test_explicit_large_packet_and_checked_staged_removal_promotion(self):
        outer=RAW/'control-tests'/('staged-native-'+uuid.uuid4().hex);workspace=outer/'fixture-workspace'
        root=workspace/'artifacts'/RAW.name;source=root/'native/123/synthetic';source.mkdir(parents=True)
        (root/'sample').mkdir();stage=root/'tmp/direct-native-zip/sample/retained-native-v1';stage.mkdir(parents=True)
        report=b'{"status":"synthetic actual report"}\n';large=random.Random(1).randbytes(17*1024**2)
        (source/'N01.report.json').write_bytes(report);(source/'large.whl').write_bytes(large)
        files={p.relative_to(root).as_posix():dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in source.iterdir()}
        archive=stage/'packets.tar.gz'
        with tarfile.open(archive,'w:gz') as stream:
            for name,row in files.items():
                member=tarfile.TarInfo(name);member.size=row['bytes'];stream.addfile(member,io.BytesIO((root/name).read_bytes()))
        index=dict(schema_version=2,project='sample',generation=1,runs=['123'],files=files,expanded_bytes=sum(r['bytes'] for r in files.values()),
            archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,max_file_bytes=32*1024**2,max_archive_bytes=48*1024**2)
        immutable_json(stage/'index.json',index)
        proof=dict(index_sha256=sha256(stage/'index.json'),archive_sha256=sha256(archive),members_verified=2)
        immutable_json(stage/'verified.json',proof);(stage/'selected-restore.bin').write_bytes(report)
        with patch.object(reader,'RAW',root):
            _,payloads=reader.read_packet('sample',1,stage=True)
            self.assertEqual(payloads['native/123/synthetic/large.whl'],large)
            self.assertEqual(payloads['native/123/synthetic/N01.report.json'],report)
            for limits in [dict(max_archive_bytes=16*1024**2,max_file_bytes=16*1024**2),dict(max_archive_bytes=32*1024**2,max_file_bytes=32*1024**2)]:
                changed=dict(index,**limits);(stage/'index.json').write_text(json.dumps(changed),encoding='utf-8')
                (stage/'verified.json').write_text(json.dumps(dict(proof,index_sha256=sha256(stage/'index.json'))),encoding='utf-8')
                with self.assertRaises(ValueError):reader.read_packet('sample',1,stage=True)
        (stage/'index.json').write_text(json.dumps(index,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        (stage/'verified.json').write_text(json.dumps(proof,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        self.assertEqual(sha256(stage/'index.json'),proof['index_sha256'])
        immutable_json(stage/'complete-readback.json',dict(index_sha256=proof['index_sha256'],members_compared_byte_exact=2,archive_sha256=sha256(archive)))
        # Exercise actual native checked move/removal on Windows; other hosts
        # still verify real >16MiB archive/member bytes and both refusal bounds.
        if os.name=='nt':
            scripts=workspace/'scripts/acceptance';scripts.mkdir(parents=True)
            for name in ['next20_remove_native.ps1','next20_promote_native.ps1']:shutil.copyfile(ROOT/'scripts/acceptance'/name,scripts/name)
            async def run(script,label,expected,staged=False):
                return await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',scripts/script,'-Project','sample','-Generation','1',*(['-Staged'] if staged else [])],
                    'core',label,cwd=workspace,env=owned_environment(),timeout=30,expected=expected,campaign=NextCampaign(outer))
            asyncio.run(run('next20_promote_native.ps1','native-stage-promotion-refuses-unremoved-inputs',1))
            (source/'N01.report.json').write_bytes(b'changed')
            asyncio.run(run('next20_remove_native.ps1','native-stage-removal-refuses-changed-input',1,True));self.assertTrue(source.exists())
            (source/'N01.report.json').write_bytes(report)
            asyncio.run(run('next20_remove_native.ps1','native-stage-removal-exact-owned-inputs',0,True));self.assertFalse(source.exists())
            asyncio.run(run('next20_promote_native.ps1','native-stage-promotion-after-complete-removal',0))
            final=root/'sample/retained-native-v1';self.assertFalse(stage.exists());self.assertTrue((final/'promoted.json').is_file())
            with patch.object(reader,'RAW',root):self.assertEqual(reader.read_packet('sample',1)[1]['native/123/synthetic/large.whl'],large)
        # This is deterministic synthetic unit-test scratch, not application
        # evidence. Retain its hashes/outcome and remove only these exact large
        # bytes after every real readback/refusal/move assertion has passed.
        selected_archive=(root/'sample/retained-native-v1/packets.tar.gz') if os.name=='nt' else archive
        candidates=[(source/'large.whl',hashlib.sha256(large).hexdigest()),(selected_archive,index['archive_sha256'])]
        removed=[]
        for path,digest in candidates:
            if not path.exists():continue
            path.resolve(strict=True).relative_to(outer.resolve(strict=True))
            self.assertFalse(path.is_symlink());self.assertEqual(sha256(path),digest)
            size=path.stat().st_size;path.unlink();removed.append(dict(path=path.relative_to(outer).as_posix(),bytes=size,sha256=digest))
        immutable_json(outer/'synthetic-payload-cleanup.json',dict(schema_version=1,deterministic_seed=1,synthetic_payload_bytes=len(large),
            synthetic_payload_sha256=hashlib.sha256(large).hexdigest(),all_readback_and_refusal_assertions_passed=True,removed=removed,
            scope='Synthetic unit-test scratch only; no application evidence, packet or target input removed. Exact seed/size/source define reproducible test data.'))
