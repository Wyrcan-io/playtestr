"""Retain exact small compiled target modules under their actual content hashes."""
import hashlib

from next20_check import RAW,ROOT


def capture(app,compiled):
    destination=RAW/'cz-cli/compiled-payloads';destination.mkdir(parents=True,exist_ok=True)
    result={}
    for name,digest in compiled.items():
        path=app/name;path.resolve(strict=True).relative_to(app.resolve(strict=True))
        if path.is_symlink() or path.stat().st_size>4*1024**2:raise ValueError('Unsafe compiled target module')
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Actual compiled module changed')
        retained=destination/(digest+'.js')
        if retained.exists():
            if retained.read_bytes()!=data:raise ValueError('Compiled content identity collision')
        else:
            with retained.open('xb') as stream:stream.write(data)
        result[name]=retained.relative_to(ROOT).as_posix()
    return result
