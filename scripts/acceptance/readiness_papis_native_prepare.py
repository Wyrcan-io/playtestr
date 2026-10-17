"""Prepare exact candidate and reviewed Papis solely inside a native checkout."""
import asyncio
import os
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    candidate=ROOT/'.playtestr-bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    binary=RAW/'bin'/candidate.name;binary.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(candidate,binary)
    if os.name!='nt':binary.chmod(0o755)
    immutable_json(RAW/'papis-native-runner.json',dict(source_revision=os.environ['SOURCE_REVISION'],
        candidate_sha256=sha256(candidate),copied_sha256=sha256(binary)))
    if os.name!='nt':
        immutable_json(RAW/'papis-runtime-baseline.json',await runtime_inventory('papis','runtime-baseline-before-acquisition'))
    for script,label,timeout in [('readiness_acquire_papis.py','native-pinned-source-acquisition',180),
            ('readiness_build_papis.py','native-owned-reviewed-build',1200)]:
        await execute([sys.executable,'scripts/acceptance/'+script],'papis',label,timeout=timeout,campaign=Campaign())
    # Each public journey sets the target PATH only in its child environment.
    # Keep workflow helpers on the installed bootstrap interpreter so the
    # additional owned-runtime observer cannot match a venv helper itself.


if __name__=='__main__':asyncio.run(main())
