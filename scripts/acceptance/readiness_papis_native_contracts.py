"""Copy reviewed public contracts, with only the declared native UTF-8 locale."""
import argparse
import asyncio
import json
import platform
import os
from pathlib import Path
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_papis_cases import environment


async def main():
    reviewed = ROOT/'docs/validation/runner-readiness-ten-project-pass/papis'
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    profile=reviewed/'native-profiles/windows' if os.name=='nt' else reviewed
    if platform.system() not in {'Linux','Windows'}:raise RuntimeError('undeclared native papis profile')
    freeze=json.loads((profile/'reviewed-contract-freeze.json').read_text(encoding='utf-8-sig'))
    if len(freeze['contracts'])!=20:raise RuntimeError('twenty frozen contracts required')
    canonical=profile/'contracts'
    for name,digest in freeze['all_package_inputs'].items():
        if sha256(canonical/name)!=digest:raise RuntimeError('reviewed native papis package changed')
    package=RAW/'papis/host-contracts';shutil.copytree(canonical,package)
    declaration=reviewed/'scenario-declaration-revision-3.json'
    declared=json.loads(declaration.read_text(encoding='utf-8-sig'))['host_profiles']['windows' if os.name=='nt' else 'linux']
    prepared_directories=[]
    for row in declared:
        for name in row['dirs']:
            directory=package/'fixtures'/row['id']/name
            directory.resolve().relative_to(package.resolve())
            directory.mkdir(parents=True,exist_ok=True)
            prepared_directories.append(directory.relative_to(package).as_posix())
    changes=[dict(contract=name,canonical_sha256=digest,native_sha256=sha256(package/name),
                  only_permitted_change='No changes; exact independently reviewed native profile') for name,digest in sorted(freeze['contracts'].items())]
    immutable_json(RAW/'papis/native-profile.json',dict(host=platform.system(),contracts=changes,
        profile=profile.relative_to(ROOT).as_posix(),freeze_sha256=sha256(profile/'reviewed-contract-freeze.json'),
        declared_empty_directories=prepared_directories,declaration_sha256=sha256(declaration),
        setup='Create only explicitly declared synthetic fixture directories absent from Git; frozen files, actions and outcomes unchanged.'))
    if args.prepare_only:
        print('Prepared the exact reviewed native papis contracts without a target invocation.')
        return
    root = RAW/'papis/suites'/uuid.uuid4().hex
    root.mkdir(parents=True)
    runner = RAW/('bin/playtestr.exe' if os.name=='nt' else 'bin/playtestr')
    selection = await execute([runner, 'test', '--list', package.relative_to(ROOT)], 'papis', 'native-public-twenty-list',
                              env=environment(), timeout=30, campaign=Campaign())
    selected = root/'selected.txt'
    selected.write_text(selection['output'], encoding='utf-8', newline='\n')
    report = root/'results.json'
    suite = await execute([sys.executable, 'scripts/acceptance/readiness_public_suite.py', '--project', 'papis',
                           '--selection', selected.relative_to(ROOT), '--', runner, 'test', '--report',
                           report.relative_to(ROOT), '--artifacts-dir', (root/'evidence').relative_to(ROOT),
                           package.relative_to(ROOT)], 'papis', 'native-frozen-twenty-suite-parent',
                          env=environment(), timeout=600, campaign=Campaign())
    outcome = json.loads(report.read_text(encoding='utf-8-sig'))
    if outcome['summary'] != dict(total=20, passed=20, failed=0, cancelled=0, not_run=0):
        raise RuntimeError('native frozen suite incomplete')
    for result in outcome['results']:
        if not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
            raise RuntimeError('native frozen suite cleanup unconfirmed')
        for step in result['steps']:
            if 'state' in step and (step['state']['invocation_id'] != result['invocation_id'] or
                                   step['state']['workspace_id'] != result['workspace']['id']):
                raise RuntimeError('native frozen suite has cross-execution state')
    immutable_json(root/'verified.json', dict(parent=suite['id'], report_sha256=sha256(report),
                   runner_sha256=sha256(runner), contracts=changes, phase='development', final_archive_credit=False))
    print('All twenty frozen public papis contracts pass reviewed native byte/screen assertions on this native host.')


if __name__ == '__main__':
    asyncio.run(main())
