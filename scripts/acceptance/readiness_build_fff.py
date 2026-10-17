"""Verify the reviewed interpreted target using installed native Bash; no install."""
import asyncio
import json
import os
from pathlib import Path
import platform
import re
import shutil

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256

PIN = '6f2dc6f3a003d24e8b3fd48b046241b486022ad5'


async def main():
    if platform.system() not in {'Linux', 'Darwin'}:
        raise RuntimeError('fff profile declares native Linux/macOS only')
    active = RAW/'active/fff'
    owner = json.loads((active/'task-owned.json').read_text())
    if owner != dict(workspace=str(ROOT), campaign='runner-readiness-ten-project-pass', project='dylanaraps/fff', pin=PIN):
        raise RuntimeError('unowned fff source')
    for path in [RAW, RAW/'active', active, active/'src']:
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise RuntimeError('redirected fff source')
    review = json.loads((ROOT/'docs/validation/runner-readiness-ten-project-pass/fff/source-review.json').read_text())
    if sha256(active/'source.tar.gz') != review['archive_sha256']:
        raise RuntimeError('canonical fff archive changed')
    if any(sha256(active/'src'/name) != digest for name, digest in review['reviewed_inputs'].items()):
        raise RuntimeError('reviewed interpreted source changed before initial setup')
    bash = Path('/bin/bash').resolve(strict=True)
    env = dict(PATH=str(bash.parent)+os.pathsep+'/usr/bin:/bin:/usr/sbin:/sbin', LANG='C', LC_ALL='C')
    for name, folder in [('HOME', 'home'), ('USERPROFILE', 'home'), ('TEMP', 'tmp'), ('TMP', 'tmp'),
                         ('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'home/cache'), ('XDG_CONFIG_HOME', 'home/config'),
                         ('XDG_DATA_HOME', 'home/data')]:
        path = active/folder
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    tools = {}
    for name in ['file', 'stty', 'mkdir', 'cp', 'mv', 'rm', 'chmod']:
        found = shutil.which(name, path=env['PATH'])
        if not found:
            raise RuntimeError('installed native prerequisite missing: '+name)
        path = Path(found).resolve(strict=True)
        tools[name] = dict(path=str(path), sha256=sha256(path))
    version = await execute([bash, '--noprofile', '--norc', '--version'], 'fff', 'installed-native-bash-version',
                            cwd=active, env=env, timeout=30, campaign=Campaign())
    parsed = re.search(r'version (\d+)\.(\d+)', version['output'])
    if parsed is None or tuple(map(int, parsed.groups())) < (3, 2):
        raise RuntimeError('installed Bash does not meet upstream 3.2 minimum')
    immutable_json(active/'runtime.json', dict(bash_path=str(bash), bash_sha256=sha256(bash),
                   version_attempt=version['id'], native_os=platform.system(), native_arch=platform.machine(),
                   installed_globally=False, tools=tools, startup_files_read=False))
    script = active/'src/fff'
    syntax = await execute([bash, '--noprofile', '--norc', '-n', script], 'fff', 'reviewed-bash-syntax-check',
                           cwd=active, env=env, timeout=30, campaign=Campaign())
    target = await execute([bash, '--noprofile', '--norc', script, '-v'], 'fff', 'interpreted-pinned-fff-version',
                           cwd=active, env=env, timeout=30, campaign=Campaign())
    if target['output'].strip() != 'fff 2.2':
        raise RuntimeError('unexpected pinned fff version')
    observed = usage(active)
    if observed > 24*1024**2:
        raise RuntimeError('fff source/runtime setup exceeded reviewed growth stop')
    immutable_json(active/'build.json', dict(pin=PIN, archive_sha256=review['archive_sha256'],
                   binary_relative_path='src/fff', binary_sha256=sha256(script), version=target['output'].strip(),
                   interpreter_sha256=sha256(bash), syntax_attempt=syntax['id'], version_attempt=target['id'],
                   active_bytes_observed=observed, build_kind='interpreted Bash source; no compilation or installation'))
    print('Verified reviewed fff syntax/version with installed native Bash and owned homes/temp; no installation.')


if __name__ == '__main__':
    asyncio.run(main())
