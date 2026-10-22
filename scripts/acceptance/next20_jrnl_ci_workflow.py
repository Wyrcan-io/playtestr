"""Reviewable manual-dispatch adaptation of the actual generated CI contract."""
from next20_check import RAW, ROOT, DOC
from readiness_evidence import immutable_json, sha256


def main():
    generated=RAW/'jrnl/delivered-generated.yml'
    text=generated.read_text(encoding='utf-8')
    text=text.replace('name: Playtestr recorded regression','name: Next twenty jrnl delivered CI',1)
    text=text.replace('  workflow_dispatch:\n','''  push:
    branches: [work/p0-p2-implementation]
    paths: ['.github/workflows/runner-readiness-next20-jrnl-delivered.yml']
  workflow_dispatch:
    inputs:
      mode:
        type: choice
        required: true
        options: [baseline, fault, recovered]
      route:
        type: choice
        required: true
        options: [source, private-archive]
''',1)
    text=text.replace('  contents: read\n','  contents: read\n  actions: read\n',1)
    text=text.replace('  cancel-in-progress: true','  cancel-in-progress: false',1)
    text=text.replace('jobs:\n','''env:
  JRNLCI_MODE: ${{ inputs.mode }}
  JRNLCI_ROUTE: ${{ inputs.route }}
  GH_TOKEN: ${{ github.token }}
  PYTHONDONTWRITEBYTECODE: '1'
  PYTHONIOENCODING: utf-8
  PSModuleAnalysisCachePath: ${{ github.workspace }}/artifacts/runner-readiness-next-twenty-project-pass/shell-cache/module-analysis
  GOCACHE: ${{ github.workspace }}/artifacts/runner-readiness-next-twenty-project-pass/go-cache
  GOMODCACHE: ${{ github.workspace }}/artifacts/runner-readiness-next-twenty-project-pass/gopath/pkg/mod
jobs:
''',1)
    text=text.replace('  terminal:\n','  terminal:\n    if: github.event_name == \'workflow_dispatch\'\n',1)
    text=text.replace('      fail-fast: false\n','      fail-fast: false\n      max-parallel: 2\n',1)
    text+='''      - name: Restore actual source and checked-remove owned target
        if: always() && steps.prepare.outcome == 'success' && steps.tests.outcome != 'skipped'
        run: python -B scripts/acceptance/next20_check.py --label delivered-jrnl-checked-restoration-cleanup --timeout 900 -- python -B scripts/acceptance/next20_jrnl_ci.py cleanup
      - uses: actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f
        if: always()
        with:
          name: next20-jrnl-delivered-${{ runner.os }}
          path: |
            artifacts/runner-readiness-next-twenty-project-pass/jrnl/delivered-ci/
            artifacts/runner-readiness-next-twenty-project-pass/jrnl/host-contracts/
            artifacts/runner-readiness-next-twenty-project-pass/jrnl/process-proof.json
            artifacts/runner-readiness-next-twenty-project-pass/jrnl/retained-source/*.json
            artifacts/runner-readiness-next-twenty-project-pass/jrnl/*/console.log
            artifacts/runner-readiness-next-twenty-project-pass/core/
            artifacts/runner-readiness-next-twenty-project-pass/candidate/*/installed.json
            artifacts/runner-readiness-next-twenty-project-pass/events/
            artifacts/runner-readiness-next-twenty-project-pass/identities/
          include-hidden-files: true
          if-no-files-found: error
          retention-days: 14
'''
    workflow=ROOT/'.github/workflows/runner-readiness-next20-jrnl-delivered.yml'
    with workflow.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
    immutable_json(DOC/'jrnl/delivered-ci-declaration.json',dict(schema_version=1,
        generated_workflow_sha256=sha256(generated),dispatched_workflow_sha256=sha256(workflow),
        source_revision='294d6e42f6c0965a4e090aa11835941984d32a0a',
        modes=['baseline','fault','recovered'],routes=['source','private-archive'],
        planned_runs=6,hosts=['linux','windows'],standard_jobs=12,max_simultaneous_target_jobs=2,
        job_deadline_minutes=30,total_job_minute_ceiling=360,estimated_job_minutes=80,
        adaptation='Manual inputs, scoped push registration with skipped job, max two target jobs, owned caches, read-only artifact token and always restoration/evidence. Generated runner build, test, report, context and summary steps unchanged.',
        override='Private-archive route explicitly replaces PLAYTESTR_BIN after exact frozen archive install in target build. It is separate from source-built delivered-route credit.',
        failure='Real F03 source corruption must fail the unchanged file oracle after passed screen/exit, make provider job non-success and retain rendered report. Recovery runs fresh source matching the declared original.',
        retention='CI inventories reference wheel/source bytes already retained in native generations; cross-packet hash closure required. No runtime/cache upload.',
        applicability='Manual dispatch only; no real PR/fork journey or publication claim.',new_project_credit=0))
    print('Prepared explicit generated-contract CI triplets; no execution credit.')


if __name__=='__main__':main()
