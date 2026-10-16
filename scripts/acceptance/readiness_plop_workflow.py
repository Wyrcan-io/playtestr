"""Prepare the reviewed hosted derivative of the public generated Plop workflow."""
from readiness_evidence import ROOT, immutable_json, sha256


def main():
    original=ROOT/'docs/validation/runner-readiness-ten-project-pass/plop/free-workflow.generated.yml'
    output=ROOT/'.github/workflows/runner-readiness-plop.yml'
    if output.exists():raise RuntimeError('review existing workflow; do not silently replace it')
    text=original.read_text(encoding='utf-8')
    def replace(old,new):
        nonlocal text
        if text.count(old)!=1:raise RuntimeError('generated workflow anchor changed')
        text=text.replace(old,new)
    replace('name: Playtestr recorded regression','name: Runner readiness Plop native')
    replace('  pull_request:\n    types: [opened, synchronize, reopened, ready_for_review]\n  workflow_dispatch:',
            "  push:\n    branches: [work/p0-p2-implementation]\n    paths: ['.github/workflows/runner-readiness-plop.yml']\n  workflow_dispatch:")
    replace('  terminal:\n','  terminal:\n    if: github.event_name == \'workflow_dispatch\'\n')
    replace('      fail-fast: false\n','      fail-fast: false\n      max-parallel: 2\n')
    text=text.replace('          persist-credentials: false\n','          persist-credentials: false\n          set-safe-directory: false\n')
    replace("      - uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e\n        with:\n          go-version-file: .playtestr-tooling/go.mod\n          cache: false\n      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1\n        with:\n          python-version: '3.12'\n",'''      - name: Bootstrap official SDK only inside checkout
        run: |
          mkdir -p "$TEMP" "$GOCACHE" "$GOPATH"
          python3 scripts/acceptance/readiness_check.py --label plop-native-sdk --timeout 360 -- python3 scripts/acceptance/readiness_bootstrap_go.py
''')
    replace('permissions:\n', '''env:
  SOURCE_REVISION: 'e5571bdd05a63448c875b8f1da1412e9810aac75'
  PYTHONDONTWRITEBYTECODE: '1'
  PYTHONIOENCODING: utf-8
  GOTOOLCHAIN: local
  TEMP: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/tmp
  TMP: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/tmp
  TMPDIR: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/tmp
  GOTMPDIR: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/tmp
  GOCACHE: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/go-cache
  GOPATH: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/gopath
  GOMODCACHE: ${{ github.workspace }}/artifacts/runner-readiness-ten-project-pass/gopath/pkg/mod
permissions:
''')
    text=text.replace('          python .playtestr-tooling/', '          python3 .playtestr-tooling/')
    replace('      - uses: actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f', '''      - name: Real source faults and public maintenance
        if: always() && steps.context.outcome == 'success'
        run: |
          python3 scripts/acceptance/readiness_check.py --label native-plop-faults-parent --timeout 900 -- python3 scripts/acceptance/readiness_plop_faults.py --package artifacts/runner-readiness-ten-project-pass/plop/host-contracts
          python3 scripts/acceptance/readiness_check.py --label native-plop-maintenance-parent --timeout 900 -- python3 scripts/acceptance/readiness_plop_maintenance.py --package artifacts/runner-readiness-ten-project-pass/plop/host-contracts
      - name: Verify retained source restore and remove owned target
        if: always() && steps.prepare.outcome == 'success'
        run: |
          python3 scripts/acceptance/readiness_check.py --label native-plop-cleanup-parent --timeout 120 -- python3 scripts/acceptance/readiness_cleanup_plop.py
      - uses: actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f''')
    replace('          path: artifacts/playtestr/', '''          path: |
            artifacts/playtestr/
            artifacts/runner-readiness-ten-project-pass/events/
            artifacts/runner-readiness-ten-project-pass/identities/
            artifacts/runner-readiness-ten-project-pass/core/
            artifacts/runner-readiness-ten-project-pass/plop/
            artifacts/runner-readiness-ten-project-pass/plop-native-runner.json
            artifacts/runner-readiness-ten-project-pass/toolchain/sdk.json''')
    # Each isolated step needs the same owned SDK and explicit target launcher.
    text=text.replace('        run: |\n','        run: |\n          export PATH="$GITHUB_WORKSPACE/artifacts/runner-readiness-ten-project-pass/toolchain/go/bin:$GITHUB_WORKSPACE/artifacts/runner-readiness-ten-project-pass/active/plop/bin:$PATH"\n')
    text='# Reviewed campaign derivative: owned prerequisites; manual event; bounded extra faults and teardown.\n'+text
    output.write_text(text,encoding='utf-8',newline='\n')
    immutable_json(original.parent/'free-workflow-derivation.json',dict(
        generated_sha256=sha256(original),reviewed_workflow_sha256=sha256(output),
        runner_source_revision='e5571bdd05a63448c875b8f1da1412e9810aac75',
        changes=['manual-only jobs; narrow push registers workflow without executing target',
                 'installed Python/Node; official Go SDK and all caches inside checkout',
                 'native reviewed profile selected before tests',
                 'same generated ordinary test/context/HTML/summary route',
                 'real source faults, selected maintenance, verified evidence restore and removal',
                 'two standard hosted jobs, max two concurrent, 25 minutes each'],
        status='prepared, not dispatched or qualified'))
    print('Reviewed generated-workflow derivative:',output)


if __name__=='__main__':main()
