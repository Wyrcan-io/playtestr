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

    def test_candidate_series_selects_separate_exact_archive_and_rejects_tampering(self):
        import next20_candidate as candidate
        from unittest.mock import patch
        output=self.root/'candidate-native-exit-v1/windows';output.mkdir(parents=True)
        binary=output/'playtestr.exe';binary.write_bytes(b'synthetic candidate bytes')
        digest=sha256(binary);archive_digest='a'*64
        freeze=self.root/'replacement-candidate-freeze-native-exit-v1.json'
        immutable_json(freeze,dict(cells=[dict(host='windows',binary_sha256=digest,archive_sha256=archive_digest)]))
        immutable_json(output/'installed.json',dict(binary_sha256=digest,archive_sha256=archive_digest))
        with patch.object(candidate,'DOC',self.root),patch.object(candidate,'RAW',self.root):
            self.assertEqual(candidate.executable('native-exit-v1','windows'),binary)
            self.assertFalse((self.root/'candidate').exists())
            binary.write_bytes(b'changed synthetic candidate')
            with self.assertRaisesRegex(ValueError,'frozen archive'):candidate.executable('native-exit-v1','windows')
            with self.assertRaisesRegex(ValueError,'undeclared'):candidate.contract('invented','windows')

    def test_invalid_spec_cleanup_classification_refuses_any_launch_or_cleanup_state(self):
        import copy
        from next20_target_cleanup import invalid_spec_before_launch
        row=dict(status='failed',duration_ms=0,viewport=dict(width=0,height=0),target=dict(exited=False),
            failure=dict(category='invalid_spec',message='test specification is invalid'),
            cleanup=dict(attempted=False,graceful=False,forced=False,confirmed_exited=False),evidence={})
        self.assertTrue(invalid_spec_before_launch(dict(results=[row]),row))
        for key,value in [('invocation_id','observed'),('workspace',dict(prepared=True)),
            ('evidence',dict(screen='observed')),('steps',[dict(status='passed')]),
            ('cleanup',dict(attempted=True,graceful=False,forced=False,confirmed_exited=False)),
            ('target',dict(exited=True)),('duration_ms',1)]:
            changed=copy.deepcopy(row);changed[key]=value
            self.assertFalse(invalid_spec_before_launch(dict(results=[changed]),changed),key)

    def test_replacement_source_campaign_records_supported_phase_without_changing_argv(self):
        from next20_replacement_candidate import SourceCampaign
        source=self.root/'source-input.go';source.write_bytes(b'package synthetic\n')
        campaign=SourceCampaign([source],raw=self.root)
        self.assertEqual(campaign.phase,'development')
        result=asyncio.run(execute([sys.executable,'-B','-c','import sys; print(len(sys.argv))'],
            'core','source-binding-command-control',cwd=ROOT,env=owned_environment(),
            timeout=10,campaign=campaign))
        self.assertEqual(result['output'].strip(),'1')
        identified=json.loads((self.root/'events'/(result['id']+'-identified.json')).read_text())
        manifest=json.loads((self.root/identified['identity']['manifest']).read_text())
        self.assertEqual(manifest['files'][source.relative_to(ROOT).as_posix()],sha256(source))
        # This valid non-file operand exceeded NAME_MAX on native Linux before
        # the source adapter stopped probing Go -run regexps as filenames.
        long_regexp='^Test('+('SourceBindingAlternative|'*20)+'Final)$'
        reference=campaign.identity('core',[sys.executable,'-run',long_regexp])
        rebound=json.loads((self.root/reference['manifest']).read_text())
        self.assertEqual(rebound['files'][source.relative_to(ROOT).as_posix()],sha256(source))

    def test_native_runtime_requires_matching_build_and_rejects_changed_binary(self):
        target=self.root/'active/native-control';binary=target/'bin/target.exe'
        binary.parent.mkdir(parents=True);binary.write_bytes(b'compiled native control bytes')
        digest=sha256(binary)
        immutable_json(target/'runtime.json',dict(kind='native',native=str(binary),native_sha256=digest))
        with self.assertRaises(FileNotFoundError):self.campaign.identity('native-control',[binary])
        build=target/'build.json'
        immutable_json(build,dict(runtime_kind='native',binary_sha256=digest,binary_relative_path='bin/target.exe'))
        self.campaign.identity('native-control',[binary])
        binary.write_bytes(b'changed native control bytes')
        with self.assertRaisesRegex(ValueError,'executable changed'):
            self.campaign.identity('native-control',[binary])
        # A matching runtime hash still cannot hide a different compiled build.
        runtime=json.loads((target/'runtime.json').read_text());runtime['native_sha256']=sha256(binary)
        (target/'runtime.json').write_text(json.dumps(runtime))
        with self.assertRaisesRegex(ValueError,'matching build provenance'):
            self.campaign.identity('native-control',[binary])

    def test_short_compiler_cache_preserves_bytes_and_refuses_changed_copy(self):
        from unittest.mock import patch
        import next20_rust_fetch as rust
        target=self.root/'active/cargo-generate'
        source=target/'cargo-home/registry/src/registry/control-1.0/build.rs'
        archive=target/'cargo-home/registry/cache/registry/control-1.0.crate'
        source.parent.mkdir(parents=True);archive.parent.mkdir(parents=True)
        source.write_bytes(b'fn main() {}\n');archive.write_bytes(b'synthetic archive identity control')
        catalog=dict(files={source.relative_to(target).as_posix():sha256(source)})
        immutable_json(target/'dependency-source-catalog.json',catalog)
        dependencies=dict(files={archive.relative_to(target).as_posix():dict(sha256=sha256(archive))})
        with patch.object(rust,'RAW',self.root):
            copied=rust.materialize_short_cache(target,dependencies,catalog)
            actual=copied/'registry/src/registry/control-1.0/build.rs'
            self.assertEqual(actual.read_bytes(),source.read_bytes())
            self.assertEqual(rust.materialize_short_cache(target,dependencies,catalog),copied)
            actual.write_bytes(b'changed source after review')
            with self.assertRaisesRegex(ValueError,'short cache changed'):
                rust.materialize_short_cache(target,dependencies,catalog)
            self.assertEqual(actual.read_bytes(),b'changed source after review')

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

    def test_local_xz_packet_preserves_exact_records_and_refuses_corruption(self):
        from unittest.mock import patch
        import next20_yo_local_packet as packet
        raw=self.root/'raw';project=raw/'yo';project.mkdir(parents=True)
        report=project/'first-ordinary-report.json';report.write_bytes(b'{"synthetic_retention_control":true}\n')
        payload=project/'notes.txt';payload.write_bytes('synthetic café 雪\n'.encode())
        canonical=project/'retained-source/npm-cache/payload';canonical.parent.mkdir(parents=True)
        canonical.write_bytes(b'untouched synthetic canonical source')
        expected={p.relative_to(raw).as_posix():p.read_bytes() for p in [report,payload]}
        with patch.object(packet,'RAW',raw):
            packet.load_packet.cache_clear();packet.compact()
            index,files=packet.verified_packet()
            self.assertEqual(files,expected);self.assertFalse(report.exists());self.assertTrue(canonical.exists())
            self.assertEqual(packet.read_bytes(report),expected[report.relative_to(raw).as_posix()])
            with self.assertRaisesRegex(ValueError,'Unsafe'):packet.safe_path('yo/../outside.txt')
            archive=packet.packet_root()/'packets.tar.xz';data=bytearray(archive.read_bytes());data[-8]^=1;archive.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'index/archive changed'):packet.verified_packet()
            packet.load_packet.cache_clear()

    def test_native_packet_encodings_preserve_aliases_and_reject_bad_hashes(self):
        import hashlib
        import io
        import tarfile
        from next20_packet_archive import archive_path,verify,tar_mode
        root=self.root/'packet-encoding-control';root.mkdir(parents=True)
        data=b'\x00synthetic exact\r\nbytes\xff'
        files={'native/123/first.bin':dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()),
               'native/123/alias.bin':dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),member='native/123/first.bin')}
        for encoding in ['tar.gz','tar.xz']:
            index=dict(compression=encoding);archive=archive_path(root,index)
            with tarfile.open(archive,'w:'+('gz' if encoding=='tar.gz' else 'xz')) as bundle:
                member=tarfile.TarInfo('native/123/first.bin');member.size=len(data);bundle.addfile(member,io.BytesIO(data))
            verify(archive,files)
            with tarfile.open(archive,tar_mode(index)) as bundle:self.assertEqual(bundle.extractfile('native/123/first.bin').read(),data)
            changed={n:dict(row,sha256='0'*64) for n,row in files.items()}
            with self.assertRaises(ValueError):verify(archive,changed)
        with self.assertRaisesRegex(ValueError,'compression'):archive_path(root,dict(compression='tar.zip'))

    def test_carried_cell_requires_exact_original_run_source_and_declaration(self):
        import copy
        from next20_verify_jrnl import cell_declaration
        package=self.root/'cell-declaration-control';package.mkdir(parents=True)
        path=package/'final-series-declaration-v2.json';immutable_json(path,dict(revision=2,hosts=['linux','windows']))
        current=dict(revision=3,accepted_prior_cells=dict(linux=dict(run='123',source_revision='a'*40,
            declaration_file=path.name,declaration_sha256=sha256(path))))
        selected,selected_path=cell_declaration(package,current,'123','linux','a'*40)
        self.assertEqual(selected['revision'],2);self.assertEqual(selected_path,path)
        self.assertEqual(cell_declaration(package,current,'456','windows','b'*40)[0],current)
        for field,value in [('run','999'),('source_revision','b'*40),('declaration_sha256','0'*64),('declaration_file','../outside.json')]:
            altered=copy.deepcopy(current);altered['accepted_prior_cells']['linux'][field]=value
            with self.assertRaises(ValueError):cell_declaration(package,altered,'123','linux','a'*40)

    def test_registry_source_root_cannot_resolve_outside_owned_campaign(self):
        from unittest.mock import patch
        import next20_yo_registry_reference as registry
        raw=self.root/'owned-campaign';raw.mkdir(parents=True)
        outside=self.root/'outside-cache';outside.mkdir();payload=outside/'untouched';payload.write_bytes(b'owned sibling control\n')
        with patch.object(registry,'RAW',raw):
            with self.assertRaises(ValueError):registry.cache_inventory(outside)
        self.assertEqual(payload.read_bytes(),b'owned sibling control\n')

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
            max_files=60000,max_bytes=2*1024**3,owner_sha256=sha256(marker),owned_links={},
            files={marker.name:dict(bytes=marker.stat().st_size,sha256=sha256(marker))}))
        immutable_json(retained/'prepared.json',dict(cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json')))
        async def run(expected,extra,label):
            return await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',script,
                '-Project','yo',*extra],'core',label,cwd=ROOT,env=owned_environment(),timeout=90,
                expected=expected,campaign=self.campaign)
        refused=asyncio.run(run(1,[],'native-large-cleanup-default-bound-refusal'))
        self.assertIn('bound differs from prepared inventory',refused['output']);self.assertTrue(target.exists())
        refused_bytes=asyncio.run(run(1,['-MaxFiles','60000'],'native-large-cleanup-default-byte-bound-refusal'))
        self.assertIn('byte bound differs from prepared inventory',refused_bytes['output']);self.assertTrue(target.exists())
        asyncio.run(run(0,['-MaxFiles','60000','-MaxBytes','2147483648'],'native-large-cleanup-explicit-bound'))
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

    def test_admission_counter_refuses_mixed_and_unidentified_candidates(self):
        from next20_update_ledger import require_counter_candidate
        old=dict(candidate='v0.4.0-rc.5',ordinary=480)
        current=dict(candidate='v0.4.0-rc.6',ordinary=480)
        require_counter_candidate([old],'v0.4.0-rc.5')
        for admissions in [[old,current],[old],[dict(ordinary=480)]]:
            with self.assertRaisesRegex(ValueError,'mixed candidate admission credits'):
                require_counter_candidate(admissions,'v0.4.0-rc.6')


if __name__=='__main__':unittest.main()
