"""Acquire a checksum-verified SDK under one reviewed original target root."""
import argparse

import readiness_bootstrap_go as bootstrap
from readiness_evidence import RAW, ROOT
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['lf'],required=True);args=parser.parse_args()
    target=RAW/'active'/('old-'+args.project)
    owner=load(target/'task-owned.json')
    review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration'/args.project/'source-review.json')
    if owner['workspace']!=str(ROOT) or owner['pin']!=review['pin'] or owner['project']!=review['repository']:
        raise RuntimeError('unowned original Go target')
    bootstrap.RAW=target;bootstrap.VERSION='go1.27.0';bootstrap.main()


if __name__=='__main__':main()
