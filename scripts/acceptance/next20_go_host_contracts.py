"""Bind frozen native-capture contracts to actual owned executable basenames."""
import argparse
import copy
import json
import os
from pathlib import Path
import platform
import shutil

from next20_check import DOC,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe Go host profile')
    canonical=DOC/project;target=RAW/'active'/project;destination=RAW/project/'host-contracts';freeze=json.loads((canonical/'development-test-freeze.json').read_text());declaration=json.loads((canonical/'scenarios.json').read_text());runtime=json.loads((target/'runtime.json').read_text());build=json.loads((target/'build.json').read_text())
    host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    for name,digest in freeze['inputs'].items():
        if sha256(canonical/name)!=digest:raise ValueError('canonical Go contract/input changed')
    capture=Path(runtime['native']);app=Path(runtime['target'])
    for name,digest in build['compiled_files'].items():
        if sha256(capture.parent/name)!=digest:raise ValueError('actual Go executable differs')
    destination.mkdir(parents=True,exist_ok=False)
    for name in freeze['inputs']:
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(canonical/name,path)
    for name in freeze['directories']:(destination/name).mkdir(parents=True,exist_ok=True)
    cases=[]
    for case in declaration['cases']:
        value=json.loads((canonical/case['spec']).read_text());argv=value['command']
        if argv.count('--app')!=1 or argv[argv.index('--app')+1] not in {project,project+'.exe'}:raise ValueError('unreviewed native-capture argv route')
        argv[0]=os.path.relpath(capture,destination).replace('\\','/');argv[argv.index('--app')+1]=app.name
        path=destination/case['spec'];path.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        cases.append(dict(case,canonical_sha256=case['spec_sha256'],spec_sha256=sha256(path)))
    immutable_json(destination/'scenarios.json',dict(declaration,cases=cases,host=host,canonical_declaration_sha256=sha256(canonical/'scenarios.json'),development_freeze_sha256=sha256(canonical/'development-test-freeze.json')))
    host_freeze=dict(freeze,canonical_freeze_sha256=sha256(canonical/'development-test-freeze.json'),inputs={name:sha256(destination/name) for name in freeze['inputs']},host=host,
        scope='Only command executable path and declared --app sibling basename rebound. All input,exit,screen,saved-output,deadline and fixture expectations byte-preserved; selected stdout is LF on both hosts.')
    immutable_json(destination/'development-test-freeze.json',host_freeze)
    immutable_json(target/'launch-runtime-catalog.json',dict(schema_version=1,runtime_root=capture.parent.relative_to(ROOT).as_posix(),files=build['compiled_files'],executable=capture.relative_to(ROOT).as_posix()))
    print('Materialized exact frozen Go capture contracts:',host,'20cases;',len(freeze['inputs']),'inputs; executable route only, no oracle changes.')


if __name__=='__main__':main()
