"""Apply explicitly reviewed viewport snapshots to an execution copy only."""
import hashlib
from pathlib import PurePosixPath


def apply(package, canonical, profiles, batch):
    selected = profiles.get(str(batch), {})
    if not isinstance(selected, dict) or len(selected) > 100:
        raise ValueError('reviewed batch snapshot count bound')
    changed = {}
    for name, rule in selected.items():
        def checked(root, relative):
            if not isinstance(relative, str):
                raise ValueError('unsafe batch snapshot path')
            value = PurePosixPath(relative)
            if '\\' in relative or ':' in relative or value.is_absolute() or value.parts[:1] != ('snapshots',) or any(p in {'', '.', '..'} for p in relative.split('/')):
                raise ValueError('unsafe batch snapshot path')
            path = root/relative
            path.resolve(strict=True).relative_to(root.resolve(strict=True))
            if any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)() for p in [path, *path.parents[:len(value.parts)-1]]):
                raise ValueError('linked batch snapshot path')
            return path
        destination = checked(package, name)
        source = checked(canonical, rule['reviewed_input'])
        before, replacement = destination.read_bytes(), source.read_bytes()
        digest = lambda body: hashlib.sha256(body).hexdigest()
        if len(replacement) > 1024**2 or digest(before) != rule['original_sha256'] or digest(replacement) != rule['reviewed_sha256']:
            raise ValueError('reviewed batch snapshot bytes differ')
        destination.write_bytes(replacement)
        changed[name] = dict(original_sha256=digest(before), reviewed_sha256=digest(replacement), reviewed_input=rule['reviewed_input'])
    return changed
