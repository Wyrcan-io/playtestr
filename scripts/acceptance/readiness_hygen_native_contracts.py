"""Execute only the exact reviewed native public Hygen profile."""
import asyncio
from pathlib import Path
import platform
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import environment, runner
from readiness_new_control_matrix import read_json as load


async def main():
    profile = ROOT / 'docs/validation/runner-readiness-ten-project-pass/hygen'
    if platform.system() == 'Darwin':
        profile = profile / 'native-profiles/macos'
    elif platform.system() != 'Linux':
        raise RuntimeError('declared Linux/macOS native profiles only')
    frozen = load(profile / 'reviewed-contract-freeze.json')
    if len(frozen['contracts']) != 20:
        raise RuntimeError('twenty reviewed contracts required')
    for name, digest in frozen['all_package_inputs'].items():
        if sha256(profile / 'contracts' / name) != digest:
            raise RuntimeError('reviewed frozen input changed')
    package = RAW / 'hygen/host-contracts'
    shutil.copytree(profile / 'contracts', package)
    immutable_json(RAW / 'hygen/native-profile.json', dict(host=platform.system(),
                   freeze_sha256=sha256(profile / 'reviewed-contract-freeze.json'),
                   profile=profile.relative_to(ROOT).as_posix(), changes='None; exact reviewed native bytes.'))
    root = RAW / 'hygen/suites' / uuid.uuid4().hex
    root.mkdir(parents=True)
    binary, candidate, cell = runner()
    listing = await execute([binary, 'test', '--list', package.relative_to(ROOT)], 'hygen',
                            'native-reviewed-twenty-directory-list', env=environment(), timeout=30, campaign=Campaign())
    selection = root / 'selected.txt'
    selection.write_text(listing['output'], encoding='utf-8', newline='\n')
    report = root / 'results.json'
    suite = await execute([sys.executable, 'scripts/acceptance/readiness_public_suite.py', '--project', 'hygen',
        '--selection', selection.relative_to(ROOT), '--', binary, 'test', '--report', report.relative_to(ROOT),
        '--artifacts-dir', (root / 'evidence').relative_to(ROOT), package.relative_to(ROOT)],
        'hygen', 'native-reviewed-twenty-suite-parent', env=environment(), timeout=600, campaign=Campaign())
    outcome = load(report)
    if outcome['runner_version'] != candidate['version'] or outcome['summary'] != dict(total=20, passed=20, failed=0, cancelled=0, not_run=0):
        raise RuntimeError('native reviewed suite incomplete')
    for result in outcome['results']:
        if not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
            raise RuntimeError('native suite cleanup unconfirmed')
        for step in result['steps']:
            if 'state' in step and (step['state']['invocation_id'] != result['invocation_id']
                                  or step['state']['workspace_id'] != result['workspace']['id']):
                raise RuntimeError('cross-execution native state proof')
    immutable_json(root / 'verified.json', dict(parent=suite['id'], report_sha256=sha256(report),
                   runner_sha256=cell['binary_sha256'], provisional_archive_sha256=cell['archive_sha256'],
                   canonical_freeze_sha256=sha256(profile / 'reviewed-contract-freeze.json'), final_archive_credit=0))
    print('Exact reviewed twenty-case native Hygen suite passed on unchanged provisional archive bytes.')


if __name__ == '__main__':
    asyncio.run(main())
