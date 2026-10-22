"""Declare exact-archive public control reexecutions and three native jobs."""
import hashlib

from readiness_archive_controls import cases, definition_sha256
from readiness_evidence import ROOT, immutable_json, sha256


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    rows=[dict(id=c['id'],definition_sha256=definition_sha256(c),category=c['category'],mode=c['mode'],
        fixture_bytes=sum(map(len,c['files'].values())),fixture_files=len(c['files']),state_steps=len(c['states'])) for c in cases()]
    immutable_json(docs/'archive-control-declaration.json',dict(cases=rows,recorder_controls=['recorder-rejected-capture','recorder-input-only'],
        public_control_reexecutions_per_host=len(rows)+2,hosts=['linux-amd64','darwin-arm64','windows-amd64'],
        candidate_freeze_sha256=sha256(docs/'migration-candidate-freeze.json'),
        fixture_source_lf_sha256=hashlib.sha256((ROOT/'cmd/fixture/main.go').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
        source_comparison='Only source-code checkout CRLF/LF comparison uses canonical LF. Actual source/compiler/fixture binary bytes are independently hashed natively; every contract, fixture and state expectation retains exact bytes.',
        policy='Install exact frozen rc.5; build only the existing trusted synthetic target. Run after the bounded original-context FFF E11 application investigation. At most two native jobs and one public invocation per host. Keep unit/race-only and harness controls separate; no new unique-control/project/fault/repetition credit.',
        resource_bounds=dict(scenario_seconds=15,hang_step_seconds=1,outer_per_command_seconds=30,fixture_build_seconds=180,
            native_job_minutes=20,native_jobs=3,max_concurrent_native_jobs=2,artifact_retention_days=14),
        scope='Public archive reexecutions: same-execution exact bytes/types/directories/entry sets, exact and exceeded file/aggregate/entry/step bounds, prelaunch validation, supported/nonzero exits, flood/deadlines/descendant termination, rendered alternate Unicode, controlled resize, recorder rejected-capture/input-only false-green refusal. Existing source-only internal fault injection and harness controls remain source-level evidence.'))
    workflow=(ROOT/'.github/workflows/runner-readiness-final-papis.yml').read_text(encoding='utf-8')
    start=workflow.index('      - name: Prepare pinned local bibliography')
    end=workflow.index('      - uses: actions/upload-artifact',start)
    workflow=workflow[:start]+'''      - name: Prepare owned compiler only for synthetic target
        run: python scripts/acceptance/readiness_check.py --label archive-controls-owned-sdk --timeout 360 -- python scripts/acceptance/readiness_bootstrap_go.py
      - name: Reexecute public controls through the exact installed archive
        run: python scripts/acceptance/readiness_check.py --label archive-controls-public-native --timeout 600 -- python scripts/acceptance/readiness_archive_controls.py
'''+workflow[end:]
    workflow=workflow.replace('Runner readiness final Papis archive matrix','Runner readiness exact archive public controls')
    workflow=workflow.replace('runner-readiness-final-papis.yml','runner-readiness-archive-controls.yml')
    workflow=workflow.replace('playtestr-final-papis','playtestr-archive-controls')
    workflow=workflow.replace('  READINESS_IDENTITY_CATALOG_PROJECT: papis\n','')
    workflow=workflow.replace('timeout-minutes: 45','timeout-minutes: 20')
    marker='          - os: windows-2025'
    workflow=workflow.replace(marker,'''          - os: macos-15
            target: darwin-arm64
            archive_target: darwin_arm64
            extension: tar.gz
'''+marker)
    workflow=workflow.replace('final-papis-','archive-controls-')
    workflow=workflow.replace('            artifacts/runner-readiness-ten-project-pass/papis/\n',
        '            artifacts/runner-readiness-ten-project-pass/product-controls/\n')
    workflow=workflow.replace('            artifacts/runner-readiness-ten-project-pass/papis-runtime-baseline.json\n','')
    workflow=workflow.replace('            !artifacts/runner-readiness-ten-project-pass/papis/retained-source/source.tar.gz\n',
        '            artifacts/runner-readiness-ten-project-pass/toolchain/sdk.json\n')
    (ROOT/'.github/workflows/runner-readiness-archive-controls.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Declared public exact-archive control reexecutions per host:',len(rows)+2,'; no execution credit.')


if __name__=='__main__':main()
