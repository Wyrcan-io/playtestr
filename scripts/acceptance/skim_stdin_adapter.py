"""Feed one bounded fixture to Skim while preserving the parent's real PTY."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    fixture = Path.cwd() / 'items.txt'
    if fixture.is_symlink() or not fixture.is_file() or fixture.stat().st_size > 64 * 1024:
        raise SystemExit('owned Skim fixture is missing, linked, or oversized')
    binary_text = os.environ.get('SKIM_TEST_BINARY')
    if not binary_text:
        raise SystemExit('SKIM_TEST_BINARY is required')
    binary = Path(binary_text).resolve(strict=True)
    if binary.name.lower() != 'sk.exe' or binary.stat().st_size > 128 * 1024 * 1024:
        raise SystemExit('unexpected owned Skim executable')
    env = {}
    for key in ('PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'TEMP', 'TMP', 'TERM'):
        if key in os.environ:
            env[key] = os.environ[key]
    process = subprocess.Popen([str(binary), *sys.argv[1:]], cwd=Path.cwd(), env=env,
        stdin=subprocess.PIPE, stdout=None, stderr=None, close_fds=True)
    payload = fixture.read_bytes()
    process.stdin.write(payload)
    process.stdin.close()
    return process.wait()


if __name__ == '__main__':
    raise SystemExit(main())
