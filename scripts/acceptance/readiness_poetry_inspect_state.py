"""Review a selected candidate through the public editor; always quit unsaved."""
import argparse
import asyncio
import os

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('spec');parser.add_argument('step',type=int)
    args=parser.parse_args()
    env=dict(os.environ)
    env['PATH']=str(RAW/'active/poetry/venv'/('Scripts' if os.name=='nt' else 'bin'))+os.pathsep+env['PATH']
    result=await execute([RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr'),
        'record','--edit',args.spec],'poetry','inspect-selected-state-without-export',
        input=f'/update-state {args.step}\n/review\n/quit\n',expected=130,env=env,timeout=120,campaign=Campaign())
    print(result['output'][-16000:])


if __name__=='__main__':asyncio.run(main())
