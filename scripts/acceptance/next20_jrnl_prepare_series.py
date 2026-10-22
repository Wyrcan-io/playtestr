"""Prepare a finite exact-archive native series; writing this file runs no jobs."""
from next20_check import DOC,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'jrnl'
    batches=[
        dict(id=0,name='ordinary-cold-1',runtime='new verified owned venv-pair-0; first logical use'),
        dict(id=1,name='ordinary-warm-1',runtime='reuse exact venv-pair-0'),
        dict(id=2,name='ordinary-cold-2',runtime='new verified owned venv-pair-1; first logical use'),
        dict(id=3,name='ordinary-warm-2',runtime='reuse exact venv-pair-1'),
        dict(id=4,name='viewport',change='initial width +10, height +2; all reviewed saved bytes unchanged'),
        dict(id=5,name='spaced-unicode-path',change='package relocated to relative path containing café 雪; explicit relative executable rebinding'),
        dict(id=6,name='ordinary-input-readiness',change='original supported actions and positive checkpoints'),
        dict(id=7,name='segmented-printable-input',change='split printable text into three-codepoint groups; key/control groups remain atomic'),
        dict(id=8,name='bounded-contention-1',change='owned 2-second 8-MiB SHA256 worker during each invocation'),
        dict(id=9,name='bounded-contention-2',change='second distinct execution under the same bounded owned worker schedule'),
        dict(id=10,name='highest-risk-small-completion',change='N01 viewport height 12; remaining dedicated edge boundaries preserved unchanged'),
        dict(id=11,name='highest-risk-startup-boundary',change='explicit 2000ms startup limit; ordinary step/run budgets unchanged'),
    ]
    declaration=dict(schema_version=1,project='jrnl',revision=1,hosts=['linux','windows'],
        canonical_test_freeze_sha256=sha256(package/'development-test-freeze.json'),
        native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),
        candidate='unchanged exact v0.4.0-rc.5 archives from 39450029736',batches=batches,
        scenarios_per_cell=20,normal=8,edge=12,repetitions_per_cell=12,ordinary_required=480,
        real_source_faults=3,calibration_required=18,
        original_first_development_failures='16 passed / 4 failed in initial 20; all retained. Replacement development series passed 20/20. Neither is final repetition credit.',
        excluded_target_behavior='Chronological file reordering after a retime crossing another entry remains an observed upstream gap; original failed workflow retained and excluded.',
        transfer_scope='All source and three mutations have been exposed locally; no untouched native transfer claim.',
        cold_scope='Freshly materialized verified target runtime followed by reuse, not OS-cache eviction or hardware cold-start proof.',
        failure_policy='No automatic per-case retry. Any red/partial final batch rejects the affected native series; retain all first attempts and declare a replacement after diagnosis.',
        dispatch_budget=dict(standard_hosted=True,target_jobs=2,max_parallel=2,job_ceiling_minutes=40,
            total_job_minute_ceiling=80,estimated_minutes=dict(linux=8,windows=12),
            automatic_harness_push_jobs=3,harness_job_ceiling_minutes=5,harness_max_parallel=2,
            queue_policy='Inspect provider at 15 queued minutes; one declared replacement at 30 only after original termination/completion is confirmed. No paid runner/budget changes.'),
        new_project_admissions=0)
    immutable_json(package/'final-series-declaration.json',declaration)
    prefix='artifacts/runner-readiness-next-twenty-project-pass'
    workflow='''name: Next twenty jrnl exact archive series
on:
  workflow_dispatch:
permissions:
  contents: read
  actions: read
concurrency:
  group: playtestr-next20-jrnl
  cancel-in-progress: false
env:
  PYTHONDONTWRITEBYTECODE: '1'
  PYTHONIOENCODING: utf-8
  TEMP: ${{ github.workspace }}/ARTIFACT_ROOT/tmp
  TMP: ${{ github.workspace }}/ARTIFACT_ROOT/tmp
  TMPDIR: ${{ github.workspace }}/ARTIFACT_ROOT/tmp
  RUNNER_TEMP: ${{ github.workspace }}/ARTIFACT_ROOT/tmp
  PSModuleAnalysisCachePath: ${{ github.workspace }}/ARTIFACT_ROOT/shell-cache/module-analysis
  GIT_CONFIG_COUNT: '1'
  GIT_CONFIG_KEY_0: core.longpaths
  GIT_CONFIG_VALUE_0: 'true'
jobs:
  native-final:
    timeout-minutes: 40
    strategy:
      fail-fast: false
      max-parallel: 2
      matrix:
        include:
          - os: ubuntu-24.04
            host: linux
            target: linux-amd64
            archive_target: linux_amd64
            extension: tar.gz
          - os: windows-2025
            host: windows
            target: windows-amd64
            archive_target: windows_amd64
            extension: zip
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        shell: bash
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803
        with:
          persist-credentials: false
          set-safe-directory: false
      - name: Create owned temporary/cache paths
        run: mkdir -p "$GITHUB_WORKSPACE/ARTIFACT_ROOT/tmp" "$GITHUB_WORKSPACE/ARTIFACT_ROOT/shell-cache"
      - uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093
        with:
          github-token: ${{ github.token }}
          repository: Wyrcan-io/playtestr
          run-id: 39450029736
          name: private-candidate-${{ runner.os }}
          path: ARTIFACT_ROOT/candidate-download
      - name: Verify and install exact frozen private archive
        run: python -B scripts/acceptance/next20_check.py --label native-jrnl-exact-archive-install --timeout 90 -- python -B scripts/acceptance/next20_candidate_install.py --archive ARTIFACT_ROOT/candidate-download/candidate-packages/migration-v2/${{ matrix.target }}/dist/playtestr_0.4.0-rc.5_${{ matrix.archive_target }}.${{ matrix.extension }}
      - name: Prepare reviewed pinned target with owned runtime and exact native contracts
        id: prepare
        run: python -B scripts/acceptance/next20_check.py --label native-jrnl-reviewed-target-preparation --timeout 1200 -- python -B scripts/acceptance/next20_jrnl_native_prepare.py
'''.replace('ARTIFACT_ROOT',prefix)
    for batch in range(12):
        workflow+=f'''      - name: Final fresh-state batch {batch+1} of twelve
        env:
          READINESS_EVIDENCE_PHASE: final-archive
        run: python -B scripts/acceptance/next20_check.py --label native-jrnl-final-batch-{batch} --timeout 900 -- python -B scripts/acceptance/next20_jrnl_final.py --batch {batch}
'''
    workflow+='''      - name: Three actual source faults and unchanged-contract recovery
        env:
          READINESS_EVIDENCE_PHASE: final-archive
        run: python -B scripts/acceptance/next20_check.py --label native-jrnl-real-fault-restoration --timeout 900 -- python -B scripts/acceptance/next20_jrnl_faults.py --package ARTIFACT_ROOT/jrnl/host-contracts
      - name: Windows target PID and birth proof
        if: always() && steps.prepare.outcome == 'success' && runner.os == 'Windows'
        run: python -B scripts/acceptance/next20_check.py --label native-jrnl-owned-process-proof --timeout 90 -- powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/acceptance/next20_target_process_proof.ps1 -Project jrnl
      - name: Retain source provenance and prepare native Windows removal
        if: always() && steps.prepare.outcome == 'success' && runner.os == 'Windows'
        run: python -B scripts/acceptance/next20_check.py --label native-jrnl-source-retention --timeout 180 -- python -B scripts/acceptance/next20_target_cleanup.py --project jrnl --prepare-only
      - name: Checked Windows source and runtime removal
        if: always() && steps.prepare.outcome == 'success' && runner.os == 'Windows'
        run: python -B scripts/acceptance/next20_check.py --label native-jrnl-source-runtime-removal --timeout 180 -- powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/acceptance/next20_remove_target.ps1 -Project jrnl
      - name: Checked Unix source and runtime removal
        if: always() && steps.prepare.outcome == 'success' && runner.os != 'Windows'
        run: python -B scripts/acceptance/next20_check.py --label native-jrnl-source-runtime-removal --timeout 180 -- python -B scripts/acceptance/next20_target_cleanup.py --project jrnl
      - uses: actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f
        if: always()
        with:
          name: next20-jrnl-${{ runner.os }}
          path: |
            ARTIFACT_ROOT/events/
            ARTIFACT_ROOT/identities/
            ARTIFACT_ROOT/core/
            ARTIFACT_ROOT/jrnl/
            ARTIFACT_ROOT/candidate/*/installed.json
          include-hidden-files: true
          if-no-files-found: error
          retention-days: 14
'''.replace('ARTIFACT_ROOT',prefix)
    path=ROOT/'.github/workflows/runner-readiness-next20-jrnl.yml'
    with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(workflow)
    print('Prepared exact rc.5 two-native-host, twelve-batch jrnl series; 80 target-job-minute ceiling, no jobs dispatched.')


if __name__=='__main__':main()
