"""Collect, independently audit, retain and checked-remove one CI host packet."""
import argparse
import asyncio
import os
import re
import sys

from adversarial_process import execute
from next20_check import RAW,ROOT,NextCampaign,owned_environment


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--host',choices=['linux','windows'],required=True)
    parser.add_argument('--mode',choices=['baseline','fault','recovered'],required=True)
    parser.add_argument('--route',choices=['source','private-archive'],required=True)
    parser.add_argument('--generation',type=int,required=True)
    args=parser.parse_args();project='commitizen-python'
    if os.name!='nt':raise ValueError('Local checked PowerShell collection adapter requires Windows')
    if not re.fullmatch('[0-9]{1,20}',args.run) or not 1<=args.generation<=1000:raise ValueError('Invalid collection scope')
    native=RAW/'native';native.mkdir(exist_ok=True)
    if any(native.iterdir()):raise ValueError('Finish existing native packet retention/removal before next collection')
    if (RAW/project/('retained-native-v'+str(args.generation))).exists():raise ValueError('Retention generation already exists')
    campaign=NextCampaign()
    async def run(argv,label,timeout=180):
        return await execute(argv,'core',label,cwd=ROOT,env=owned_environment(),timeout=timeout,campaign=campaign)
    label='Linux' if args.host=='linux' else 'Windows'
    for artifact in ['playtestr-'+label,'next20-'+project+'-delivered-'+label]:
        await run(['gh','run','download',args.run,'--name',artifact,'--dir',native/args.run/artifact],
            'collect-'+args.run+'-'+artifact)
    await run([sys.executable,'-B',ROOT/'scripts/acceptance/next20_python_ci_audit.py',
        '--run',args.run,'--host',args.host,'--mode',args.mode,'--route',args.route,
        '--generation',str(args.generation)],'independent-ci-audit-'+args.run+'-'+args.host,240)
    await run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        ROOT/'scripts/acceptance/next20_remove_native.ps1','-Project',project,
        '-Generation',str(args.generation)],'checked-ci-expansion-removal-'+args.run+'-'+args.host,180)
    print('One actual CI host observation independently audited, retained, expansion removed:',args.run,args.host)


if __name__=='__main__':asyncio.run(main())
