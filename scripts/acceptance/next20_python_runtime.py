"""Select an explicitly declared owned Python runtime, preserving old defaults."""
from pathlib import Path
import re


def python_runtime_root(target,runtime):
    name=runtime.get('runtime_directory','venv')
    if not isinstance(name,str) or not re.fullmatch(r'venv(?:-[a-z0-9][a-z0-9-]{0,31})?',name):raise ValueError('unsafe Python runtime directory')
    target=target.resolve(strict=True);root=target/name
    root.resolve(strict=True).relative_to(target)
    if root.is_symlink() or getattr(root,'is_junction',lambda:False)():raise ValueError('linked Python runtime directory')
    executable=Path(runtime['python']).resolve(strict=True);executable.relative_to(root.resolve(strict=True))
    return root
