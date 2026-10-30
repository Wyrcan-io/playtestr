"""Bind frozen native-capture contracts to actual owned executable basenames."""
import argparse
import copy
import json
import os
from pathlib import Path
import platform
import re
import shutil

from next20_check import DOC,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--resume-after');args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe Go host profile')
    canonical=DOC/project;target=RAW/'active'/project;destination=RAW/project/'host-contracts';freeze=json.loads((canonical/'development-test-freeze.json').read_text());declaration=json.loads((canonical/'scenarios.json').read_text());runtime=json.loads((target/'runtime.json').read_text());build=json.loads((target/'build.json').read_text())
    host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    for name,digest in freeze['inputs'].items():
        if sha256(canonical/name)!=digest:raise ValueError('canonical Go contract/input changed')
    capture=Path(runtime['native']);app=Path(runtime['target'])
    for name,digest in build['compiled_files'].items():
        if sha256(capture.parent/name)!=digest:raise ValueError('actual Go executable differs')
    resuming=args.resume_after is not None
    if resuming:
        if not re.fullmatch('[0-9a-f]{32}',args.resume_after):raise ValueError('invalid explicit host-profile failure')
        failed=json.loads((RAW/'events'/(args.resume_after+'-finished.json')).read_text())
        if failed['category']!='exit_mismatch' or failed['exit_code']!=1 or not destination.is_dir():raise ValueError('explicit failed host profile required')
    else:destination.mkdir(parents=True,exist_ok=False)
    for name in freeze['inputs']:
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
        if not resuming:shutil.copyfile(canonical/name,path)
    for name in freeze['directories']:(destination/name).mkdir(parents=True,exist_ok=True)
    cases=[]
    for case in declaration['cases']:
        value=json.loads((canonical/case['spec']).read_text());argv=value['command']
        if argv.count('--app')!=1 or argv[argv.index('--app')+1] not in {project,project+'.exe'}:raise ValueError('unreviewed native-capture argv route')
        argv[0]=os.path.relpath(capture,destination).replace('\\','/');argv[argv.index('--app')+1]=app.name
        path=destination/case['spec']
        if resuming:
            if json.loads(path.read_text())!=value:raise ValueError('existing host contract differs from exact expected profile')
        else:path.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        cases.append(dict(case,canonical_sha256=case['spec_sha256'],spec_sha256=sha256(path)))
    host_declaration=dict(declaration,cases=cases,host=host,canonical_declaration_sha256=sha256(canonical/'scenarios.json'),development_freeze_sha256=sha256(canonical/'development-test-freeze.json'))
    if resuming:
        if json.loads((destination/'scenarios.json').read_text())!=host_declaration:raise ValueError('existing host declaration differs')
    else:immutable_json(destination/'scenarios.json',host_declaration)
    host_freeze=dict(freeze,canonical_freeze_sha256=sha256(canonical/'development-test-freeze.json'),inputs={name:sha256(destination/name) for name in freeze['inputs']},host=host,
        scope='Only command executable path and declared --app sibling basename rebound. All input,exit,screen,saved-output,deadline and fixture expectations byte-preserved; selected stdout is LF on both hosts.')
    if resuming:
        if json.loads((destination/'development-test-freeze.json').read_text())!=host_freeze:raise ValueError('existing host freeze differs')
    else:immutable_json(destination/'development-test-freeze.json',host_freeze)
    for name,hashed in host_freeze['inputs'].items():
        if sha256(destination/name)!=hashed:raise ValueError('host input bytes changed')
        if name.startswith(('fixture/','fixtures/','snapshots/')) and sha256(destination/name)!=freeze['inputs'][name]:raise ValueError('host input/oracle changed')
    pointer=target/'launch-runtime-catalog.json'
    if pointer.exists():
        history=RAW/project/'host-profile-history';history.mkdir(exist_ok=True)
        previous=history/(sha256(pointer)+'.json')
        if previous.exists():
            if previous.read_bytes()!=pointer.read_bytes():raise ValueError('runtime pointer history collision')
        else:previous.write_bytes(pointer.read_bytes())
    value=dict(schema_version=1,runtime_root=capture.parent.relative_to(ROOT).as_posix(),files=build['compiled_files'],executable=capture.relative_to(ROOT).as_posix())
    pointer.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    if resuming:immutable_json(destination/'resume-complete.json',dict(schema_version=1,failed_attempt=args.resume_after,host_freeze_sha256=sha256(destination/'development-test-freeze.json'),runtime_catalog_sha256=sha256(pointer),scope='Existing complete contracts verified without rewriting; prior mutable runtime pointer retained separately. No target execution/credit.'))
    print('Materialized exact frozen Go capture contracts:',host,'20cases;',len(freeze['inputs']),'inputs; executable route only, no oracle changes.')


if __name__=='__main__':main()
