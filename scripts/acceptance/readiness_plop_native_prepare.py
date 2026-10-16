"""Reviewed native Plop setup; all writes below the job's campaign root."""
import asyncio
import json
import os
from pathlib import Path
import shutil

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_plop_profiles import main as profiles
from readiness_cleanup_plop import node_inventory


async def main():
    campaign=Campaign()
    env=dict(os.environ)
    for name,folder in [('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('GOCACHE','go-cache'),
                        ('GOPATH','gopath'),('GOMODCACHE','gopath/pkg/mod')]:
        path=RAW/folder;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    async def run(argv,label,timeout=120):
        return await execute(argv,'plop',label,env=env,timeout=timeout,campaign=campaign)
    candidate=ROOT/'.playtestr-bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    if not candidate.is_file():raise RuntimeError('generated workflow source candidate is missing')
    binary=RAW/'bin'/candidate.name;binary.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(candidate,binary)
    if os.name!='nt':binary.chmod(0o755)
    immutable_json(RAW/'plop-native-runner.json',dict(source_revision=os.environ['SOURCE_REVISION'],
        candidate_sha256=sha256(candidate),copied_sha256=sha256(binary)))
    if os.name!='nt':
        immutable_json(RAW/'plop-node-baseline.json',await node_inventory('node-process-baseline-before-acquisition'))
    await run(['python3','scripts/acceptance/readiness_acquire_plop.py'],'native-reviewed-acquisition',timeout=120)
    node=shutil.which('node')
    if not node:raise RuntimeError('installed Node prerequisite unavailable; no global install permitted')
    version=await run([node,'--version'],'native-node-version')
    immutable_json(RAW/'active/plop/runtime.json',dict(executable=Path(node).name,
        sha256=sha256(Path(node).resolve()),version=version['output'].strip(),version_attempt=version['id'],
        requirement='pinned upstream Node >=18; exact actual native runtime recorded'))
    await run(['python3','scripts/acceptance/readiness_build_plop.py'],'native-reviewed-yarn-build',timeout=1200)
    profiles()
    print('Native Plop build and reviewed host contracts prepared; execution credit is pending.')


if __name__=='__main__':asyncio.run(main())
