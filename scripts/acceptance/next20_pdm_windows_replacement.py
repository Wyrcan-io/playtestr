"""Declare a complete new Windows window after the retained startup experiment."""
import copy
import json

from next20_check import DOC, RAW
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'pdm';probe=RAW/'pdm/startup-probe-v1';observed=json.loads((probe/'summary.json').read_text())
    if observed['passed']!=50 or observed['failed'] or len(observed['observations'])!=50:raise ValueError('finite startup diagnostic did not pass')
    if observed['planned_sha256']!=sha256(probe/'planned.json'):raise ValueError('startup diagnostic declaration changed')
    selected=json.loads((probe/'spec.json').read_text())
    if selected['startup_timeout_ms']!=5000:raise ValueError('different measured startup contract')
    for row in observed['observations']:
        report=probe/(str(row['number'])+'.report.json');result=json.loads(report.read_text())['results'][0]
        if sha256(report)!=row['report_sha256'] or result['status']!='passed' or any(s['status']!='passed' for s in result['steps']) or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
            raise ValueError('nonpositive or unclean startup diagnostic')
    original=package/'final-series-declaration-native-exit-v1.json';value=copy.deepcopy(json.loads(original.read_text()))
    value.update(revision=2,replacement_window='v2',replacement_host='windows',
        original_declaration_sha256=sha256(original),original_rejected_window_sha256=sha256(package/'windows-first-final-rejection.json'),
        diagnostic_sha256=sha256(probe/'summary.json'),startup_timeout_ms_by_host={'windows':5000,'linux':2000},
        unchanged_linux_execution=dict(run='40869293414',source_revision='5ccd20b8ce38c3496ca5e5095819f1272dcf9e81',
            declaration_sha256=sha256(original),profile_sha256=sha256(package/'native-profile-v2.json'),status='execution-success-independent-full-cell-audit-pending'),
        startup_boundary='Windows final boundary uses an explicit5000ms first-output limit following50 positive diagnostic executions. The earlier2000ms startup refusal and unknown cause remain retained; no product default/deadline, target source, action or saved-state assertion changed. Linux retains its proven original2000ms contract.',
        scope='Fresh complete twelve-batch Windows replacement only, no failed-case retry or Linux rerun. Original227-report window remains rejected. Historical three-frame gap remains open; no project admission.',
        execution_budget=dict(windows_local_command_ceiling_seconds=1200,estimated_windows_minutes=18,
            linux_additional_jobs=0,automatic_harness_jobs_on_future_push=3,harness_job_ceiling_minutes=5,harness_max_parallel=2))
    immutable_json(package/'final-series-declaration-native-exit-v1-v2.json',value)
    print('Declared fresh240+9 Windows windowv2 at explicit5000ms startup; original227 attempts rejected; Linux execution unchanged; no admission.')


if __name__=='__main__':main()
