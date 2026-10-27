"""Freeze the useful reviewed jrnl development contracts before held-out faults."""
import json
import argparse

from next20_check import DOC,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def main(project='jrnl',exposure=None):
    package=DOC/project;declaration=json.loads((package/'scenarios.json').read_text())
    summaries=[]
    for path in (RAW/project/'development').glob('*/summary.json'):
        value=json.loads(path.read_text())
        if value['passed']==20 and value['failed']==0 and value['declaration_sha256']==sha256(package/'scenarios.json'):
            summaries.append(path)
    if len(summaries)!=1:raise ValueError('need one current complete positive development series')
    inputs={};directories=[]
    for case in declaration['cases']:
        spec=package/case['spec']
        if sha256(spec)!=case['spec_sha256']:raise ValueError('selected contract changed')
        inputs[spec.relative_to(package).as_posix()]=sha256(spec)
        fixture=package/case['initial_fixture']
        for path in [fixture,*sorted(fixture.rglob('*'))]:
            if path.is_dir():directories.append(path.relative_to(package).as_posix())
            elif path.is_file():inputs[path.relative_to(package).as_posix()]=sha256(path)
        for step in json.loads(spec.read_text())['steps']:
            if 'snapshot' in step:
                path=package/'snapshots'/step['snapshot'];inputs[path.relative_to(package).as_posix()]=sha256(path)
    immutable_json(package/'development-test-freeze.json',dict(schema_version=1,status='frozen-before-fault-selection',
        scenarios_sha256=sha256(package/'scenarios.json'),inputs=inputs,directories=sorted(set(directories)),
        positive_development_summary=summaries[0].relative_to(ROOT).as_posix(),positive_summary_sha256=sha256(summaries[0]),
        ordinary_development_cases=20,final_ordinary_credit=0,
        exposure=exposure or 'Normal target source/docs and three earlier failed oracle/message assumptions plus the retained upstream reorder limitation are already known. No source mutation has yet been applied.'))
    print('Froze twenty current reviewed contracts and',len(inputs),'exact files before source-fault selection.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--project',default='jrnl');parser.add_argument('--exposure')
    args=parser.parse_args()
    if '/' in args.project or '\\' in args.project or not (DOC/args.project/'source-provenance.json').is_file():raise ValueError('undeclared project')
    main(args.project,args.exposure)
