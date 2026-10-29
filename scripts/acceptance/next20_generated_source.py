"""Verify separately declared backend-generated files without changing Git inputs."""
from pathlib import PurePosixPath


def restored_source_inventory(primary, generated):
    expected=dict(primary)
    for name,row in generated.items():
        path=PurePosixPath(name)
        if (not name or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or
                path.as_posix()!=name or name in expected):
            raise ValueError('generated file escapes or overlaps primary source')
        digest=row['sha256']
        if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('invalid generated file digest')
        expected[name]=digest
    return expected
