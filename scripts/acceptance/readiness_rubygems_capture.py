"""Explicit selected public review routes; captures are never independent oracles."""
import argparse
import asyncio
import json
import os
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT
from readiness_rubygems_cases import PACKAGE, OPTIONS, environment


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--inspect',nargs=2,metavar=('SPEC','STEP'))
    parser.add_argument('--case',choices=['N02','E04'])
    args=parser.parse_args()
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    if args.inspect:
        spec,step=args.inspect
        argv=[runner,'record','--edit',str((PACKAGE/spec).relative_to(ROOT))]
        controls=f'/update-state {int(step)}\n/review\n/quit\n'
        expected=130
    else:
        ref=json.loads((PACKAGE/'normal-gem.json').read_text())
        name='normal-extension.json' if args.case=='N02' else 'wrong-type-review-'+uuid.uuid4().hex+'.json'
        output=PACKAGE/name if args.case=='N02' else RAW/'rubygems'/name
        fixture=PACKAGE/('fixture' if args.case=='N02' else 'wrong-type-fixture')
        argv=[runner,'record','--output',output.relative_to(ROOT),'--fixture',fixture.name,
              '--temporary-home','--temporary-temp','--inherit-env','RUBYLIB','--width','160','--height','100',
              '--timeout-ms','10000','--run-timeout-ms','120000']
        # Fixture must be relative to exported spec. Both routes stay in package.
        if args.case=='E04':
            output=PACKAGE/name;argv[3]=str(output.relative_to(ROOT));argv[5]='wrong-type-fixture'
        for key,value in ref['env'].items():argv+=['--env',key+'='+value]
        argv+=['--','ruby','-EUTF-8','-S','bundle','gem',
               'native_atlas' if args.case=='N02' else 'blocked/atlas',*OPTIONS,'--test=rspec']
        if args.case=='N02':
            argv+=['--ext=c']
            controls="/expect Gem 'native_atlas' was successfully created.\n/exit 0\n"
            for path in ['ext/native_atlas/native_atlas.c','ext/native_atlas/native_atlas.h','ext/native_atlas/extconf.rb','lib/native_atlas.rb','lib/native_atlas/version.rb']:
                controls+='/file native_atlas/'+path+'\n'
            controls+='/entries native_atlas/ext/native_atlas\n/file sentinel.txt\n/review\n/replay\n/save\n'
        else:controls='/exit 1\n/snapshot wrong-type-review.txt\n/review\n/quit\n'
        expected=0 if args.case=='N02' else 130
    result=await execute(argv,'rubygems','public-selected-review-'+str(args.case or args.inspect[0]),
        input=controls,expected=expected,env=environment(),timeout=180,campaign=Campaign())
    print(result['output'][-24000:])


if __name__=='__main__':asyncio.run(main())
