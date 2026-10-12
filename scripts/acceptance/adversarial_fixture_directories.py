"""Restore declared empty synthetic fixture directories omitted by Git checkouts."""
import json
from pathlib import Path, PurePosixPath


def prepare(package):
    manifest=package/'fixture-directories.json'
    if not manifest.exists():
        return
    if manifest.stat().st_size>65536:
        raise RuntimeError('Fixture directory declaration size bound')
    config=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
    roots={case.get('fixture',config.get('fixture','fixtures')) for case in config['cases']}
    values=json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(values,list) or len(values)>1000 or any(not isinstance(v,str) for v in values) or len(set(values))!=len(values):
        raise RuntimeError('Invalid fixture directory declaration')
    admitted=[]
    for value in values:
        if not isinstance(value,str) or '\\' in value or ':' in value or '\0' in value:
            raise RuntimeError('Unsafe fixture directory name')
        relative=PurePosixPath(value)
        if relative.is_absolute() or '..' in relative.parts or relative.as_posix()!=value:
            raise RuntimeError('Unsafe fixture directory path')
        if len(relative.parts)>16 or any(len(part)>240 for part in relative.parts):
            raise RuntimeError('Fixture directory depth/name bound')
        if not any(relative.is_relative_to(PurePosixPath(root)) and relative!=PurePosixPath(root) for root in roots):
            raise RuntimeError('Directory is outside the declared fixture roots')
        path=package.joinpath(*relative.parts)
        for parent in [path,*path.parents]:
            if parent==package.parent:
                break
            if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():
                raise RuntimeError('Refuse linked fixture directory')
        path.resolve().relative_to(package.resolve())
        if path.exists() and (not path.is_dir() or any(path.iterdir())):
            raise RuntimeError('Declared empty fixture directory is not empty')
        admitted.append(path)
    # Validate every path before creating any, so a rejected manifest has no
    # partial directory side effects. Existing fixture file bytes are untouched.
    for path in admitted:
        path.mkdir(parents=True,exist_ok=True)
