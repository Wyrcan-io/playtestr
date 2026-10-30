"""Install the declared official Go prerequisite under one owned target root."""
import argparse
import json

from next20_check import DOC,RAW,ROOT,NAME
import readiness_bootstrap_go as bootstrap


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe owned SDK project')
    target=RAW/'active'/project;owner=json.loads((target/'task-owned.json').read_text());lock=json.loads((DOC/project/'native-module-lock.json').read_text())
    if owner['workspace']!=str(ROOT) or owner['campaign']!=NAME or owner['slug']!=project or owner['pin']!=lock['pin'] or lock['compiler_version']!='go1.27.0':raise ValueError('foreign target or undeclared Go SDK')
    bootstrap.VERSION=lock['compiler_version'];bootstrap.main(owned=target/'toolchain')


if __name__=='__main__':main()
