"""Reexecute inherited public control definitions in the new evidence namespace."""
import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW, ROOT, NextCampaign, owned_environment
from readiness_archive_controls import cases, definition_sha256, wait_child_gone
from readiness_evidence import immutable_json, sha256


class ArchiveControlCampaign(NextCampaign):
    def identity(self,project,argv):
        reference=super().identity(project,argv)
        if Path(str(argv[0])).name.lower() not in {'go','go.exe'}:return reference
        compiler=Path(str(argv[0])).resolve(strict=True)
        value=json.loads((self.raw/reference['manifest']).read_text())
        value.setdefault('runtime_executables',{})['go']=sha256(compiler)
        value['read_only_compiler_path']=str(compiler)
        value['files']['cmd/fixture/main.go']=sha256(ROOT/'cmd/fixture/main.go')
        path=self.raw/'identities'/(uuid.uuid4().hex+'-compiler.json')
        immutable_json(path,value)
        return dict(manifest=path.relative_to(self.raw).as_posix(),sha256=sha256(path))


async def main():
    inherited=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    declaration=json.loads((inherited/'archive-control-declaration.json').read_text())
    freeze=json.loads((inherited/'migration-candidate-freeze.json').read_text())
    host={'Linux':'linux','Darwin':'darwin','Windows':'windows'}[platform.system()]
    cell=next(c for c in freeze['cells'] if c['host']==host)
    binary=RAW/'candidate'/host/('playtestr.exe' if os.name=='nt' else 'playtestr')
    installed=json.loads((binary.parent/'installed.json').read_text())
    if sha256(binary)!=cell['binary_sha256'] or installed['archive_sha256']!=cell['archive_sha256']:
        raise ValueError('Exact frozen archive installation missing')
    if [(c['id'],definition_sha256(c)) for c in cases()]!=[(c['id'],c['definition_sha256']) for c in declaration['cases']]:
        raise ValueError('Inherited public control definitions changed')
    if hashlib.sha256((ROOT/'cmd/fixture/main.go').read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=declaration['fixture_source_lf_sha256']:
        raise ValueError('Reviewed synthetic target source changed')
    root=RAW/'product-controls'/uuid.uuid4().hex;root.mkdir(parents=True)
    suffix='.exe' if os.name=='nt' else '';fixture=root/'bin'/('fixture'+suffix);fixture.parent.mkdir()
    compiler=shutil.which('go')
    if compiler is None:raise ValueError('Installed read-only Go prerequisite missing')
    # Windows PATH discovery preserves an uppercase .EXE spelling. The inherited
    # prelaunch source selector recognizes the canonical Go executable basename.
    # Resolve the same file with that spelling; do not alter historical defaults.
    if os.name=='nt':compiler=str(Path(compiler).with_name('go.exe'))
    env=owned_environment();env['GOTOOLCHAIN']='local';campaign=ArchiveControlCampaign(phase='final-archive')
    async def run(argv,label,expected=0,input=None,timeout=30):
        return await execute(argv,'core',label,cwd=ROOT,env=env,timeout=timeout,expected=expected,input=input,campaign=campaign)
    built=await run([compiler,'build','-buildvcs=false','-o',fixture,'./cmd/fixture'],'archive-controls-fixture-build',timeout=180)
    build=dict(fixture_relative_path=fixture.relative_to(ROOT).as_posix(),fixture_sha256=sha256(fixture),
        fixture_source_sha256=sha256(ROOT/'cmd/fixture/main.go'),compiler_sha256=sha256(compiler),
        go_mod_sha256=sha256(ROOT/'go.mod'),go_sum_sha256=sha256(ROOT/'go.sum'),
        build_attempt=built['id'],runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'])
    immutable_json(root/'build.json',build)
    immutable_json(root/'intent.json',dict(declaration_sha256=sha256(inherited/'archive-control-declaration.json'),
        definition_source_sha256=sha256(ROOT/'scripts/acceptance/readiness_archive_controls.py'),
        build_sha256=sha256(root/'build.json'),planned_cases=[c['id'] for c in cases()]+declaration['recorder_controls'],
        host=host,scope='Fresh exact-archive public reexecutions; zero new whole-control or application credit.'))
    rows=[]
    for case in cases():
        folder=root/case['id'];folder.mkdir();seed=folder/'fixture';seed.mkdir()
        for name,data in case['files'].items():
            path=seed/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        for name in case['dirs']:(seed/name).mkdir(parents=True,exist_ok=True)
        steps=([dict(expect='Press Enter to save the synthetic file'),dict(key='Enter'),dict(expect='Saved successfully'),dict(exit=0)]
            if case['mode']=='saved-state' else [dict(text='x'),dict(key='Enter'),dict(expect='input received'),dict(exit=0)])
        value=dict(version=3,name='Next twenty archive control '+case['id'],command=[str(fixture),case['mode']],
            workspace=dict(fixture='fixture',cwd='.',home='temporary',temp='temporary'),
            inherit_env=['SYSTEMROOT','WINDIR','PATH','SystemDrive'] if os.name=='nt' else [],
            width=100,height=28,timeout_ms=5000,run_timeout_ms=15000,max_output_bytes=2000000,
            steps=steps+[dict(state=s) for s in case['states']])
        value.update(copy.deepcopy(case['changes']));spec=folder/'spec.json';immutable_json(spec,value)
        report=folder/'report.json';expected=int(case['category'] is not None)
        attempt=await run([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (folder/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'archive-control-'+case['id'],expected)
        result=json.loads(report.read_text(encoding='utf-8'));row=result['results'][0]
        if result['runner_version']!=freeze['version'] or row['status']!=('failed' if expected else 'passed'):
            raise ValueError('Wrong exact archive control outcome')
        if expected and row['failure']['category']!=case['category']:raise ValueError('Wrong control diagnosis: '+case['id'])
        if case['category']=='invalid_spec':
            if row.get('invocation_id') or row.get('workspace') or row['cleanup']['attempted']:raise ValueError('Invalid spec launched')
        else:
            if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('Unconfirmed control cleanup')
            if not expected and (len(row['steps'])!=len(value['steps']) or any(s['status']!='passed' for s in row['steps'])):
                raise ValueError('Missing positive control steps')
            for step in row['steps']:
                if 'state' in step and (step['state']['invocation_id']!=row['invocation_id'] or step['state']['workspace_id']!=row['workspace']['id']):
                    raise ValueError('Cross-execution control state')
        independent=None
        if case['id']=='descendant-timeout-cleanup':
            matches=re.findall(r'started child ([0-9]+)',(ROOT/row['evidence']['screen_path']).read_text(encoding='utf-8-sig'))
            if len(matches)!=1:raise ValueError('Missing independently observed owned PID')
            independent=await wait_child_gone(int(matches[0]))
        rows.append(dict(case=case['id'],attempt=attempt['id'],report_sha256=sha256(report),spec_sha256=sha256(spec),
            category=case['category'],independent_child_termination=independent))
    for label,mode,controls in [('recorder-rejected-capture','saved-state',
        '/expect Press Enter to save the synthetic file\n/key Enter\n/expect Saved successfully\n/exit 0\n/file never-written\n/review\n/replay\n/save\n'),
        ('recorder-input-only','hang','/text "x"\n/review\n/replay\n/save\n')]:
        folder=root/label;folder.mkdir();(folder/'fixture').mkdir();spec=folder/'recorded.json'
        attempt=await run([binary,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home',
            '--temporary-temp','--timeout-ms','1000','--run-timeout-ms','5000','--',fixture,mode],
            'archive-control-'+label,1,controls)
        anchor='unresolved control failures' if label=='recorder-rejected-capture' else 'completion'
        if spec.exists() or anchor not in attempt['output']:raise ValueError('Recorder exported a false green or omitted diagnosis')
        rows.append(dict(case=label,attempt=attempt['id'],export_absent=True))
    immutable_json(root/'results.json',dict(controls=rows,observed=len(rows),runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256']))
    if os.name=='nt':
        await run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
            ROOT/'scripts/acceptance/next20_remove_control_fixture.ps1','-ControlId',root.name],
            'archive-controls-fixture-checked-removal',timeout=90)
    else:
        if fixture.is_symlink() or sha256(fixture)!=build['fixture_sha256']:raise ValueError('Fixture changed before removal')
        fixture.unlink();fixture.parent.rmdir()
    immutable_json(root/'removed.json',dict(fixture_binary_removed=not fixture.exists(),fixture_sha256=build['fixture_sha256'],all_public_target_workspaces_checked=True))
    print('Verified 35 fresh exact-archive public control reexecutions on',host,'; zero new breadth/whole-control credit.')


if __name__=='__main__':asyncio.run(main())
