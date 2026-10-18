"""Relocate reviewed public exports, run the full directory suite, then freeze."""
import asyncio
import copy
import json
import platform
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_cases import plan_hash, rows
from readiness_hygen_first_use import environment, runner
from readiness_new_control_matrix import read_json as load


async def main():
    package = RAW / 'hygen/contracts'
    package.mkdir(exist_ok=False)
    (package / 'snapshots').mkdir()
    approvals = []
    for row in rows():
        approval_path = RAW / 'hygen/approved' / (row['id'] + '.json')
        approval = load(approval_path)
        if approval['plan_sha256'] != plan_hash(row):
            raise RuntimeError('approved plan changed')
        source = ROOT / approval['spec']
        if sha256(source) != approval['spec_sha256']:
            raise RuntimeError('approved export changed')
        contract = load(source)
        original_steps = copy.deepcopy(contract['steps'])
        fixture = 'fixtures/' + row['id']
        shutil.copytree(source.parent / 'fixture', package / fixture)
        contract['workspace']['fixture'] = fixture
        contract['name'] = 'Hygen ' + row['id'] + ': ' + row['title']
        # Only reference names move; every actual action and expected payload stays exact.
        renamed = {}
        for step in contract['steps']:
            if 'snapshot' in step:
                name = step['snapshot']
                if name != 'prompt.rows.json':
                    raise RuntimeError('unexpected reviewed snapshot reference')
                destination = row['id'] + '-' + name
                shutil.copyfile(source.parent / 'snapshots' / name, package / 'snapshots' / destination)
                renamed[destination] = name
                step['snapshot'] = destination
        comparable = copy.deepcopy(contract['steps'])
        for step in comparable:
            if 'snapshot' in step:
                step['snapshot'] = renamed[step['snapshot']]
        if comparable != original_steps:
            raise RuntimeError('relocation changed an approved public action or expectation')
        path = package / (row['id'] + '.json')
        path.write_text(json.dumps(contract, indent=2, ensure_ascii=True) + '\n', encoding='utf-8', newline='\n')
        approvals.append(dict(id=row['id'], approval_sha256=sha256(approval_path), plan_sha256=plan_hash(row),
                              exported_spec_sha256=sha256(source), contract_sha256=sha256(path),
                              reference_relocation=renamed))
    binary, frozen, cell = runner()
    root = RAW / 'hygen/suites' / uuid.uuid4().hex
    root.mkdir(parents=True)
    listing = await execute([binary, 'test', '--list', package.relative_to(ROOT)], 'hygen',
                            'public-twenty-directory-list', env=environment(), timeout=30, campaign=Campaign())
    selection = root / 'selected.txt'
    selection.write_text(listing['output'], encoding='utf-8', newline='\n')
    report = root / 'results.json'
    suite = await execute([sys.executable, 'scripts/acceptance/readiness_public_suite.py', '--project', 'hygen',
        '--selection', selection.relative_to(ROOT), '--', binary, 'test', '--report', report.relative_to(ROOT),
        '--artifacts-dir', (root / 'evidence').relative_to(ROOT), package.relative_to(ROOT)],
        'hygen', 'full-public-twenty-contract-suite-parent', env=environment(), timeout=600, campaign=Campaign())
    outcomes = load(report)
    if (outcomes['runner_version'] != frozen['version'] or outcomes['summary'] !=
            dict(total=20, passed=20, failed=0, cancelled=0, not_run=0)):
        raise RuntimeError('full exact-archive ordinary suite incomplete')
    for result in outcomes['results']:
        if not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
            raise RuntimeError('suite cleanup unconfirmed')
        for step in result['steps']:
            if 'state' in step and (step['state']['invocation_id'] != result['invocation_id']
                                  or step['state']['workspace_id'] != result['workspace']['id']):
                raise RuntimeError('cross-execution state proof')
    files = {p.relative_to(package).as_posix(): sha256(p) for p in package.rglob('*') if p.is_file()}
    immutable_json(RAW / 'hygen/reviewed-contract-freeze.json', dict(schema_version=1,
        host=platform.system(), architecture=cell['architecture'], normal_scenarios=8, edge_scenarios=12,
        contracts={row['id'] + '.json': row['contract_sha256'] for row in approvals},
        all_package_inputs=files, approvals=approvals, ordinary_parent=suite['id'], ordinary_report_sha256=sha256(report),
        runner_sha256=cell['binary_sha256'], provisional_archive_sha256=cell['archive_sha256'],
        source_revision=frozen['source_revision'], target_build_sha256=sha256(RAW / 'active/hygen/build.json'),
        fault_selection='No source fault selected before this complete twenty-case freeze.', final_archive_credit=0))
    print('Twenty public Hygen exports pass the ordinary exact-archive directory suite; frozen before fault selection.')


if __name__ == '__main__':
    asyncio.run(main())
