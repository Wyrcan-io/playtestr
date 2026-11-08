"""Twelve declared fresh native repetitions using exact archive bytes."""
import argparse
import asyncio
import copy
import json
import os
import platform
import re
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256
from next20_candidate import contract,executable,SERIES
from next20_python_runtime import python_runtime_root
from next20_startup_profile import startup_deadline, tight_startup
from next20_batch_snapshots import apply as batch_snapshots


def segmented_steps(original, readiness=False):
    """Retain three-codepoint writes, optionally checking declared input consumption."""
    steps=[]
    for number,step in enumerate(original):
        if set(step)=={'text'} and len(step['text'])>1 and all(ord(c)>=32 and ord(c)!=127 for c in step['text']):
            value=step['text'];following=original[number+1] if number+1<len(original) else {}
            expected=following.get('expect') if set(following)=={'expect'} else None
            prefix=expected[:-len(value)] if readiness and isinstance(expected,str) and expected.endswith(value) else None
            for index in range(0,len(value),3):
                steps.append({'text':value[index:index+3]})
                if prefix is not None and index+3<len(value):steps.append({'expect':prefix+value[:index+3]})
        else:steps.append(copy.deepcopy(step))
    return steps


def widen_viewport(spec, width_delta=10, height_delta=2):
    """Resize a valid public spec, honoring its documented default dimensions."""
    width = spec.get('width', 80)
    height = spec.get('height', 24)
    if (type(width) is not int or type(height) is not int or width < 1 or height < 1):
        raise ValueError('viewport dimensions must be positive integers')
    spec['width'] = width + width_delta
    spec['height'] = height + height_delta
    return spec


def expected_scenario_hash(declaration):
    """Resolve the scenario digest without conflating a separate freeze receipt."""
    return declaration.get('canonical_scenario_sha256',
                           declaration.get('canonical_test_freeze_sha256'))


def runtime_lock_path(package, candidate_series):
    """Use a series-specific runtime lock or the package's canonical lock."""
    specific=package/('native-runtime-lock-'+candidate_series+'.json')
    canonical=package/'native-runtime-lock.json'
    return specific if specific.is_file() or not canonical.is_file() else canonical


async def main(project='jrnl',batch=None,candidate_series='rc5',chunk_readiness=False,window=None,
               startup_timeout_ms_by_host=None,declaration_path_override=None):
    if batch is None:
        parser=argparse.ArgumentParser();parser.add_argument('--batch',type=int,required=True)
        parser.add_argument('--project',default=project);parser.add_argument('--candidate-series',choices=SERIES,default=candidate_series)
        parser.add_argument('--window',default=window)
        args=parser.parse_args();project=args.project;candidate_series=args.candidate_series;window=args.window
    else:args=argparse.Namespace(batch=batch)
    if not (DOC/project/'source-provenance.json').is_file() or '/' in project or '\\' in project:raise ValueError('undeclared project')
    if not 0<=args.batch<12:raise ValueError('undeclared final batch')
    if window is not None and (not re.fullmatch(r'v[1-9][0-9]{0,2}',window) or int(window[1:])<2):raise ValueError('invalid explicit replacement window')
    host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    suffix='' if candidate_series=='rc5' else '-'+candidate_series
    if window:suffix+='-'+window
    declaration_path=(Path(declaration_path_override) if declaration_path_override else
        DOC/project/('final-series-declaration'+suffix+'.json'))
    declaration=json.loads(declaration_path.read_text())
    if host not in declaration['hosts']:raise ValueError('undeclared host')
    freeze,_,_=contract(candidate_series,host)
    if declaration.get('candidate_freeze_sha256') and sha256(
        ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json'
        if candidate_series=='rc5' else DOC/'replacement-candidate-freeze-native-exit-v1.json')!=declaration['candidate_freeze_sha256']:
        raise ValueError('Candidate freeze differs from final-series declaration')
    # Native campaigns may materialize their immutable host contracts under
    # RAW after checkout. Validate the declaration against the same canonical
    # package that the batch copies below, falling back to the committed
    # package for campaigns that retain it in docs.
    raw_contracts=RAW/project/'host-contracts'
    doc_contracts=DOC/project/'host-contracts'
    canonical=raw_contracts if raw_contracts.is_dir() else doc_contracts
    scenarios_path=canonical/'scenarios.json'
    expected_scenarios=expected_scenario_hash(declaration)
    if expected_scenarios and sha256(scenarios_path)!=expected_scenarios:
        raise ValueError('Canonical scenario freeze differs from final-series declaration')
    runtime_lock=runtime_lock_path(DOC/project,candidate_series)
    if declaration.get('native_runtime_lock_sha256') and (
        not runtime_lock.is_file() or sha256(runtime_lock)!=declaration['native_runtime_lock_sha256']):
        raise ValueError('Native runtime lock differs from final-series declaration')
    root=RAW/project/('final-series'+suffix)/str(args.batch)
    root.mkdir(parents=True,exist_ok=False)
    if canonical.is_symlink() or getattr(canonical,'is_junction',lambda:False)():raise ValueError('Linked canonical native contract root')
    canonical.resolve(strict=True).relative_to((DOC if canonical.is_relative_to(DOC) else RAW).resolve(strict=True))
    package=root/('relocated café 雪' if args.batch==5 else 'contracts')
    shutil.copytree(canonical,package)
    snapshot_changes=batch_snapshots(package,DOC/project,declaration.get('batch_snapshot_profiles',{}),args.batch)
    source=RAW/'active'/project;runtime=json.loads((source/'runtime.json').read_text());kind=runtime.get('kind','python')
    if kind not in {'python','node','native'}:raise ValueError('Undeclared final runtime kind')
    python=Path(runtime[kind]);executable_sha256=runtime[kind+'_sha256']
    installed=json.loads((source/'installed-inventory.json').read_text());inventory=installed['files']
    original_runtime=ROOT/installed['runtime_root'] if kind!='python' else python_runtime_root(source,runtime)
    original_runtime.resolve(strict=True).relative_to(source.resolve(strict=True))
    if kind!='python':inventory={**inventory,**json.loads((source/'build.json').read_text())['compiled_files']}
    def dependencies():
        for name,digest in inventory.items():
            if sha256(original_runtime/name)!=digest:raise ValueError('native installed/compiled dependency changed: '+name)
    dependencies()
    clone_prefix=('venv-pair-' if kind=='python' else 'app-pair-')
    if suffix:clone_prefix+=candidate_series+'-'
    if window:clone_prefix+=window+'-'
    # Cold means a newly materialized, hash-verified runtime copy, followed by
    # reuse in its paired warm batch. It does not claim a flushed OS file cache.
    if args.batch in {0,2}:
        clone=source/(clone_prefix+str(args.batch//2))
        shutil.copytree(original_runtime,clone,symlinks=kind=='python')
        for name,digest in inventory.items():
            if sha256(clone/name)!=digest:raise ValueError('fresh runtime copy mismatch')
        immutable_json(clone/'copy-identity.json',dict(source_inventory_sha256=sha256(source/'installed-inventory.json'),
            source_relative_path=original_runtime.relative_to(source).as_posix(),cold_scope='First use of a newly materialized verified runtime, not OS-cache eviction'))
    if args.batch<4:
        clone=source/(clone_prefix+str(args.batch//2))
        if not clone.exists():raise ValueError('warm repetition missing preceding cold runtime preparation')
        if kind=='python':python=clone/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        elif kind=='native':python=clone/python.name
        if sha256(python)!=executable_sha256:raise ValueError('actual executed interpreter differs')
        for name,digest in inventory.items():
            if sha256(clone/name)!=digest:raise ValueError('actual copied dependency changed: '+name)
    actual_runtime=clone if args.batch<4 else original_runtime
    actual_runtime_files={name:sha256(actual_runtime/name) for name in inventory}
    if actual_runtime_files!=inventory:raise ValueError('actual selected runtime does not match installed dependency bytes')
    runtime_catalog=dict(schema_version=1,runtime_root=actual_runtime.relative_to(ROOT).as_posix(),
        files=actual_runtime_files,executable=python.relative_to(ROOT).as_posix(),executable_sha256=sha256(python),
        source_inventory_sha256=sha256(source/'installed-inventory.json'))
    immutable_json(root/'runtime-catalog.json',runtime_catalog)
    shutil.copyfile(root/'runtime-catalog.json',source/'launch-runtime-catalog.json')
    scenario_catalog=json.loads((canonical/'scenarios.json').read_text())
    cases=scenario_catalog['cases'];changes=[]
    if scenario_catalog.get('fixture_manifest'):
        fixture_manifest=canonical/scenario_catalog['fixture_manifest']
        if sha256(fixture_manifest)!=scenario_catalog.get('fixture_manifest_sha256'):
            raise ValueError('Frozen native fixture manifest changed')
        manifest=json.loads(fixture_manifest.read_text())
        fixture_root=canonical/'fixtures'
        if manifest.get('project')!=project or manifest.get('source_pin')!=json.loads((DOC/project/'source-provenance.json').read_text())['pin']:
            raise ValueError('Frozen native fixture manifest provenance differs')
        fixture_paths=list(fixture_root.rglob('*'))
        if any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in fixture_paths):
            raise ValueError('Frozen native fixture tree contains a linked path')
        actual_files={p.relative_to(fixture_root).as_posix():sha256(p) for p in fixture_paths if p.is_file()}
        if actual_files!=manifest.get('files'):
            raise ValueError('Frozen native fixture bytes or membership changed')
    for case in cases:
        before=package/case['spec'];value=json.loads(before.read_text())
        if sha256(canonical/case['spec'])!=case['spec_sha256']:raise ValueError('native base contract changed')
        if kind=='native':
            command=value.get('command')
            if not isinstance(command,list) or not command or command[0] not in {'taskell','sh'}:
                raise ValueError('Native target launcher is outside the reviewed Taskell command set')
            if command[0]=='sh' and command!=['sh','readonly.sh']:
                raise ValueError('Native Taskell read-only wrapper command changed')
        else:
            value['command'][0]=os.path.relpath(python,package).replace('\\','/')
        if kind=='python' and '--python' in value['command']:
            index=value['command'].index('--python')+1
            if Path(value['command'][index]).resolve()!=Path(runtime['python']).resolve():
                raise ValueError('explicit Python selection differs from declared source runtime')
            value['command'][index]=str(python)
        if kind=='node':
            old='../'+runtime['app_relative_path']+'/'+runtime['entrypoint']
            if value['command'][2].count(old)!=1:raise ValueError('Canonical Node entry routing changed')
            value['command'][2]=value['command'][2].replace(old,'../'+actual_runtime.name+'/'+runtime['entrypoint'])
        if args.batch==4:widen_viewport(value)
        if args.batch==7:
            value['steps']=segmented_steps(value['steps'],readiness=chunk_readiness)
        if args.batch==10 and case['id']=='N01':value['height']=12
        if args.batch==11:
            deadline=startup_deadline(host,declaration,startup_timeout_ms_by_host)
            value=tight_startup(value,case,deadline)
        before.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        changes.append(dict(case=case['id'],spec=case['spec'],canonical_sha256=case['canonical_sha256'],
            native_base_sha256=case['spec_sha256'],executed_spec_sha256=sha256(before)))
    runner=executable(candidate_series,host)
    install=json.loads((runner.parent/'installed.json').read_text())
    if sha256(runner)!=install['binary_sha256']:raise ValueError('wrong final archive binary')
    env=environment(source)
    if kind=='native':
        # Resolve the documented command name from the hash-verified runtime.
        env['PATH']=str(python.parent)+os.pathsep+env.get('PATH','')
    campaign=NextCampaign(phase='final-archive')
    immutable_json(root/'prepared.json',dict(schema_version=2 if kind!='python' else 1,host=host,batch=args.batch,
        declaration_sha256=sha256(declaration_path),changes=changes,
        **(dict(reviewed_snapshot_changes=snapshot_changes) if snapshot_changes else {}),
        **(dict(chunk_readiness=True) if chunk_readiness else {}),
        runner_sha256=sha256(runner),archive_sha256=install['archive_sha256'],
        **(dict(actual_executable=python.relative_to(ROOT).as_posix(),actual_executable_sha256=sha256(python),runtime_kind=kind)
           if kind!='python' else dict(actual_python=python.relative_to(ROOT).as_posix(),actual_python_sha256=sha256(python))),
        actual_runtime_catalog_sha256=sha256(root/'runtime-catalog.json'),
        installed_inventory_sha256=sha256(source/'installed-inventory.json')))
    observations=[];failures=[];not_run=[];unsafe_abort=None
    for case_index,case in enumerate(cases):
        spec=package/case['spec'];report=root/(case['id']+'.report.json')
        planned=dict(schema_version=1,phase='final-archive',host=host,batch=args.batch,case=case['id'],
            spec=spec.relative_to(ROOT).as_posix(),spec_sha256=sha256(spec),runner_sha256=sha256(runner),
            archive_sha256=install['archive_sha256'],target_runtime_sha256=sha256(source/'runtime.json'),
            variation=declaration['batches'][args.batch],expected_runner_exit=0)
        command=[runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)]
        if kind!='python':planned.update(schema_version=2,command=list(map(str,command)),cwd=str(ROOT))
        immutable_json(root/(case['id']+'.planned.json'),planned)
        # No per-case retries: any failure rejects this series, with all existing
        # attempts preserved. Replacement requires an explicit new declaration.
        result=None;row=None;reasons=[]
        try:
            dependencies()
            result=await execute(command,project,'final-batch-'+str(args.batch)+'-'+case['id'],
                cwd=ROOT,env=env,timeout=140,load=args.batch in {8,9},campaign=campaign)
            row=json.loads(report.read_text())['results'][0]
            if row['status']!='passed' or any(s['status']!='passed' for s in row['steps']):reasons.append('nonpositive final step')
            if not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:reasons.append('incomplete target/workspace cleanup')
            if any(s.get('state') and (s['state']['invocation_id']!=row['invocation_id'] or s['state']['workspace_id']!=row['workspace']['id']) for s in row['steps']):
                reasons.append('cross-invocation saved state')
        except Exception as error:
            reasons.append(type(error).__name__+': '+str(error))
            if report.is_file():
                try:row=json.loads(report.read_text())['results'][0]
                except (ValueError,KeyError,IndexError):pass
        record=dict(case=case['id'],attempt=result['id'] if result else None,
            invocation=row.get('invocation_id') if row else None,
            report=report.relative_to(ROOT).as_posix(),report_sha256=sha256(report) if report.is_file() else None,
            spec_sha256=sha256(spec),attempted=bool(result or report.is_file()),passed=not reasons)
        if reasons:
            record['failure_reasons']=reasons;failures.append(record)
            print(host,args.batch,case['id'],'failed','; '.join(reasons),flush=True)
        else:
            observations.append(record);print(host,args.batch,case['id'],'passed',flush=True)
        if (row is not None and (not row.get('workspace',{}).get('cleaned') or
                not row.get('cleanup',{}).get('confirmed_exited'))):
            unsafe_abort='target or workspace cleanup was not confirmed'
        elif row is None and not report.is_file():
            unsafe_abort='runner invocation ended without a report or cleanup evidence'
        if unsafe_abort:
            not_run=[dict(case=pending['id'],status='not_run',reason=unsafe_abort) for pending in cases[case_index+1:]]
            break
    try:dependencies()
    except Exception as error:
        failures.append(dict(case=None,attempt=None,passed=False,failure_reasons=['runtime integrity: '+str(error)]))
    if args.batch<4:
        for name,digest in inventory.items():
            if sha256(clone/name)!=digest:raise ValueError('copied runtime changed during final batch: '+name)
    immutable_json(root/'summary.json',dict(schema_version=2,phase='final-archive',host=host,batch=args.batch,
        observations=observations,failures=failures,not_run=not_run,
        ordinary_attempts=sum(bool(item.get('attempted')) for item in observations+failures),ordinary_passed=len(observations),
        ordinary_not_run=len(not_run),ordinary_required=len(cases),runner_sha256=sha256(runner),archive_sha256=install['archive_sha256'],
        new_project_admissions=0,scope='One declared complete scenario batch; failures are retained and no case is retried.'))
    if failures or not_run:raise ValueError('final batch rejected; all attempted/not-run case outcomes are retained in summary.json')


if __name__=='__main__':asyncio.run(main())
