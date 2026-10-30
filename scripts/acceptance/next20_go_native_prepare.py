"""Prepare reviewed native Go code, bounded capture and exact host contracts."""
import argparse
import asyncio
import json
import os
import sys

from adversarial_process import execute
from next20_check import DOC,RAW,ROOT,NextCampaign,owned_environment


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project or not (DOC/project/'native-module-lock.json').is_file():raise ValueError('reviewed Go native lock required')
    if (RAW/'active'/project).exists():raise ValueError('preserve existing owned Go target; no automatic retry')
    if os.name=='nt':raise ValueError('this fresh hosted preparation is currently declared for native Linux')
    env=owned_environment();campaign=NextCampaign()
    async def run(script,arguments,limit):
        return await execute([sys.executable,'-B',ROOT/'scripts/acceptance'/script,*arguments],project,'native-go-prepare-'+script.removesuffix('.py'),cwd=ROOT,env=env,timeout=limit,campaign=campaign)
    acquisition=[project];tree=[project,'--verify-existing'];policy=DOC/project/'source-link-policy.json'
    if policy.is_file():
        acquisition+=['--omitted-documentation-links',policy];tree+=['--omitted-documentation-links',policy]
    await run('next20_acquire.py',acquisition,180)
    await run('next20_source_tree.py',tree,120)
    await run('next20_go_sdk.py',[project],360)
    env['PATH']=str(RAW/'active'/project/'toolchain/go/bin')+os.pathsep+env['PATH']
    await run('next20_go_fetch.py',[project],240)
    await run('next20_go_inspect.py',[project,'--native-module-lock'],210)
    await run('next20_go_review.py',[project],180)
    await run('next20_go_metadata_readback.py',[project],90)
    await run('next20_go_build.py',[project],1000)
    target=RAW/'active'/project;fetch=json.loads((target/'module-fetch.json').read_text());review=json.loads((DOC/project/'dependency-source-review-declaration.json').read_text())
    from readiness_build_rclone import environment
    fixture_env=environment(target);fixture_env.update(GOENV='off',GOPROXY='off',GOSUMDB='off')
    helper=ROOT/review['capture_helper']
    await execute([fetch['compiler'],'test','-v','-mod=readonly','-modfile='+str(target/'build-inputs/pinned.mod'),str(helper),str(helper.with_name('main_test.go'))],project,
        'native-bounded-stdout-capture-real-process-regressions',cwd=target/'src',env=fixture_env,timeout=150,campaign=campaign)
    await run('next20_go_host_contracts.py',[project],90)
    print('Prepared exact pinned native Go target,all reviewed module sources,bounded real-process capture and frozen host contracts.')


if __name__=='__main__':asyncio.run(main())
