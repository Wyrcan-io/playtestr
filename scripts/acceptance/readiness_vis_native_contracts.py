"""Copy reviewed public contracts, with only the declared native UTF-8 locale."""
import asyncio
import json
import platform
from pathlib import Path
import shutil
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_vis_cases import environment


async def main():
    reviewed = ROOT/'docs/validation/runner-readiness-ten-project-pass/vis'
    freeze = json.loads((reviewed/'reviewed-contract-freeze.json').read_text(encoding='utf-8-sig'))
    if len(freeze['contracts']) != 20:
        raise RuntimeError('twenty frozen public contracts required')
    canonical = reviewed/'contracts'
    for name, digest in freeze['all_package_inputs'].items():
        if sha256(canonical/name) != digest:
            raise RuntimeError('reviewed Vis input changed: '+name)
    package = RAW/'vis/host-contracts'
    shutil.copytree(canonical, package)
    changes = []
    for name in sorted(freeze['contracts']):
        path = package/name
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        if value['env'] != {'LC_ALL': 'C.UTF-8', 'TERM': 'xterm-256color'}:
            raise RuntimeError('unexpected canonical locale/environment')
        if platform.system() == 'Darwin':
            value['env']['LC_ALL'] = 'en_US.UTF-8'
            path.write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8', newline='\n')
        elif platform.system() != 'Linux':
            raise RuntimeError('undeclared Vis native host')
        changes.append(dict(contract=name, canonical_sha256=sha256(canonical/name), native_sha256=sha256(path),
                            only_permitted_change='LC_ALL C.UTF-8 to en_US.UTF-8 on macOS; no action, byte or screen changes'))
    immutable_json(RAW/'vis/native-profile.json', dict(host=platform.system(), contracts=changes,
                   freeze_sha256=sha256(reviewed/'reviewed-contract-freeze.json')))
    root = RAW/'vis/suites'/uuid.uuid4().hex
    root.mkdir(parents=True)
    runner = RAW/'bin/playtestr'
    selection = await execute([runner, 'test', '--list', package.relative_to(ROOT)], 'vis', 'native-public-twenty-list',
                              env=environment(), timeout=30, campaign=Campaign())
    selected = root/'selected.txt'
    selected.write_text(selection['output'], encoding='utf-8', newline='\n')
    report = root/'results.json'
    suite = await execute([sys.executable, 'scripts/acceptance/readiness_public_suite.py', '--project', 'vis',
                           '--selection', selected.relative_to(ROOT), '--', runner, 'test', '--report',
                           report.relative_to(ROOT), '--artifacts-dir', (root/'evidence').relative_to(ROOT),
                           package.relative_to(ROOT)], 'vis', 'native-frozen-twenty-suite-parent',
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
    print('All twenty frozen public Vis contracts pass unchanged byte/screen assertions on this native host.')


if __name__ == '__main__':
    asyncio.run(main())
