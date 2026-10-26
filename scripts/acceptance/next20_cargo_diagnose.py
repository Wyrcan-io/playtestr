"""Inspect the first recorder startup failure with the public screen command."""
import asyncio
import os

from adversarial_process import execute
from next20_check import RAW,DOC,ROOT,NextCampaign
from next20_python_setup import environment


async def main():
    target=RAW/'active/cargo-generate';package=DOC/'cargo-generate'
    runner=RAW/'candidate/windows/playtestr.exe'
    relative=os.path.relpath(target/'bin/cargo-generate.exe',package).replace('\\','/')
    result=await execute([runner,'record','--output',(package/'diagnostic-draft.json').relative_to(ROOT),
        '--fixture','fixture','--temporary-home','--temporary-temp','--env','GIT_CONFIG_NOSYSTEM=1',
        '--env','GIT_CONFIG_GLOBAL='+os.devnull,'--timeout-ms','10000','--run-timeout-ms','120000',
        '--',relative,'generate','--path','template','--vcs','none','--no-workspace'],
        'cargo-generate','first-route-public-startup-screen',cwd=ROOT,env=environment(target),
        input='/exit 1\n/screen\n/quit\n',expected=130,timeout=120,campaign=NextCampaign())
    print(result['output'])


if __name__=='__main__':asyncio.run(main())
