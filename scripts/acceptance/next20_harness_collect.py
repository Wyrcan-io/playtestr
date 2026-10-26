"""Collect, source-audit, retain and checked-remove one actual harness cell."""
import argparse
import asyncio
import re
import sys

from adversarial_process import execute
from next20_check import RAW, ROOT, NextCampaign, owned_environment


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    parser.add_argument('--revision',required=True);parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--host',choices=['ubuntu-24.04','macos-15','windows-2025'],required=True);args=parser.parse_args()
    if not re.fullmatch('[0-9]{1,20}',args.run) or not re.fullmatch('[0-9a-f]{40}',args.revision) or not 1<=args.generation<=1000:
        raise ValueError('Invalid exact harness collection scope')
    if any((RAW/'native').iterdir()):raise ValueError('Retain/remove current native packet before next collection')
    if (RAW/'harness'/('retained-native-v'+str(args.generation))).exists():raise ValueError('Preserve existing harness generation')
    artifact='next20-harness-'+args.host;campaign=NextCampaign()
    async def run(command,label):
        return await execute(command,'core',label,cwd=ROOT,env=owned_environment(),timeout=180,campaign=campaign)
    await run(['gh','run','download',args.run,'--repo','Wyrcan-io/playtestr','--name',artifact,
        '--dir',RAW/'native'/args.run/artifact],'collect-harness-'+args.run+'-'+args.host)
    await run([sys.executable,'-B',ROOT/'scripts/acceptance/next20_harness_audit.py',args.host,
        '--run',args.run,'--revision',args.revision,'--generation',str(args.generation)],'audit-harness-'+args.run+'-'+args.host)
    await run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        ROOT/'scripts/acceptance/next20_remove_native.ps1','-Project','harness','-Generation',str(args.generation)],
        'remove-harness-expansion-'+args.run+'-'+args.host)
    print('Actual harness cell independently source-audited, retained and expansion checked-removed:',args.run,args.host)


if __name__=='__main__':asyncio.run(main())
