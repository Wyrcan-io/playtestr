"""Reapply original native migration audits to the exact final private archives."""
import argparse
import importlib

from readiness_evidence import RAW, ROOT, immutable_json
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['cookiecutter','copier','lf','superfile','helix','glow'],required=True)
    parser.add_argument('--host',choices=['linux','macos','windows'],required=True);parser.add_argument('--run',required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid native final migration run')
    hosts=['linux','macos'] if args.project in {'superfile','glow'} else ['linux','windows']
    require(args.host in hosts,'undeclared original native host')
    parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2
        and all(j['status']=='completed' and j['conclusion']=='success' for j in metadata['jobs']),'incomplete native final migration jobs')
    suffix={'linux':'Linux','windows':'Windows','macos':'macOS'}[args.host]
    base=parent/('old-'+args.project+'-'+suffix)
    module=importlib.import_module('readiness_old_'+args.project+'_verify')
    receipt=module.audit(base,args.host,args.run,series='migration-v2')
    receipt['scope']+=' Fresh exact rc.5 archive requalification; prior rc.4 migration evidence retained separately.'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration'/args.project
    immutable_json(docs/('final-verified-'+args.host+'.json'),receipt)
    print('Independently verified original migration against final archive:',args.project,args.host)


if __name__=='__main__':main()
