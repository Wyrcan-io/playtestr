"""Compile/probe a test-only per-process Linux socket guard in owned paths."""
import asyncio
import platform
import shutil

from adversarial_process import execute
from readiness_build_rclone import environment
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    if platform.system()!='Linux' or platform.machine()!='x86_64':
        raise RuntimeError('socket policy experiment declares native Linux amd64 only')
    root=RAW/'offline-guard'
    root.mkdir()
    env=environment(root)
    env.update(GOPROXY='off',GOSUMDB='off',GO111MODULE='off')
    source=root/'main.go'
    shutil.copyfile(ROOT/'scripts/acceptance/readiness_socket_guard.go.txt',source)
    compiler=RAW/'toolchain/go/bin/go'
    binary=root/'guard'
    built=await execute([compiler,'build','-trimpath','-o',binary,source], 'core',
        'offline-guard-reviewed-fixture-build',env=env,timeout=180,campaign=Campaign())
    probes={}
    for name,flag,expected in [('baseline','--baseline-probe','socket-created-and-closed; no connection attempted'),
                               ('guarded','--guard-probe','socket-denied=EPERM')]:
        result=await execute([binary,flag],'core','offline-guard-'+name,env=env,timeout=30,campaign=Campaign())
        if result['output'].strip()!=expected:
            raise RuntimeError('socket policy control did not produce its positive evidence')
        probes[name]=result['id']
    immutable_json(root/'verified.json',dict(build_attempt=built['id'],probes=probes,
        source_sha256=sha256(source),binary_sha256=sha256(binary),compiler_sha256=sha256(compiler),
        scope='A normal IP socket can be created/closed without connecting. The same launcher under its process-local filter receives EPERM. No firewall, host configuration or OS network isolation change. Trusted fixture only; not a security sandbox.'))
    print('Built/probed process-scoped socket guard; application execution still required.')


if __name__=='__main__':asyncio.run(main())
