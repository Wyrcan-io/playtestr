"""Materialize original native contracts plus public saved-state checkpoints."""
import argparse
import json
import shutil

from adversarial_journey import host_case_name
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_migration_prepare import migrate,relative


def bounded_files(root):
    files=[];total=0
    for path in root.rglob('*'):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise RuntimeError('linked original fixture')
        if path.is_file():
            total+=path.stat().st_size;files.append(path)
            if total>64*1024**2 or len(files)>4096:raise RuntimeError('old migration package bound')
    return files


def materialize(project,host,output):
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    inventory=load(docs/'old-migration-inventory.json')
    candidates=[p for p in inventory['projects'] if p['project']==project]
    if len(candidates)!=1 or host not in candidates[0]['previously_qualified_hosts']:
        raise RuntimeError('undeclared original project/host')
    original=ROOT/'docs/validation/ten-new-project-adversarial-pass'/project
    config=load(original/'scenarios.json')
    if sha256(original/'scenarios.json')!=candidates[0]['original_scenarios_sha256']:raise RuntimeError('original scenarios changed')
    output.resolve().relative_to(RAW.resolve());output.mkdir(parents=True,exist_ok=False)
    system={'linux':'Linux','macos':'Darwin','windows':'Windows'}[host]
    copied={};rows=[]
    for case in config['cases']:
        if case.get('qualified_hosts') and host not in case['qualified_hosts']:continue
        native=host_case_name(case,config,system)
        source=original/(native+'.json');old=load(source);contract=migrate(old,case)
        name=case['name']+'.json';relative(name)
        fixture=relative(old['workspace']['fixture'])
        if fixture not in copied:
            fixture_source=original/fixture
            if project=='broot' and fixture=='fixtures-large' and not fixture_source.exists():
                from adversarial_broot_cases import large_files,prepare_large_fixture
                if large_files()!=case['expected_files']:raise RuntimeError('original generated fixture differs from original scenario')
                prepare_large_fixture(output)
                fixture_source=output/fixture
            else:
                fixture_source.resolve(strict=True).relative_to(original.resolve())
                bounded_files(fixture_source)
                shutil.copytree(fixture_source,output/fixture)
            files=bounded_files(fixture_source)
            copied[fixture]={str(p.relative_to(fixture_source).as_posix()):sha256(p) for p in files}
        for step in old['steps']:
            if 'snapshot' not in step:continue
            baseline=relative(step['snapshot']);selected=original/'snapshots'/baseline
            selected.resolve(strict=True).relative_to((original/'snapshots').resolve())
            if selected.is_symlink() or selected.stat().st_size>4*1024**2:raise RuntimeError('original snapshot bound/type')
            destination=output/'snapshots'/baseline;destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.exists():
                if sha256(destination)!=sha256(selected):raise RuntimeError('conflicting original native snapshot')
            else:shutil.copyfile(selected,destination)
        destination=output/name
        destination.write_text(json.dumps(contract,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
        if contract['steps'][:len(old['steps'])]!=old['steps']:raise RuntimeError('original public prefix changed')
        rows.append(dict(case=case['name'],original_native_spec=source.relative_to(ROOT).as_posix(),
            original_native_spec_sha256=sha256(source),contract_sha256=sha256(destination),
            original_prefix_steps=len(old['steps']),appended_state_steps=len(contract['steps'])-len(old['steps'])))
    directory_plan=original/'fixture-directories.json'
    if directory_plan.exists():
        for name in load(directory_plan):
            relative(name)
            if not any(name==f or name.startswith(f+'/') for f in copied):continue
            (output/name).mkdir(parents=True,exist_ok=True)
    files=bounded_files(output)
    receipt=dict(project=project,host=host,repository=candidates[0]['repository'],pin=candidates[0]['pin'],cases=rows,
        original_scenarios_sha256=sha256(original/'scenarios.json'),host_selector_sha256=sha256(ROOT/'scripts/acceptance/adversarial_journey.py'),
        copied_fixtures=copied,all_package_inputs={p.relative_to(output).as_posix():sha256(p) for p in files},
        execution_credit=0,status='Materialized unchanged original native prefixes plus public same-execution saved-state assertions; target execution still required.')
    return receipt


def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--project');group.add_argument('--all',action='store_true')
    parser.add_argument('--host',choices=['linux','macos','windows']);args=parser.parse_args()
    if bool(args.project)!=bool(args.host):parser.error('a selected project needs its declared host; --all selects original hosts')
    inventory=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration-inventory.json')
    selected=([(args.project,args.host)] if args.project else
        [(p['project'],h) for p in inventory['projects'] for h in p['previously_qualified_hosts']])
    profiles=[]
    for project,host in selected:
        destination=RAW/'old-migration'/project/host/'contracts'
        receipt_path=destination.parent/'materialized.json'
        if receipt_path.exists():
            receipt=load(receipt_path)
            if receipt['project']!=project or receipt['host']!=host or receipt['execution_credit']!=0:
                raise RuntimeError('existing prepared profile identity differs')
            actual={p.relative_to(destination).as_posix():sha256(p) for p in bounded_files(destination)}
            if actual!=receipt['all_package_inputs']:raise RuntimeError('existing prepared native payload changed')
        else:
            receipt=materialize(project,host,destination)
            immutable_json(receipt_path,receipt)
        profiles.append(dict(project=project,host=host,cases=len(receipt['cases']),receipt_sha256=sha256(receipt_path),
            package_bytes=sum(p.stat().st_size for p in bounded_files(destination))))
        print('Materialized',len(receipt['cases']),'original native',project,host,'contracts; no execution credit.',flush=True)
    if args.all:
        immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration-native-preparation.json',
            dict(profiles=profiles,prepared_native_profiles=len(profiles),
                prepared_native_contracts=sum(p['cases'] for p in profiles),source_reacquired=False,
                migrated_projects=0,old_native_executions=0,status='Prepared exact original native prefixes, baselines and fixtures with appended public saved-state assertions. Actual target execution remains required.'))


if __name__=='__main__':main()
