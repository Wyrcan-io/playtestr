"""Record a public suite invocation before launch, including every selected spec.

This wraps the unchanged public argv. It never supplies an assertion oracle,
updates a baseline, retries a failure, or treats selection as execution proof.
"""
import argparse
import asyncio
from pathlib import Path
import re

from adversarial_process import execute
from readiness_evidence import Campaign, ROOT


class SelectedCampaign(Campaign):
    def __init__(self, selection):
        super().__init__()
        self.selection=selection

    def identity(self,project,argv):
        selection=self.selection.resolve(strict=True)
        selection.relative_to(ROOT)
        if self.selection.is_symlink() or selection.stat().st_size>256*1024:
            raise ValueError('unsafe or oversized public selection')
        lines=selection.read_text(encoding='utf-8-sig').splitlines()
        if not lines or not re.fullmatch(r'Selected [1-9][0-9]* specs:',lines[0]):
            raise ValueError('public selection is missing or malformed')
        names=lines[1:]
        if len(names)!=int(lines[0].split()[1]) or len(names)>1000 or len(set(names))!=len(names):
            raise ValueError('public selection count/identity mismatch')
        selected=[]
        for name in names:
            path=ROOT/name
            if len(name)>4096 or path.is_symlink() or not path.is_file():
                raise ValueError('unsafe or missing selected specification')
            path.resolve(strict=True).relative_to(ROOT)
            selected.append(path)
        # Additional identity inputs are not additional process arguments.
        return super().identity(project,[*argv,selection,*selected])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True)
    parser.add_argument('--selection',type=Path,required=True)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',args.project):parser.error('invalid project identity')
    argv=args.command[1:] if args.command[:1]==['--'] else args.command
    if not argv:parser.error('public runner argv required')
    result=asyncio.run(execute(argv,args.project,'public-recorded-suite',timeout=900,
                              campaign=SelectedCampaign(args.selection)))
    print(result['output'][-12000:])
    print('Immutable suite attempt:',result['id'])


if __name__=='__main__':main()
