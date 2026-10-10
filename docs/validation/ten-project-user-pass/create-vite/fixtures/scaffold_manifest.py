"""Independent, bounded manifest of actual generated files, before teardown."""
import hashlib, json, sys
from pathlib import Path

root = Path(sys.argv[1])
if root.is_absolute() or '..' in root.parts or root.is_symlink():
    raise SystemExit('Expected owned relative scaffold directory')
files = sorted(root.rglob('*'))
if len(files) > 64:
    raise SystemExit('Unexpected scaffold file count')
manifest = {}
for item in files:
    if item.is_symlink():
        raise SystemExit('Unexpected scaffold link')
    if item.is_file():
        if item.stat().st_size > 1024 * 1024:
            raise SystemExit('Unexpected scaffold file size')
        manifest[str(item.relative_to(root))] = hashlib.sha256(item.read_bytes()).hexdigest()
print(json.dumps(manifest, sort_keys=True))
