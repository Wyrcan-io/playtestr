"""Freeze the current successful development package before source mutations."""
import argparse
from next20_check import DOC
from next20_jrnl_freeze import main as freeze


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    if not (DOC/args.project/'first-use.json').is_file():raise ValueError('public route required before test freeze')
    freeze(args.project,'Source and normal behavior have been reviewed. Earlier authoring/development misses remain retained in the project disposition. No concrete source mutation has been applied before this freeze; no independent human/untouched-source claim.')


if __name__=='__main__':main()
