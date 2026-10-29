import hashlib
import io
import json
import tarfile
import unittest
from unittest.mock import patch
import uuid

import next20_local_records as packets
import next20_target_cleanup as cleanup
from next20_check import RAW
from readiness_evidence import immutable_json, sha256


class ClosedReportTests(unittest.TestCase):
    def test_cleanup_reads_exact_retained_report_and_refuses_duplicate_or_unconfirmed_retention(self):
        root=RAW/'control-tests'/('closed-reports-'+uuid.uuid4().hex);project=root/'sample';packet=project/'retained-failed-final-v1';packet.mkdir(parents=True)
        name='sample/final/failure.report.json';raw=b'{"runner_version":"synthetic","results":[]}\n'
        archive=packet/'packets.tar.xz'
        with tarfile.open(archive,'w:xz') as stream:
            member=tarfile.TarInfo(name);member.size=len(raw);stream.addfile(member,io.BytesIO(raw))
        immutable_json(packet/'index.json',dict(project='sample',compression='tar.xz',archive_sha256=sha256(archive),
            files={name:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())}))
        proof=dict(all_expanded_removed=True,index_sha256=sha256(packet/'index.json'),archive_sha256=sha256(archive))
        removed=packet/'expanded-removed.json';immutable_json(removed,proof)
        with patch.object(packets,'RAW',root),patch.object(cleanup,'RAW',root):
            actual=list(cleanup.cleanup_reports(project,['retained-failed-final-v1']))
            self.assertEqual(actual,[(root/name,json.loads(raw),hashlib.sha256(raw).hexdigest())])
            path=root/name;path.parent.mkdir();path.write_bytes(raw)
            with self.assertRaises(ValueError):list(cleanup.cleanup_reports(project,['retained-failed-final-v1']))
            path.unlink();proof['all_expanded_removed']=False;removed.write_text(json.dumps(proof),encoding='utf-8')
            with self.assertRaises(ValueError):list(cleanup.cleanup_reports(project,['retained-failed-final-v1']))
            with self.assertRaises(ValueError):list(cleanup.cleanup_reports(project,['../escape']))
