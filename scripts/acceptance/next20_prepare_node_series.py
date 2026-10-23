"""Declare and register the third project's actual compiled Node native series."""
import copy
import json

from next20_check import ROOT,DOC
from readiness_evidence import immutable_json,sha256


def main():
    project='cz-cli';package=DOC/project
    lock=dict(schema_version=1,kind='compiled-node',source_review_sha256=sha256(package/'source-review.json'),
        canonical_source_sha256=sha256(package/'source-provenance.json'),
        build_lock_derivation_sha256=sha256(package/'build-lock-derivation.json'),
        node_requirement='Read-only installed Node >=18, exact owned copy and actual version/hash recorded per host; no global SDK installation.',
        runtime='Canonical upstream production lock with hooks/bin-links disabled; exact189-package closure.',
        compiler='Exact200-package Babel closure from upstream lock; unchanged Babel configuration and explicit compiler invocation only.',
        native_profile='Relative owned Node executable and actual app entry routing; Linux /usr/bin:/bin Git PATH, /dev/null global Git config, no inherited Windows environment names. Windows interruption1; planned verified-by-execution Unix self-SIGINT130. All other actions, file/fixture bytes and snapshot unchanged.')
    immutable_json(package/'native-runtime-lock.json',lock)
    previous=json.loads((DOC/'jrnl/final-series-declaration.json').read_text(encoding='utf-8'))
    batches=copy.deepcopy(previous['batches'])
    for row in batches[:4]:row['runtime']=row['runtime'].replace('venv-pair','app-pair')+'; exact owned Node interpreter reused'
    declaration=dict(schema_version=1,project=project,revision=1,hosts=['linux','windows'],runtime_kind='node',
        canonical_test_freeze_sha256=sha256(package/'development-test-freeze.json'),
        native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),candidate=previous['candidate'],batches=batches,
        scenarios_per_cell=20,normal=8,edge=12,repetitions_per_cell=12,ordinary_required=480,
        real_source_faults=3,required_three_phase_calibrations=18,additional_terminal_only_calibrations=2,calibration_required=20,
        original_first_development_failures='First17pass/3fail preserved; two observed Windows interruption codes and one intact wrapped-label anchor corrected. Complete replacement20passed. All40 development observations excluded from final repetition credit.',
        authoring='Public first3invocations/20controls; separate fix+snapshot technical3/22. Prepared familiar operator, no human beginner measurement.',
        transfer_scope='Source and three compiled mutations already exposed locally; not untouched-source/human transfer.',
        cold_scope='Two newly materialized hash-verified app/module/compiled-code copies, each followed by a warm reuse. Same exact owned Node executable; no OS-cache eviction claim.',
        failure_policy=previous['failure_policy'],
        dispatch_budget=dict(standard_jobs=2,max_simultaneous_target_jobs=2,job_deadline_minutes=50,
            total_job_minute_ceiling=100,estimated_minutes=dict(linux=30,windows=20),
            build_deadline_seconds=1200,scenario_deadline_seconds=120,step_deadline_seconds=10,
            cleanup='Native Windows full inventory/removal helper capped900s; Unix retention/removal300s. Product deadlines unchanged.'),new_project_admissions=0)
    immutable_json(package/'final-series-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-next20-commitizen-python.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('next20_native_python.py commitizen-python','next20_cz_cli_native.py')
    workflow=workflow.replace('commitizen-python',project).replace('timeout-minutes: 40','timeout-minutes: 50')
    workflow=workflow.replace('--label native-cz-cli-source-retention --timeout 180','--label native-cz-cli-source-retention --timeout 300')
    workflow=workflow.replace('--label native-cz-cli-source-runtime-removal --timeout 180','--label native-cz-cli-source-runtime-removal --timeout 900')
    workflow=workflow.replace('--label native-cz-cli-source-runtime-removal --timeout 240','--label native-cz-cli-source-runtime-removal --timeout 900')
    workflow=workflow.replace('--timeout 900 -- python -B scripts/acceptance/next20_target_cleanup.py --project cz-cli','--timeout 300 -- python -B scripts/acceptance/next20_target_cleanup.py --project cz-cli')
    output=ROOT/'.github/workflows/runner-readiness-next20-cz-cli.yml'
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(workflow)
    print('Declared actual Node two-host twelve-repeat series:480 ordinary,18 mandatory calibrations,2 separate probes. No dispatch or execution credit.')


if __name__=='__main__':main()
