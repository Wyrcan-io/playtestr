"""Prepare public v3 saved-state conversions without running old applications."""
import base64
import copy
import hashlib
import json
from pathlib import PurePosixPath

from readiness_evidence import ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def relative(value, root=False):
    if root and value=='.':return value
    if (not isinstance(value,str) or not value or len(value)>4096 or '\\' in value or ':' in value
            or '\x00' in value or any(p in {'','.','..'} for p in value.split('/'))):
        raise ValueError('saved outcome needs a confined portable relative path')
    return value


def saved_states(case):
    files=case.get('expected_files',{})
    directories=set(case.get('expected_directories',[]))
    empty=set(case.get('empty_directories',[]))
    if not isinstance(files,dict) or not empty<=directories:
        raise ValueError('invalid original saved-state declarations')
    if set(files)&directories:raise ValueError('contradictory original file/directory types')
    states=[]
    for name,value in sorted(files.items()):
        relative(name)
        if not isinstance(value,str):raise ValueError('original file expectation is not exact text bytes')
        data=value.encode('utf-8')
        if len(data)>4*1024**2:raise ValueError('prepared exact file byte bound')
        states.append(dict(state=dict(kind='file',path=name,bytes_base64=base64.b64encode(data).decode())))
    for name in sorted(set(case.get('absent_paths',[]))):
        states.append(dict(state=dict(kind='absent',path=relative(name))))
    for name in sorted(directories):
        states.append(dict(state=dict(kind='empty_directory' if name in empty else 'directory',path=relative(name,True))))
    exact=case.get('exact_tree',False)
    if not isinstance(exact,bool):raise ValueError('invalid original exact-tree declaration')
    if exact:
        nodes=set(files)|directories
        for name in list(nodes):
            relative(name)
            nodes.update(p.as_posix() for p in PurePosixPath(name).parents if p!=PurePosixPath('.'))
        if len(nodes)>4096:raise ValueError('original exact-tree entry bound')
        parents={'.'}|{n for n in nodes if n not in files}
        for directory in sorted(parents):
            entries=sorted(PurePosixPath(n).name for n in nodes if PurePosixPath(n).parent.as_posix()==directory)
            states.append(dict(state=dict(kind='entries',path=directory,entries=entries)))
    if not states:raise ValueError('no representable saved outcome declared')
    return states


def migrate(original, case):
    if original.get('version')!=2 or not isinstance(original.get('steps'),list):
        raise ValueError('expected original public v2 contract')
    if original.get('workspace',{}).get('cwd','.')!='.':
        raise ValueError('non-root original state checkpoint needs case-specific review')
    steps=original['steps']
    exits=[i for i,s in enumerate(steps) if 'exit' in s]
    if not exits or any(set(s)-{'snapshot','expect','expect_not','timeout_ms'} for s in steps[exits[-1]+1:]):
        raise ValueError('saved state needs an exact completion checkpoint after the final input')
    if 'expected_exit' in case and steps[exits[-1]]['exit']!=case['expected_exit']:
        raise ValueError('original exact exit disagrees with saved-outcome declaration')
    if any('state' in s for s in steps):raise ValueError('original v2 already contains a state step')
    result=copy.deepcopy(original)
    result['version']=3
    result['steps'].extend(saved_states(case))
    return result


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass'
    inventory=load(docs/'old-migration-inventory.json')
    projects=[];converted=0;unsupported=[]
    for project in inventory['projects']:
        name=project['project']
        scenarios=old/name/'scenarios.json'
        if sha256(scenarios)!=project['original_scenarios_sha256']:
            raise RuntimeError('original scenario source changed')
        cases=[]
        for case in load(scenarios)['cases']:
            original_path=old/name/(case['name']+'.json')
            original=load(original_path)
            try:
                contract=migrate(original,case)
            except ValueError as error:
                unsupported.append(dict(project=name,case=case['name'],reason=str(error)))
                continue
            payload=json.dumps(contract,sort_keys=True,ensure_ascii=True).encode()
            cases.append(dict(case=case['name'],original_spec_sha256=sha256(original_path),
                prepared_contract_sha256=hashlib.sha256(payload).hexdigest(),
                appended_state_steps=len(contract['steps'])-len(original['steps']),contract=contract))
            converted+=1
        projects.append(dict(project=name,repository=project['repository'],pin=project['pin'],
            original_scenarios_sha256=sha256(scenarios),previously_qualified_hosts=project['previously_qualified_hosts'],cases=cases))
    record=dict(schema_version=1,projects=projects,prepared_canonical_contracts=converted,unsupported=unsupported,
        original_inventory_sha256=sha256(docs/'old-migration-inventory.json'),
        status='Prepared canonical conversion plan only, not a materialized or executed migration package.',
        preservation='Original commands, input/screen/exit steps, fixture references and snapshots remain exact; only version changes and public saved-state steps append after completion.',
        pending='Reacquire one old application at a time after Rclone, materialize original fixtures/baselines, apply previously qualified native action/snapshot variants, execute all representable cases and real corruption/recovery controls.',
        source_reacquired=False,migrated_projects=0,old_native_executions=0,new_project_credit=0)
    if len(json.dumps(record).encode())>8*1024**2:raise RuntimeError('prepared migration plan byte bound')
    immutable_json(docs/'old-migration-conversion-plan.json',record)
    print('Prepared',converted,'canonical v3 conversions;',len(unsupported),'explicit unsupported cases; no migration execution credit.')


if __name__=='__main__':main()
