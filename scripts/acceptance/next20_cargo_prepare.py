"""Prepare the real reviewed upstream target within one bounded acquisition/build window."""
import asyncio
import argparse
import sys

from adversarial_process import execute
from next20_check import RAW,ROOT,NextCampaign,owned_environment


async def prepare(linux_readiness_profile=2):
    if (RAW/'active/cargo-generate').exists():raise ValueError('preserve an existing native target; no automatic setup retry')
    commands=[('next20_acquire.py',['cargo-generate'],180),
        ('next20_cargo_native_source.py',[],90),
        ('next20_rust_fetch.py',['cargo-generate','--native-host'],900),
        ('next20_cargo_hook_review.py',['--native-readback'],240),
        ('next20_cargo_build.py',['--native-build'],1150),
        ('next20_cargo_host_contracts.py',['--linux-readiness-profile',str(linux_readiness_profile)],90)]
    for script,args,timeout in commands:
        await execute([sys.executable,'-B',ROOT/'scripts/acceptance'/script,*args],'cargo-generate',
            'native-prepare-'+script.removesuffix('.py'),cwd=ROOT,env=owned_environment(),timeout=timeout,campaign=NextCampaign())
    print('Fresh pinned source, reviewed locked dependencies and ordinary offline native build completed.')


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--linux-readiness-profile',type=int,choices=[2,3],default=2);args=parser.parse_args()
    # Leave40 seconds for bounded owned-process shutdown before the independent
    # 1200-second outer command deadline. Product scenario deadlines are unchanged.
    await asyncio.wait_for(prepare(args.linux_readiness_profile),timeout=1160)


if __name__=='__main__':asyncio.run(main())
