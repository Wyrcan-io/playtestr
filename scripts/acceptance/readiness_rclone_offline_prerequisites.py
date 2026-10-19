"""Inspect the cached full CLI dependency graph without another build or network."""
import asyncio
import os

from adversarial_process import execute
from readiness_build_rclone import environment
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


async def main():
    target=RAW/'active/rclone'
    review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone/source-review.json')
    for name in ['go.mod','go.sum']:
        if sha256(target/'src'/name)!=review['reviewed_inputs'][name]:raise RuntimeError('original dependency lock changed')
    go=target/'toolchain/go/bin'/('go.exe' if os.name=='nt' else 'go')
    env=environment(target)
    env.update(GOPROXY='off',GOSUMDB='off')
    result=await execute([go,'list','-mod=readonly','-deps','-e','-f',
        '{{if .Error}}{{.ImportPath}}: {{.Error.Err}}{{end}}','.'],
        'rclone','offline-cached-main-package-prerequisite-probe',cwd=target/'src',env=env,
        timeout=120,output_cap=1024**2,campaign=Campaign())
    errors=[line for line in result['output'].splitlines() if line.strip()]
    immutable_json(RAW/'rclone/offline-prerequisite-probe.json',dict(attempt=result['id'],
        compiler_sha256=sha256(go),go_mod_sha256=sha256(target/'src/go.mod'),go_sum_sha256=sha256(target/'src/go.sum'),
        package_errors=errors,graph_has_no_reported_errors=not errors,
        proxy_disabled=True,sumdb_disabled=True,target_built=False,target_executed=False,
        qualification='One bounded prerequisite diagnostic only. No dependency acquisition, build success or runtime coverage claimed.'))
    print('Offline full-CLI prerequisite probe:',len(errors),'reported package/dependency lines; no build or target execution.')


if __name__=='__main__':asyncio.run(main())
