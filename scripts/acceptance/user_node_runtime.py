#!/usr/bin/env python3
"""Build reviewed pinned JS sources with explicit task-local prerequisites."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['install', 'rebuild'])
parser.add_argument('application')
args = parser.parse_args()
app = ROOT / '.cache/ten-project-apps' / args.application
owner = json.loads((app / 'task-owned.json').read_text())
if owner['created_by'] != 'ten-project-user-pass':
    raise SystemExit('Unknown application ownership')
runtime = Path('/var/tmp') / ('playtestr-user-pass-' + args.application)
if json.loads((runtime / 'task-owned.json').read_text()) != dict(workspace=str(ROOT), application=args.application):
    raise SystemExit('Unknown native runtime ownership')
source = Path(json.loads((app / 'native-source.json').read_text())['path'])
source.resolve().relative_to(runtime.resolve())
doc = ROOT / 'docs/validation/ten-project-user-pass' / owner['project']
config = json.loads((doc / 'node-build.json').read_text())
node = ROOT / '.tools/ten-project-runtime/node-v24.7.0-linux-x64/bin/node'
env = dict(os.environ, PATH=str(node.parent) + os.pathsep + os.environ['PATH'],
           npm_config_cache=str(runtime / 'npm-cache'),
           npm_config_userconfig=str(runtime / 'empty.npmrc'),
           npm_config_globalconfig=str(runtime / 'empty-global.npmrc'),
           HOME=str(runtime / 'home'), PNPM_HOME=str(runtime / 'pnpm-home'), CI='true')
(runtime / 'home').mkdir(exist_ok=True)
(runtime / 'empty.npmrc').touch()
(runtime / 'empty-global.npmrc').touch()
raw = ROOT / 'artifacts/ten-project-user-pass' / owner['project']
raw.mkdir(parents=True, exist_ok=True)
start = time.monotonic()
with (raw / 'native-node-build.log').open('w') as log:
    for entry in config['commands']:
        if args.mode == 'rebuild' and entry.get('phase') != 'build':
            continue
        cwd = source / entry.get('cwd', '.')
        cwd.resolve().relative_to(source.resolve())
        remaining = 1200 - (time.monotonic() - start)
        if remaining <= 0:
            raise SystemExit('Twenty-minute project build deadline')
        log.write(json.dumps(entry) + '\n'); log.flush()
        subprocess.run(entry['argv'], cwd=cwd, env=env, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=remaining)
digest = hashlib.sha256()
files = 0
for item in sorted(source.rglob('*')):
    if not item.is_file() or item.is_symlink() or '.git' in item.parts:
        continue
    digest.update(str(item.relative_to(source)).encode()); digest.update(b'\0')
    with item.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    files += 1
identity = dict(source_sha=subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
                installed_tree_sha256=digest.hexdigest(), files=files,
                node_version=subprocess.check_output([str(node), '--version'], text=True).strip(),
                build_seconds=time.monotonic() - start, reviewed_commands=config['commands'])
(raw / 'installed-target-identity.json').write_text(json.dumps(identity, indent=2) + '\n')
print('Built actual pinned source with task-local Node prerequisites', args.application, flush=True)
