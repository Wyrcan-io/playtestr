"""Explicit new-campaign adapter over the existing verified packet compactor."""
import argparse

from next20_check import RAW
from readiness_compact_native import compact


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True)
    parser.add_argument('--run',required=True);parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--max-file-mib',type=int,choices=[4,16],default=4);args=parser.parse_args()
    (RAW/args.project).mkdir(exist_ok=True)
    compact(RAW,args.project,[args.run],args.max_file_mib*1024**2,generation=args.generation)


if __name__=='__main__':main()
