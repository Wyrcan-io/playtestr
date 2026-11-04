"""Capture one bounded native Linux PTY launch for Git Town diagnostics."""
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import struct
import subprocess
import termios
import time
import uuid

from next20_git_town_case import isolated_env
from next20_check import RAW
from readiness_evidence import immutable_json, sha256


def main():
    target = RAW / 'active' / 'git-town'
    binary = target / 'bin' / 'git-town'
    fixture = Path('docs/validation/runner-readiness-next-twenty-project-pass/git-town/fixtures/branch-repo').resolve(strict=True)
    run_id = uuid.uuid4().hex
    root = target / 'terminal-probe' / run_id
    repo = root / 'repo'
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(fixture, repo)
    env, _ = isolated_env(target)
    env['TERM'] = 'xterm-256color'
    argv = [str(binary), 'hack', '--no-sync', '--non-interactive', 'feat-probe']
    started = dict(schema_version=1, project='git-town', label='linux-native-pty-probe',
        argv=argv, cwd=str(repo), executable_sha256=sha256(binary),
        fixture_sha256=sha256(target / 'fixture-source.json'),
        launch_policy='owned synthetic fixture; 3 second PTY cap; process-group cleanup')
    immutable_json(root / 'started.json', started)

    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
    process = None
    output = bytearray()
    error = None
    timed_out = False
    try:
        process = subprocess.Popen(argv, cwd=repo, env=env, stdin=slave, stdout=slave,
            stderr=slave, start_new_session=True, close_fds=True)
        os.close(slave)
        slave = -1
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and process.poll() is None:
            readable, _, _ = select.select([master], [], [], 0.05)
            if readable:
                try:
                    block = os.read(master, 8192)
                except OSError:
                    break
                if block:
                    if len(output) + len(block) > 64 * 1024:
                        error = 'output cap exceeded'
                        break
                    output.extend(block)
        timed_out = process.poll() is None
    finally:
        if slave >= 0:
            os.close(slave)
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGINT)
                process.wait(timeout=1)
            except Exception:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=1)
        if process is not None:
            while True:
                readable, _, _ = select.select([master], [], [], 0)
                if not readable:
                    break
                try:
                    block = os.read(master, 8192)
                except OSError:
                    break
                if not block:
                    break
                if len(output) + len(block) > 64 * 1024:
                    error = 'output cap exceeded'
                    break
                output.extend(block)
        os.close(master)

    raw_path = root / 'pty-output.bin'
    raw_path.write_bytes(output)
    result = dict(started, status='timed-out' if timed_out else 'exited',
        target_exit=process.returncode if process else None, output_bytes=len(output),
        output_sha256=sha256(raw_path), output_relative_path=raw_path.relative_to(target).as_posix(),
        output_utf8=bytes(output).decode('utf-8', 'replace')[-4096:], error=error,
        workspace_exists=repo.exists(),
        repo_head=(subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, env=env,
            capture_output=True, timeout=10).stdout.decode().strip() if repo.exists() else None))
    immutable_json(root / 'finished.json', result)
    print(json.dumps(result, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
