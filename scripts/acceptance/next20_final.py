"""Execute one declared shared Python final-series batch without retries."""
import argparse
import asyncio
import re
from next20_jrnl_final import main as run_batch


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--batch',type=int,required=True);args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project):raise ValueError('unsafe final project slug')
    asyncio.run(run_batch(args.project,args.batch))


if __name__=='__main__':main()
