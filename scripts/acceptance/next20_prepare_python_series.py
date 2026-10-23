"""Declare and register a second real Python project's shared native protocol."""
import argparse
import hashlib
import json
import re
import zipfile
from email.parser import BytesParser

from next20_check import RAW, ROOT, DOC
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args();project=args.project
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',project):raise ValueError('unsafe project slug')
    package=DOC/project;target=RAW/'active'/project
    setup=json.loads((package/'setup-declaration.json').read_text());versions={}
    for path in (target/'dependency-review').glob('*.metadata.txt'):
        meta=BytesParser().parsebytes(path.read_bytes());versions[meta['Name'].lower().replace('_','-')]=meta['Version']
    scripts=json.loads((target/'wheel-script-approval.json').read_text())
    if len(scripts)!=1:raise ValueError('declared reviewed backend script required')
    backend=next(iter(scripts.values()))
    lock=dict(schema_version=1,versions=versions,reviewed_linux_additions=[],module=setup['module'],
        expected_version='4.19.2',version_args=['version','--commitizen'],
        backend_script=dict(distribution='uv-build',name='uv-build',shim_file='uv_build/__init__.py',shim_sha256=backend['shim_sha256']),
        native_profile='Exact copied Python path; Linux uses /usr/bin:/bin and /dev/null for explicit Git prerequisites. Windows keeps declared Git/system PATH. All commands, inputs, Git seed bytes, assertions, saved-file bytes and reviewed screen unchanged.',
        common_wheels_sha256=sha256(target/'wheels.json'),source_review_sha256=sha256(package/'source-review.json'),
        scope='Pinned reviewed dependency versions; each native wheel must match primary release digest before offline install. Backend script/shim is explicit, not an automatic startup hook.')
    immutable_json(package/'native-runtime-lock.json',lock)
    first=json.loads((DOC/'jrnl/final-series-declaration.json').read_text())
    declaration=dict(schema_version=1,project=project,revision=1,hosts=['linux','windows'],
        canonical_test_freeze_sha256=sha256(package/'development-test-freeze.json'),
        native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),candidate=first['candidate'],batches=first['batches'],
        scenarios_per_cell=20,normal=8,edge=12,repetitions_per_cell=12,ordinary_required=480,
        real_source_faults=3,required_three_phase_calibrations=18,additional_terminal_only_calibrations=2,calibration_required=20,
        original_first_development_failures='18 passed / two failed at initial width40 readiness anchor. Original reports/screens/specs retained; distinct replacement passed all20. Both development series excluded from final repetition credit.',
        authoring='Original local three/twenty route preserved with unnecessary personal venv PATH; separately remeasured portable three/twenty route selected. Plain-name TOML snapshot route is separate technical work (three/twenty-two), not first-use credit.',
        transfer_scope='Source and all three mutations already exposed locally; no untouched native/human claim.',
        cold_scope=first['cold_scope'],failure_policy=first['failure_policy'],dispatch_budget=first['dispatch_budget'],new_project_admissions=0)
    declaration['dispatch_budget']['estimated_minutes']={'linux':8,'windows':15}
    immutable_json(package/'final-series-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-next20-jrnl.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('next20_jrnl_native_prepare.py','next20_native_python.py '+project)
    workflow=workflow.replace('next20_jrnl_final.py --batch','next20_final.py '+project+' --batch')
    workflow=workflow.replace('next20_jrnl_faults.py --package','next20_python_faults.py '+project+' --package')
    workflow=workflow.replace('jrnl',project)
    path=ROOT/'.github/workflows'/('runner-readiness-next20-'+project+'.yml')
    with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(workflow)
    print('Prepared shared two-host twelve-batch Python series:',project,'480 ordinary /20 separate calibration observations. No execution credit.')


if __name__=='__main__':main()
