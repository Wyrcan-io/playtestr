"""Owned native candidate and pinned Poetry acquisition/build/profile preparation."""
import asyncio
import argparse
import json
import os
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_poetry_profiles import main as profiles


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target-only',action='store_true');args=parser.parse_args()
    candidate=ROOT/'.playtestr-bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    if not args.target_only:
        binary=RAW/'bin'/candidate.name;binary.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(candidate,binary)
        if os.name!='nt':binary.chmod(0o755)
        immutable_json(RAW/'poetry-native-runner.json',dict(source_revision=os.environ['SOURCE_REVISION'],
            candidate_sha256=sha256(candidate),copied_sha256=sha256(binary)))
    immutable_json(RAW/'poetry-runtime-baseline.json',await runtime_inventory('poetry','runtime-baseline-before-acquisition'))
    for script,label,timeout in [('readiness_acquire_poetry.py','native-pinned-acquisition',180),
                                  ('readiness_build_poetry.py','native-owned-build',1200)]:
        await execute([sys.executable,'scripts/acceptance/'+script],'poetry',label,
                      timeout=timeout,campaign=Campaign())
    profiles()


if __name__=='__main__':asyncio.run(main())
