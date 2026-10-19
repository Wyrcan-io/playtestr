"""Execute exact committed native Rclone contracts on the frozen runner."""
import asyncio
import os
import platform
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_build_rclone import environment
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


def native_profile():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'
    if platform.system()=='Windows':return docs/'native-profiles/windows'
    if platform.system()!='Linux':raise RuntimeError('undeclared Rclone native profile')
    return docs


def target_environment():
    target=RAW/'active/rclone';env=environment(target)
    env['PATH']=str(target/'bin')+os.pathsep+env.get('PATH','')
    return env


async def main():
    profile=native_profile();frozen=load(profile/'reviewed-contract-freeze.json')
    if len(frozen['contracts'])!=20:raise RuntimeError('twenty frozen contracts required')
    for name,digest in frozen['all_package_inputs'].items():
        if sha256(profile/'contracts'/name)!=digest:raise RuntimeError('committed native input changed')
    package=RAW/'rclone/host-contracts';shutil.copytree(profile/'contracts',package)
    immutable_json(RAW/'rclone/native-profile.json',dict(host=platform.system(),
        freeze_sha256=sha256(profile/'reviewed-contract-freeze.json'),profile=profile.relative_to(ROOT).as_posix(),changes='None'))
    root=RAW/'rclone/suites'/uuid.uuid4().hex;root.mkdir(parents=True)
    binary,candidate,cell=runner();env=target_environment()
    listing=await execute([binary,'test','--list',package],'rclone','native-reviewed-twenty-directory-list',env=env,timeout=30,campaign=Campaign())
    selection=root/'selected.txt';selection.write_text(listing['output'],encoding='utf-8',newline='\n')
    report=root/'results.json'
    result=await execute([sys.executable,'scripts/acceptance/readiness_public_suite.py','--project','rclone',
        '--selection',selection,'--',binary,'test','--report',report.relative_to(ROOT),
        '--artifacts-dir',(root/'evidence').relative_to(ROOT),package.relative_to(ROOT)],
        'rclone','native-reviewed-twenty-suite-parent',env=env,timeout=600,campaign=Campaign())
    outcome=load(report)
    if outcome['runner_version']!=candidate['version'] or outcome['summary']!=dict(total=20,passed=20,failed=0,cancelled=0,not_run=0):
        raise RuntimeError('native frozen suite incomplete')
    for row in outcome['results']:
        if not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise RuntimeError('native cleanup unconfirmed')
    immutable_json(root/'verified.json',dict(parent=result['id'],report_sha256=sha256(report),runner_sha256=cell['binary_sha256'],
        provisional_archive_sha256=cell['archive_sha256'],canonical_freeze_sha256=sha256(profile/'reviewed-contract-freeze.json'),final_archive_credit=0))
    print('Exact twenty-case native Rclone profile passed.')


if __name__=='__main__':asyncio.run(main())
