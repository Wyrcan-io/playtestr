"""Re-audit admitted packets without duplicating their large actual models."""
import argparse
import json
import uuid

from next20_check import RAW, DOC
from next20_verify_jrnl import build_model, validate
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project',choices=['jrnl','commitizen-python','cz-cli','yo'])
    parser.add_argument('--host',choices=['linux','windows']);parser.add_argument('--run');args=parser.parse_args()
    declaration=json.loads((DOC/args.project/'final-series-declaration.json').read_text())
    admission=json.loads((DOC/args.project/'admission.json').read_text()) if not args.run else None
    generations=declaration.get('retained_generations',dict(linux=1,windows=2));results=[]
    for host,generation in generations.items():
        if args.host and host!=args.host:continue
        retained=RAW/args.project/('retained-native-v'+str(generation))
        index=json.loads((retained/'index.json').read_text())
        run=str(index['runs'][0]) if 'runs' in index else str(admission['native_run'])
        if args.run and run!=args.run:raise ValueError('Explicit native readback run differs')
        model,_=build_model(retained,run,host,args.project);counts=validate(model)
        matches=[p for p in (RAW/args.project/'audits').glob('*/actual-model.json') if json.loads(p.read_text())==model]
        if len(matches)!=1:raise ValueError('Readback differs from original independently audited model')
        results.append(dict(host=host,run=run,original_model=matches[0].relative_to(RAW).as_posix(),
            original_model_sha256=sha256(matches[0]),counts=counts))
    root=RAW/'harness/audit-regressions'/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'verified.json',dict(schema_version=1,project=args.project,results=results,
        new_scenario_credit=0,new_project_admissions=0,scope='Fresh exact packet readback using current auditor; original model reused without duplicate large payloads.'))
    print('Current auditor reconstructed',len(results),'actual cells; exact original models unchanged.')


if __name__=='__main__':main()
