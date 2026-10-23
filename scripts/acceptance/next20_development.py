"""Run the common twenty-case development protocol for a declared active project."""
import argparse
import asyncio

from next20_check import RAW, DOC
from next20_jrnl_development import main as run_cases


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    if not (RAW/'active'/args.project/'task-owned.json').is_file() or not (DOC/args.project/'scenarios.json').is_file():
        raise ValueError('declared active project/scenarios required')
    asyncio.run(run_cases(args.project))


if __name__=='__main__':main()
