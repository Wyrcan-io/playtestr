import copy
import hashlib
import io
import json
import tarfile
import unittest
from unittest.mock import patch
import uuid

import next20_native_packet_reader as reader
from next20_check import RAW
from readiness_evidence import immutable_json, sha256


class ExactNativeReferenceTests(unittest.TestCase):
    def test_exact_references_restore_and_refuse_missing_changed_unsafe_or_chained_inputs(self):
        root=RAW/'control-tests'/('exact-native-'+uuid.uuid4().hex);project='synthetic';base=root/project/'retained-native-v1';base.mkdir(parents=True)
        shared=b'exact reviewed bytes\r\n';current=b'new actual report\n'
        def write(generation,files,external=None,required=None):
            path=root/project/('retained-native-v'+str(generation));path.mkdir(exist_ok=True)
            archive=path/'packets.tar.gz';rows={}
            with tarfile.open(archive,'w:gz') as stream:
                for name,data in files.items():
                    member=tarfile.TarInfo(name);member.size=len(data);stream.addfile(member,io.BytesIO(data))
                    rows[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            index=dict(schema_version=3 if external else 2,project=project,generation=generation,files=rows,archive_sha256=sha256(archive))
            if external:index.update(external_exact_payloads=external,required_canonical_packet=required)
            immutable_json(path/'index.json',index)
            immutable_json(path/'verified.json',dict(index_sha256=sha256(path/'index.json'),archive_sha256=sha256(archive)))
            return path
        write(1,{'native/1/base/common.bin':shared})
        reference=dict(generation=1,index_sha256=sha256(base/'index.json'),archive_sha256=sha256(base/'packets.tar.gz'))
        external={'native/2/current/common.bin':dict(bytes=len(shared),sha256=hashlib.sha256(shared).hexdigest(),canonical_logical_path='native/1/base/common.bin')}
        write(2,{'native/2/current/report.json':current},external,reference)
        with patch.object(reader,'RAW',root):
            _,actual=reader.read_packet(project,2)
            self.assertEqual(actual,{'native/2/current/report.json':current,'native/2/current/common.bin':shared})
            for generation,change in enumerate(['payload','missing','escape','overlap','canonical','forward'],3):
                altered=copy.deepcopy(external);required=dict(reference)
                if change=='payload':next(iter(altered.values()))['sha256']='0'*64
                elif change=='missing':next(iter(altered.values()))['canonical_logical_path']='native/1/base/missing'
                elif change=='escape':altered={'../escape':next(iter(altered.values()))}
                elif change=='overlap':altered={'native/2/current/report.json':next(iter(altered.values()))}
                elif change=='canonical':required['index_sha256']='0'*64
                elif change=='forward':required['generation']=generation
                write(generation,{'native/2/current/report.json':current},altered,required)
                with self.assertRaises(ValueError):reader.read_packet(project,generation)
            write(9,{'native/9/report.json':current},{'native/9/common.bin':dict(bytes=len(shared),sha256=hashlib.sha256(shared).hexdigest(),canonical_logical_path='native/2/current/common.bin')},
                dict(generation=2,index_sha256=sha256(root/project/'retained-native-v2/index.json'),archive_sha256=sha256(root/project/'retained-native-v2/packets.tar.gz')))
            with self.assertRaises(ValueError):reader.read_packet(project,9)
            (base/'packets.tar.gz').write_bytes(b'changed canonical archive')
            with self.assertRaises(ValueError):reader.read_packet(project,2)
