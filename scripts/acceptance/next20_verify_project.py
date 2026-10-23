"""Audit a declared Python project's complete actual retained native cell."""
import argparse
import uuid

from next20_check import RAW
from next20_verify_jrnl import build_model, validate
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project',choices=['jrnl','commitizen-python','cz-cli'])
    parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'],required=True)
    parser.add_argument('--generation',type=int,required=True)
    args=parser.parse_args()
    retained=RAW/args.project/('retained-native-v'+str(args.generation))
    model,index=build_model(retained,args.run,args.host,args.project)
    counts=validate(model)
    destination=RAW/args.project/'audits'/uuid.uuid4().hex
    destination.mkdir(parents=True)
    immutable_json(destination/'actual-model.json',model)
    immutable_json(destination/'verified.json',dict(schema_version=1,project=args.project,
        run=args.run,host=args.host,actual_model_sha256=sha256(destination/'actual-model.json'),
        archive_sha256=index['archive_sha256'],index_sha256=sha256(retained/'index.json'),
        **counts,overall_project_admissions=0))
    print('Independently audited complete actual cell:',args.project,args.host,counts)


if __name__=='__main__':main()
