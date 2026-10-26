"""Declare the complete native yo series before dispatch; no coverage claim."""
import json

from next20_check import DOC, ROOT, RAW
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'yo'
    if (package/'final-series-declaration.json').exists():raise ValueError('Preserve existing native declaration')
    revision=json.loads((package/'development-revision.json').read_text())
    original=json.loads((RAW/'yo/development-inputs-v1/preserved.json').read_text())
    first=RAW/original['first_series'];initial=json.loads(first.read_text())
    frozen=json.loads((package/'development-test-freeze.json').read_text())
    positive=ROOT/frozen['positive_development_summary']
    if json.loads(positive.read_text())['passed']!=20 or initial['passed']!=18 or initial['failed']!=2:
        raise ValueError('Complete original and positive replacement outcomes required')
    immutable_json(package/'first-development-disposition.json',dict(schema_version=1,passed=18,failed=2,
        ordinary_development_attempts=20,initial_series=first.parent.name,
        original_inputs='artifacts/runner-readiness-next-twenty-project-pass/yo/development-inputs-v1',
        original_input_index_sha256=sha256(RAW/'yo/development-inputs-v1/preserved.json'),
        revised_declaration_sha256=sha256(package/'scenarios.json'),changes=revision['changes'],
        complete_positive_replacement=frozen['positive_development_summary'],positive_summary_sha256=sha256(positive),
        sandbox_prelaunch_failure='20470f4fcb1746f3b1b2284468f264d4: native workspace expansion denied before target launch; no application or qualification credit.',
        failed_attempts_preserved=True,runner_repairs=0,final_ordinary_credit=0))
    template=json.loads((DOC/'cz-cli/final-series-declaration-v1.json').read_text())
    declaration={key:value for key,value in template.items() if key not in {'native_runtime_lock_sha256'}}
    declaration.update(project='yo',revision=1,canonical_test_freeze_sha256=sha256(package/'development-test-freeze.json'),
        framework_lock_sha256=sha256(package/'generator-package-lock.json'),retained_generations=dict(linux=1,windows=2),
        cold_scope='Two newly materialized verified complete app/framework module trees, each followed by warm reuse. Same exact owned Node executable; no OS-cache eviction claim.',
        original_first_development_failures='Original18pass/2fail and exact inputs/screens retained. Corrected two actual diagnostic text anchors only, then complete20pass replacement. All40 observations excluded from native repetitions. One separate sandbox-denied prelaunch attempt excluded.',
        transfer_scope='Normal workflows and three interpreted-source mutations already exposed locally; no untouched-source or human-transfer claim.',
        source_execution='Copied interpreted ESM modules, no compiler. Exact Node, canonical SRI packages and actual declared source-copy variants bound before launch.')
    declaration['dispatch_budget'].update(job_deadline_minutes=65,total_job_minute_ceiling=130,
        estimated_minutes=dict(linux=40,windows=35),cleanup='Explicit60000-file bound,128MiB/file,1GiB owned tree; Windows removal900s, native retention600s. Default40000 unchanged. Product deadlines unchanged.')
    for batch in declaration['batches']:
        if batch['id']<4:batch['runtime']=batch['runtime'].replace('app-pair','complete app/framework-pair')
    immutable_json(package/'final-series-declaration.json',declaration)
    source=ROOT/'.github/workflows/runner-readiness-next20-cz-cli.yml'
    destination=source.with_name('runner-readiness-next20-yo.yml')
    if destination.exists():raise ValueError('Preserve existing yo workflow')
    workflow=source.read_text().replace('cz-cli','yo').replace('next20_cz_cli_native.py','next20_yo_native.py').replace('timeout-minutes: 50','timeout-minutes: 65')
    workflow=workflow.replace('--label native-yo-source-retention --timeout 300','--label native-yo-source-retention --timeout 600')
    workflow=workflow.replace('--label native-yo-source-runtime-removal --timeout 300','--label native-yo-source-runtime-removal --timeout 600')
    workflow=workflow.replace('next20_target_cleanup.py --project yo','next20_target_cleanup.py --project yo --max-files 60000')
    workflow=workflow.replace('next20_remove_target.ps1 -Project yo','next20_remove_target.ps1 -Project yo -MaxFiles 60000')
    anchor='      - name: Windows target PID and birth proof\n'
    if workflow.count(anchor)!=1:raise ValueError('Original complete workflow boundary changed')
    step=('      - name: Preserve exact npm metadata compactly\n'
          "        if: always() && steps.prepare.outcome == 'success'\n"
          '        run: python -B scripts/acceptance/next20_check.py --label native-yo-cache-metadata-retention --timeout 120 -- python -B scripts/acceptance/next20_yo_cache_retention.py\n')
    workflow=workflow.replace(anchor,step+anchor)
    destination.write_text(workflow,encoding='utf-8',newline='\n')
    print('Declared complete yo native matrix and bounded standard-hosted workflow; no dispatch or compatibility credit.')


if __name__=='__main__':main()
