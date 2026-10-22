"""Exercise public controls through exact private archives, never runner rebuilds."""
import asyncio
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


def file_state(path,data):return dict(path=path,kind='file',bytes_base64=base64.b64encode(data).decode())


def definition_sha256(case):
    value={**case,'files':{n:base64.b64encode(b).decode() for n,b in case['files'].items()}}
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()


def cases():
    rows=[]
    def add(name,states=(),files=None,dirs=(),category=None,mode='input',**changes):
        rows.append(dict(id=name,states=list(states),files=files or {},dirs=list(dirs),category=category,mode=mode,changes=changes))
    def state(kind,path,**extra):return dict(kind=kind,path=path,**extra)
    add('dynamic-binary-unicode',[file_state('result.bin','reviewed\r\n\x00caf\u00e9\n'.encode())],mode='saved-state')
    add('dynamic-wrong-bytes',[file_state('result.bin',b'wrong')],mode='saved-state',category='state_assertion_failure')
    add('absence',[state('absent','missing.bin')])
    add('absence-existing',[state('absent','present.bin')],files={'present.bin':b'x'},category='state_assertion_failure')
    add('directory',[state('directory','folder')],dirs=['folder'])
    add('directory-wrong-type',[state('directory','folder')],files={'folder':b'x'},category='state_assertion_failure')
    add('empty-directory',[state('empty_directory','folder')],dirs=['folder'])
    add('nonempty-directory',[state('empty_directory','folder')],files={'folder/x':b'x'},category='state_assertion_failure')
    add('exact-entries',[state('entries','folder',entries=['a','b'])],files={'folder/a':b'a','folder/b':b'b'})
    add('extra-entry',[state('entries','folder',entries=['a'])],files={'folder/a':b'a','folder/b':b'b'},category='state_assertion_failure')
    add('missing-entry',[state('entries','folder',entries=['a','b'])],files={'folder/a':b'a'},category='state_assertion_failure')
    add('empty-file',[file_state('empty.bin',b'')],files={'empty.bin':b''})
    add('file-64k',[file_state('full.bin',b'A'*65536)],files={'full.bin':b'A'*65536})
    add('observed-file-over-limit',[file_state('full.bin',b'')],files={'full.bin':b'A'*65537},category='state_assertion_failure')
    values={str(i)+'.bin':bytes([65+i])*65536 for i in range(8)}
    add('aggregate-512k',[file_state(n,b) for n,b in values.items()],files=values)
    over={**values,'8.bin':b'I'*65536}
    add('expected-aggregate-over-limit',[file_state(n,b) for n,b in over.items()],files=over,category='invalid_spec')
    entries={f'folder/f{i:03}':b'' for i in range(256)}
    add('entries-256',[state('entries','folder',entries=[f'f{i:03}' for i in range(256)])],files=entries)
    add('observed-entries-over-limit',[state('entries','folder',entries=[f'f{i:03}' for i in range(256)])],files={**entries,'folder/extra':b''},category='state_assertion_failure')
    add('expected-entries-over-limit',[state('entries','folder',entries=[f'f{i:03}' for i in range(257)])],category='invalid_spec')
    add('traversal-refused',[file_state('../outside.bin',b'x')],category='invalid_spec')
    add('expected-file-over-limit',[file_state('full.bin',b'A'*65537)],category='invalid_spec')
    add('total-1000-steps',[file_state('one.bin',b'x') for _ in range(996)],files={'one.bin':b'x'})
    add('total-1001-steps',[file_state('one.bin',b'x') for _ in range(997)],files={'one.bin':b'x'},category='invalid_spec')
    add('unsupported-format',category='invalid_spec',version=999)
    add('old-format-state',[file_state('one.bin',b'x')],category='invalid_spec',version=2)
    add('output-flood',mode='flood',category='output_limit',max_output_bytes=4096,
        steps=[dict(expect='never a completion')])
    add('assertion-timeout',mode='hang',category='assertion_timeout',timeout_ms=1000,run_timeout_ms=5000,
        steps=[dict(expect='fixture ready; waiting forever'),dict(expect='never a completion')])
    add('whole-run-timeout',mode='hang',category='run_timeout',timeout_ms=5000,run_timeout_ms=1000,
        steps=[dict(expect='fixture ready; waiting forever'),dict(expect='never a completion')])
    add('descendant-timeout-cleanup',mode='child',category='assertion_timeout',timeout_ms=1000,run_timeout_ms=5000,
        steps=[dict(expect='started child'),dict(expect='never a completion')])
    add('unexpected-exit',mode='unknown-control-mode',category='unexpected_exit',steps=[dict(exit=0)])
    add('expected-nonzero-exit',mode='unknown-control-mode',steps=[dict(exit=2)])
    add('rendered-alternate-unicode',mode='screen',steps=[dict(expect='alternate screen'),dict(text='x'),
        dict(expect='compat complete'),dict(expect='compat main: caf\u00e9 \u03bb'),dict(exit=0)])
    add('controlled-resize',mode='resize',steps=[dict(expect='resize ready'),dict(resize=dict(width=80,height=20)),
        dict(text='x'),dict(expect='resized 80x20'),dict(exit=0)])
    return rows


async def wait_child_gone(pid):
    deadline=time.monotonic()+5
    while True:
        if os.name=='nt':
            import ctypes
            api=ctypes.WinDLL('kernel32',use_last_error=True)
            api.OpenProcess.restype=ctypes.c_void_p
            api.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
            api.CloseHandle.argtypes=[ctypes.c_void_p]
            handle=api.OpenProcess(0x100000|0x1000,False,pid)
            if not handle:
                if ctypes.get_last_error()==87:return 'native PID absent'
                raise RuntimeError('cannot independently inspect owned child termination')
            try:
                if api.WaitForSingleObject(handle,0)==0:return 'native process handle signaled'
            finally:api.CloseHandle(handle)
        else:
            try:os.kill(pid,0)
            except ProcessLookupError:return 'native PID absent'
        if time.monotonic()>=deadline:raise RuntimeError('owned fixture descendant remains after runner cleanup')
        await asyncio.sleep(.05)


async def main():
    binary,candidate,cell=runner('migration-v2');declaration=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/archive-control-declaration.json')
    # Normalize checkout line endings only for source-code comparison. Every
    # actual native source file and all test data retain their exact byte hashes.
    if declaration['fixture_source_lf_sha256']!=hashlib.sha256((ROOT/'cmd/fixture/main.go').read_bytes().replace(b'\r\n',b'\n')).hexdigest():raise RuntimeError('declared synthetic fixture source changed')
    if [(c['id'],definition_sha256(c)) for c in cases()]!=[(c['id'],c['definition_sha256']) for c in declaration['cases']]:raise RuntimeError('declared public control definitions changed')
    root=RAW/'product-controls'/uuid.uuid4().hex;root.mkdir(parents=True)
    suffix='.exe' if os.name=='nt' else '';fixture=root/'bin'/('fixture'+suffix);fixture.parent.mkdir()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GOTOOLCHAIN='local')
    for key,name in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),('LOCALAPPDATA','home/localappdata'),
        ('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('GOTMPDIR','tmp'),('GOCACHE','go-cache'),('GOPATH','gopath'),('GOMODCACHE','gopath/pkg/mod')]:
        path=RAW/name;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
    cache=root/'shell-cache';cache.mkdir();env['PSModuleAnalysisCachePath']=str(cache/'ModuleAnalysisCache')
    sdk=RAW/'toolchain/go/bin'/('go'+suffix)
    built=await execute([sdk,'build','-buildvcs=false','-o',fixture,'./cmd/fixture'],'core','archive-controls-fixture-build',env=env,timeout=180,campaign=Campaign(phase='final-archive'))
    build=dict(fixture_relative_path=fixture.relative_to(ROOT).as_posix(),fixture_sha256=sha256(fixture),
        fixture_source_sha256=sha256(ROOT/'cmd/fixture/main.go'),go_mod_sha256=sha256(ROOT/'go.mod'),go_sum_sha256=sha256(ROOT/'go.sum'),
        compiler_sha256=sha256(sdk),build_attempt=built['id'],runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'])
    immutable_json(root/'build.json',build)
    immutable_json(root/'intent.json',dict(declaration_sha256=sha256(ROOT/'docs/validation/runner-readiness-ten-project-pass/archive-control-declaration.json'),
        build_sha256=sha256(root/'build.json'),planned_cases=[r['id'] for r in cases()]+['recorder-rejected-capture','recorder-input-only'],
        scope='Exact archived runner; separately built synthetic target fixture. These are public control reexecutions, not new unique controls, project faults or final scenario repetitions.'))
    results=[]
    for case in cases():
        folder=root/case['id'];folder.mkdir();seed=folder/'fixture';seed.mkdir()
        for name,data in case['files'].items():
            path=seed/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        for name in case['dirs']:(seed/name).mkdir(parents=True,exist_ok=True)
        steps=([dict(expect='Press Enter to save the synthetic file'),dict(key='Enter'),dict(expect='Saved successfully'),dict(exit=0)]
            if case['mode']=='saved-state' else [dict(text='x'),dict(key='Enter'),dict(expect='input received'),dict(exit=0)])
        value=dict(version=3,name='Final archive control '+case['id'],command=[str(fixture),case['mode']],
            workspace=dict(fixture='fixture',cwd='.',home='temporary',temp='temporary'),
            inherit_env=['SYSTEMROOT','WINDIR','PATH','SystemDrive'] if os.name=='nt' else [],
            width=100,height=28,timeout_ms=5000,run_timeout_ms=15000,max_output_bytes=2000000,
            steps=steps+[dict(state=s) for s in case['states']])
        value.update(copy.deepcopy(case['changes']));spec=folder/'spec.json';immutable_json(spec,value)
        report=folder/'report.json';expected=int(case['category'] is not None)
        attempt=await execute([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(folder/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],
            'core','archive-control-'+case['id'],env=env,timeout=30,expected=expected,campaign=Campaign(phase='final-archive'))
        result=load(report);row=result['results'][0]
        if result['runner_version']!=candidate['version'] or row['status']!=('failed' if expected else 'passed'):raise RuntimeError('wrong archive control outcome')
        if expected and row['failure']['category']!=case['category']:raise RuntimeError('wrong archive control diagnosis: '+case['id'])
        if case['category']=='invalid_spec':
            if row.get('invocation_id') or row.get('workspace') or row['cleanup']['attempted']:raise RuntimeError('invalid contract launched a target')
        else:
            if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise RuntimeError('public control target/workspace cleanup unconfirmed')
            if not expected and (len(row['steps'])!=len(value['steps']) or any(s['status']!='passed' for s in row['steps'])):raise RuntimeError('missing positive archive control evidence')
            for step in row['steps']:
                if 'state' in step and (step['state']['invocation_id']!=row['invocation_id'] or step['state']['workspace_id']!=row['workspace']['id']):raise RuntimeError('cross-execution archive state')
        independent=None
        if case['id']=='descendant-timeout-cleanup':
            screen=ROOT/row['evidence']['screen_path'];matches=re.findall(r'started child ([0-9]+)',screen.read_text(encoding='utf-8-sig'))
            if len(matches)!=1:raise RuntimeError('missing actual owned descendant PID')
            independent=await wait_child_gone(int(matches[0]))
        results.append(dict(case=case['id'],attempt=attempt['id'],report_sha256=sha256(report),spec_sha256=sha256(spec),
            category=case['category'],independent_child_termination=independent))
        print('Public exact-archive control:',case['id'],'verified',flush=True)
    for label,mode,controls in [('recorder-rejected-capture','saved-state',
        '/expect Press Enter to save the synthetic file\n/key Enter\n/expect Saved successfully\n/exit 0\n/file never-written\n/review\n/replay\n/save\n'),
        ('recorder-input-only','hang','/text "x"\n/review\n/replay\n/save\n')]:
        folder=root/label;folder.mkdir();(folder/'fixture').mkdir();spec=folder/'recorded.json'
        attempt=await execute([binary,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
            '--timeout-ms','1000','--run-timeout-ms','5000','--',fixture,mode],
            'core','archive-control-'+label,env=env,input=controls,expected=1,timeout=30,campaign=Campaign(phase='final-archive'))
        if spec.exists():raise RuntimeError('recorder exported a false green')
        if label=='recorder-rejected-capture' and 'unresolved control failures' not in attempt['output']:raise RuntimeError('missing actual rejected-capture diagnosis')
        if label=='recorder-input-only' and 'completion' not in attempt['output']:raise RuntimeError('missing actual input-only diagnosis')
        results.append(dict(case=label,attempt=attempt['id'],export_absent=True))
    immutable_json(root/'results.json',dict(controls=results,observed=len(results),runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256']))
    if os.name=='nt':
        cleanup=await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/acceptance/readiness_remove_control_fixture.ps1',
            '-ControlId',root.name],'core','archive-controls-fixture-checked-removal',env=env,timeout=60,campaign=Campaign(phase='final-archive'))
    else:
        if fixture.is_symlink() or sha256(fixture)!=build['fixture_sha256']:raise RuntimeError('fixture changed before removal')
        fixture.unlink();fixture.parent.rmdir();cleanup=None
    immutable_json(root/'removed.json',dict(fixture_binary_removed=not fixture.exists(),fixture_sha256=build['fixture_sha256'],
        native_removal_attempt=cleanup['id'] if cleanup else None,all_public_target_workspaces_checked=True))
    print('Verified public archive controls:',len(results),'; no new project/unique-control credit.')


if __name__=='__main__':asyncio.run(main())
