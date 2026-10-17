"""Run the exact selected twenty-case package via the ordinary directory CLI."""
import asyncio
import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_rubygems_cases import environment
from readiness_rubygems_profiles import main as profiles


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runner',type=Path);args=parser.parse_args()
    suite=RAW/'rubygems/host-contracts'
    if not suite.exists():profiles()
    root=RAW/'rubygems/local-suite'/uuid.uuid4().hex;root.mkdir(parents=True)
    runner=args.runner.resolve() if args.runner else RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    runner.relative_to(ROOT)
    selected=await execute([runner,'test','--list',suite.relative_to(ROOT)],'rubygems','public-directory-list',
        env=environment(),timeout=30,campaign=Campaign())
    selection=root/'selected.txt';selection.write_text(selected['output'],encoding='utf-8',newline='\n')
    report=root/'results.json'
    ordinary=await execute([sys.executable,'scripts/acceptance/readiness_public_suite.py','--project','rubygems',
        '--selection',selection.relative_to(ROOT),'--',runner,'test','--artifacts-dir',(root/'evidence').relative_to(ROOT),
        '--report',report.relative_to(ROOT),suite.relative_to(ROOT)],'rubygems','local-public-directory-suite-parent',
        env=environment(),timeout=600,campaign=Campaign())
    results=json.loads(report.read_text())['results']
    assert len(results)==20 and all(r['status']=='passed' and r['cleanup']['confirmed_exited'] and r['workspace']['cleaned'] for r in results)
    immutable_json(root/'receipt.json',dict(list_attempt=selected['id'],ordinary_parent=ordinary['id'],
        report_sha256=sha256(report),selection_sha256=sha256(selection),scenarios_passed=20,
        qualification='development only; no archive qualification'))
    print('All twenty ordinary selected Bundler scenarios passed:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
