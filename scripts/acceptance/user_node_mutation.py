#!/usr/bin/env python3
"""Apply a reviewed upstream source mutation and rebuild the actual JS target."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('mode', choices=['apply', 'restore'])
p.add_argument('slug')
p.add_argument('name', nargs='?', default='target-regression')
a = p.parse_args()
doc = ROOT / 'docs/validation/ten-project-user-pass' / a.slug
m = json.loads((doc / (a.name + '.json')).read_text())
app = ROOT / '.cache/ten-project-apps' / m['application']
owner = json.loads((app / 'task-owned.json').read_text())
if owner['created_by'] != 'ten-project-user-pass' or owner['project'] != a.slug:
    raise SystemExit('Unknown application ownership')
runtime = Path('/var/tmp') / ('playtestr-user-pass-' + m['application'])
if json.loads((runtime / 'task-owned.json').read_text()) != dict(workspace=str(ROOT), application=m['application']):
    raise SystemExit('Unknown runtime ownership')
source = Path(json.loads((app / 'native-source.json').read_text())['path'])
source.resolve().relative_to(runtime.resolve())
file = source / m['file']
file.resolve().relative_to(source.resolve())
backup = app / (a.name + '.original')
if a.mode == 'apply':
    original = file.read_text()
    if original.count(m['before']) != 1:
        raise SystemExit('Source mutation anchor must match exactly once')
    backup.write_text(original)
    file.write_text(original.replace(m['before'], m['after']))
    (doc / (a.name + '.patch')).write_bytes(subprocess.check_output(['git', '-C', str(source), 'diff', '--', m['file']]))
else:
    file.write_text(backup.read_text())
subprocess.run([sys.executable, str(ROOT / 'scripts/acceptance/user_node_runtime.py'), 'rebuild', m['application']], check=True, timeout=1200)
compiled = source / m['compiled_file']
compiled.resolve().relative_to(source.resolve())
path = ROOT / 'artifacts/ten-project-user-pass' / a.slug / 'mutation-identities.json'
entries = json.loads(path.read_text()) if path.exists() else []
entries.append(dict(mutation=a.name, mode=a.mode, source_file_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                    compiled_file_sha256=hashlib.sha256(compiled.read_bytes()).hexdigest(),
                    installed_identity=json.loads((path.parent / 'installed-target-identity.json').read_text())))
path.write_text(json.dumps(entries, indent=2) + '\n')
print(a.slug, a.name, a.mode, 'actual source rebuilt', flush=True)
