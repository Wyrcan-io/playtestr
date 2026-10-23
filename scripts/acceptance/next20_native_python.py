"""Explicit selected-project adapter over reviewed native Python preparation."""
import argparse
import asyncio
import re
from next20_jrnl_native_prepare import main as prepare


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project):raise ValueError('unsafe native project slug')
    asyncio.run(prepare(args.project))


if __name__=='__main__':main()
