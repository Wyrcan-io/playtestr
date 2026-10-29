"""Prepare one bounded standard-hosted PDM Linux development preflight."""
import json

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'pdm';target=RAW/'active/pdm'
    review=json.loads((package/'source-review.json').read_text())
    compatibility=json.loads((package/'runtime-compatibility-v2.json').read_text())
    setup=json.loads((package/'setup-declaration.json').read_text())
    versions={r['name'].lower().replace('_','-'):r['version'] for r in review['dependencies']}
    versions.update(compatibility['runtime_constraints'])
    immutable_json(package/'native-runtime-lock.json',dict(schema_version=1,module='pdm',
        expected_version=setup['built_source_version'],version_args=['--version'],versions=versions,
        reviewed_linux_additions=[],source_review_sha256=sha256(package/'source-review.json'),
        compatibility_sha256=sha256(package/'runtime-compatibility-v2.json'),
        additional_reviewed_wheels_sha256=sha256(RAW/'pdm/runtime-revision/v2/reviewed-wheels.json'),
        common_wheels_sha256=sha256(target/'wheels.json'),explicit_python_wizard_profile=True,
        build_environment={'PDM_BUILD_SCM_VERSION':setup['built_source_version']},
        generated_source_files=['.pdm-build/.gitignore','.pdm-build/_editable_impl_pdm.pth','src/pdm/VERSION'],
        native_profile='Bind both interpreter fields; Linux EOF CtrlD and cancel130; /dev/null Git config; convert only explicitly declared generated-text state expectations from CRLF to LF. Preserved fixtures and README remain exact. Python3.12 required; no snapshot normalization.',
        scope='Exact reviewed versions, independent primary-release digest check for every actual native wheel; no automatic startup hooks or unreviewed scripts.'))
    immutable_json(package/'linux-preflight-declaration.json',dict(schema_version=1,candidate='v0.4.0-rc.6',
        candidate_series='native-exit-v1',host='ubuntu-24.04',development_cases=20,
        native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),project_admissions=0,
        historical_screen_gap_open=True,qualification_credit=0,
        budget=dict(standard_hosted=True,target_jobs=1,max_parallel=1,job_ceiling_minutes=30,
            estimated_target_minutes=6,automatic_harness_jobs=3,harness_job_ceiling_minutes=5,harness_max_parallel=2),
        scope='Development cross-platform diagnosis only. No final repetitions, admission or missing historical-screen replacement.'))
    workflow=(ROOT/'.github/workflows/runner-readiness-next20-cargo-linux-preflight.yml').read_text()
    workflow=workflow.replace('cargo-generate','pdm').replace('cargo-linux','pdm-linux')
    start=workflow.index('      - name: Acquire,');end=workflow.index('      - name: Execute all twenty',start)
    workflow=workflow[:start]+'''      - name: Prepare reviewed pinned Python target within twenty minutes
        id: prepare
        run: python -B scripts/acceptance/next20_check.py --label pdm-linux-bounded-native-preparation --timeout 1200 -- python -B scripts/acceptance/next20_jrnl_native_prepare.py --project pdm
'''+workflow[end:]
    start=workflow.index('      - uses: actions/upload-artifact')
    workflow=workflow[:start]+'''      - name: Retain verified sources and dependencies and confirm native cleanup
        if: always() && steps.prepare.outcome == 'success'
        run: python -B scripts/acceptance/next20_check.py --label pdm-linux-source-runtime-removal --timeout 180 -- python -B scripts/acceptance/next20_target_cleanup.py --project pdm --generated-source-manifest artifacts/runner-readiness-next-twenty-project-pass/pdm/native-generated-source.json
'''+workflow[start:]
    path=ROOT/'.github/workflows/runner-readiness-next20-pdm-linux-preflight.yml'
    with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(workflow)
    print('Declared one bounded Linux development job; no dispatch/admission.')


if __name__=='__main__':main()
