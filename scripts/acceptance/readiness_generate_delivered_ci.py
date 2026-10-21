"""Generate the public free-CI template, then declare narrow campaign adapters."""
import asyncio
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner


async def main():
    binary,candidate,cell=runner('migration-v2')
    root=RAW/'delivered-ci-generation'/uuid.uuid4().hex
    root.mkdir(parents=True)
    raw=root/'generated.yml'
    destination=ROOT/'.github/workflows/runner-readiness-delivered-ci.yml'
    if destination.exists():raise RuntimeError('refuse existing generated CI harness')
    build='python scripts/acceptance/readiness_delivered_ci_target.py --phase prepare --mode "$PLAYTESTR_CI_MODE"'
    immutable_json(root/'declared.json',dict(candidate_source=candidate['source_revision'],generator_binary_sha256=cell['binary_sha256'],
        suite='artifacts/runner-readiness-ten-project-pass/rclone/host-contracts/N02.json',build=build,
        modes=['success','corruption','recovery'],hosts=['linux-amd64'],
        scope='Actual delivered workflow body and pinned source-build route. Explicit target prerequisite script builds the real reviewed Rclone pin. Campaign-only event/owned-cache/checkout/cleanup adapters are recorded; no real PR event or exact-archive project credit.'))
    result=await execute([binary,'workflow','--source-revision',candidate['source_revision'],'--os','linux',
        '--suite','artifacts/runner-readiness-ten-project-pass/rclone/host-contracts/N02.json','--build',build,
        '--job-timeout-minutes','40','--retention-days','14','--output',raw],
        'core','delivered-free-ci-public-template-generation',timeout=30,campaign=Campaign())
    text=raw.read_text(encoding='utf-8')
    original_events='''on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  workflow_dispatch:
'''
    events='''on:
  push:
    branches: [work/p0-p2-implementation]
    paths: ['.github/workflows/runner-readiness-delivered-ci.yml']
  workflow_dispatch:
    inputs:
      mode:
        description: Actual real-target success, saved-extra fault or clean recovery
        type: choice
        options: [success, corruption, recovery]
        default: success
'''
    if text.count(original_events)!=1:raise RuntimeError('delivered event template changed before review')
    text=text.replace('name: Playtestr recorded regression','name: Runner readiness delivered free CI',1).replace(original_events,events,1)
    env='''env:
  PYTHONDONTWRITEBYTECODE: '1'
  PYTHONIOENCODING: utf-8
  GOTOOLCHAIN: local
  GOTELEMETRY: 'off'
  GOENV: 'off'
  GOMAXPROCS: '2'
  GOMEMLIMIT: 2GiB
  HOME: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/home
  USERPROFILE: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/home
  XDG_CACHE_HOME: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/cache
  TEMP: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/tmp
  TMP: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/tmp
  TMPDIR: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/tmp
  RUNNER_TEMP: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/tmp
  RUNNER_TOOL_CACHE: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/tool-cache
  GOCACHE: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/go-cache
  GOPATH: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/gopath
  GOMODCACHE: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/gopath/pkg/mod
  PIP_CACHE_DIR: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/pip-cache
  PYTHONUSERBASE: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/python-user
  GIT_CONFIG_NOSYSTEM: '1'
  GIT_CONFIG_GLOBAL: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/ci/home/gitconfig
  READINESS_IDENTITY_CATALOG_PROJECT: rclone
  PLAYTESTR_CI_MODE: ${{ inputs.mode }}
'''
    text=text.replace('concurrency:\n',env+'concurrency:\n',1)
    text=text.replace('  terminal:\n','  terminal:\n    if: github.event_name == \'workflow_dispatch\'\n',1)
    text=text.replace('          persist-credentials: false\n',
        '          persist-credentials: false\n          set-safe-directory: false\n          clean: false\n')
    prep='''      - name: Prepare campaign-owned caches before checkout and SDK actions
        run: |
          owned="$GITHUB_WORKSPACE/artifacts/runner-readiness-ten-project-pass"
          mkdir -p "$owned/ci/home" "$owned/ci/cache" "$owned/ci/tmp" "$owned/ci/tool-cache" "$owned/ci/go-cache" "$owned/ci/gopath/pkg/mod" "$owned/ci/pip-cache" "$owned/ci/python-user"
'''
    text=text.replace('    steps:\n','    steps:\n'+prep,1)
    cleanup='''      - name: Verify real target restoration, preserve provenance and remove owned source/runtime
        if: always() && steps.prepare.outcome == 'success'
        run: python scripts/acceptance/readiness_delivered_ci_target.py --phase finalize --mode "$PLAYTESTR_CI_MODE"
'''
    marker='      - name: Accessible outcome summary\n'
    if text.count(marker)!=1:raise RuntimeError('delivered summary boundary changed')
    text=text.replace(marker,cleanup+marker,1)
    destination.write_text(text,encoding='utf-8',newline='\n')
    immutable_json(root/'generated.json',dict(generation_attempt=result['id'],original_sha256=sha256(raw),
        adapted_sha256=sha256(destination),original_path=raw.relative_to(ROOT).as_posix(),
        adapted_path=destination.relative_to(ROOT).as_posix(),source_revision=candidate['source_revision'],
        adapters=['Unique acceptance name and dispatch modes; PR trigger removed, branch-only no-op registration added.',
            'Owned SDK/cache/home/temp paths and explicit target mode.',
            'Checkout clean/safe-directory disabled to preserve owned directories and avoid global Git configuration.',
            'Always cleanup after real public test/report, with exact source/binary restoration and bounded build evidence.'],
        preserved='Delivered source build, actual public context/list/test/report/summary/artifact body and Action pins unchanged.',
        real_pr_event_proven=False,final_archive_credit=0))
    print('Generated actual public free-CI template and recorded campaign adapters:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
