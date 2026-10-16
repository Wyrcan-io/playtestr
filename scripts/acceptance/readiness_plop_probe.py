"""Bounded public recorder startup diagnosis; no test is exported."""
import asyncio
import os

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT


async def main():
    env=dict(os.environ)
    env['PATH']=str(RAW/'active/plop/bin')+os.pathsep+env['PATH']
    suffix='.exe' if os.name=='nt' else ''
    runner=RAW/'bin'/('playtestr'+suffix)
    await execute(['go','build','-o',runner,'./cmd/playtestr'],'plop','build-startup-probe-runner',env=env,timeout=120,campaign=Campaign())
    forms=[('shell-launcher',['cmd.exe','/d','/s','/c','plop --no-progress'])] if os.name=='nt' else []
    forms.append(('node-direct',['node',str(RAW/'active/plop/src/packages/plop/bin/plop.js'),'--no-progress']))
    for label,argv in forms:
        result=await execute([runner,'record','--output','docs/validation/runner-readiness-ten-project-pass/plop/diagnostic-no-export.json',
                              '--fixture','fixture','--temporary-home','--temporary-temp','--timeout-ms','3000',
                              '--run-timeout-ms','30000','--',*argv],'plop','startup-probe-'+label,
                             env=env,input='/expect Artifact name\n/screen\n/quit\n',expected=130,timeout=40,campaign=Campaign())
        print(label,result['output'][-3000:])


if __name__=='__main__':asyncio.run(main())
