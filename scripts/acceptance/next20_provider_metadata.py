"""Retain bounded actual GitHub Actions run/job metadata without shell redirects."""
import argparse
import json
import subprocess

from next20_check import RAW
from readiness_evidence import immutable_json


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
    if not args.run.isascii() or not args.run.isdecimal():raise ValueError('unsafe provider run')
    result=subprocess.run(['gh','run','view',args.run,'--repo','Wyrcan-io/playtestr','--json',
        'databaseId,headSha,headBranch,event,status,conclusion,jobs,url,workflowName,createdAt,updatedAt'],
        capture_output=True,timeout=60,check=True)
    if len(result.stdout)>4*1024**2 or len(result.stderr)>65536:raise ValueError('provider metadata bound')
    metadata=json.loads(result.stdout)
    if str(metadata['databaseId'])!=args.run or metadata['headBranch']!='work/p0-p2-implementation':raise ValueError('provider run ownership mismatch')
    destination=RAW/'native'/args.run/'run-metadata.json'
    immutable_json(destination,metadata)
    print('Retained actual provider metadata:',args.run,metadata['status'],metadata['conclusion'])


if __name__=='__main__':main()
