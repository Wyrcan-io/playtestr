"""Compare Git Town startup with a real controlling terminal on native Linux."""
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


def wait_nonblocking(pid):
    finished, status = os.waitpid(pid, os.WNOHANG)
    return os.waitstatus_to_exitcode(status) if finished else None


def process_group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def main():
    target = RAW / 'active' / 'git-town'
    binary = target / 'bin' / 'git-town'
    fixture = Path('docs/validation/runner-readiness-next-twenty-project-pass/git-town/fixtures/branch-repo').resolve(strict=True)
    run_id = uuid.uuid4().hex
    root = target / 'controlling-tty-probe' / run_id
    repo = root / 'repo'
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(fixture, repo)
    env, _ = isolated_env(target)
    env['TERM'] = 'xterm-256color'
    argv = [str(binary), 'hack', '--no-sync', '--non-interactive', 'feat-controlling-tty']
    started = dict(schema_version=1, project='git-town', label='linux-native-controlling-tty-probe',
        argv=argv, cwd=str(repo), executable_sha256=sha256(binary),
        fixture_sha256=sha256(target / 'fixture-source.json'),
        launch_policy='owned synthetic fixture; pty.fork controlling terminal; 3 second cap; process-group cleanup')
    immutable_json(root / 'started.json', started)

    pid, master = pty.fork()
    if pid == 0:
        try:
            os.chdir(repo)
            os.execve(argv[0], argv, env)
        except BaseException:
            os._exit(127)

    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
    output = bytearray()
    exit_code = None
    timed_out = False
    output_error = None
    deadline = time.monotonic() + 3
    try:
        while time.monotonic() < deadline:
            exit_code = wait_nonblocking(pid)
            if exit_code is not None:
                break
            readable, _, _ = select.select([master], [], [], 0.05)
            if readable:
                try:
                    block = os.read(master, 8192)
                except OSError:
                    break
                if block:
                    if len(output) + len(block) > 64 * 1024:
                        output_error = 'output cap exceeded'
                        break
                    output.extend(block)
        if exit_code is None:
            timed_out = True
    finally:
        if timed_out or exit_code is None:
            try:
                os.killpg(pid, signal.SIGINT)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 0.5
            while exit_code is None and time.monotonic() < deadline:
                exit_code = wait_nonblocking(pid)
                if exit_code is None:
                    time.sleep(0.02)
            if exit_code is None:
                try:
                    os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                _, status = os.waitpid(pid, 0)
                exit_code = os.waitstatus_to_exitcode(status)
        drain_deadline = time.monotonic() + 0.25
        while time.monotonic() < drain_deadline:
            readable, _, _ = select.select([master], [], [], 0.02)
            if not readable:
                break
            try:
                block = os.read(master, 8192)
            except OSError:
                break
            if not block:
                break
            if len(output) + len(block) > 64 * 1024:
                output_error = 'output cap exceeded'
                break
            output.extend(block)
        os.close(master)

    if process_group_exists(pid):
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + 0.5
        while process_group_exists(pid) and time.monotonic() < deadline:
            time.sleep(0.02)
        if process_group_exists(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 0.5
            while process_group_exists(pid) and time.monotonic() < deadline:
                time.sleep(0.02)
    group_absent = not process_group_exists(pid)
    raw = bytes(output)
    raw_path = root / 'pty-output.bin'
    raw_path.write_bytes(raw)
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, env=env,
        capture_output=True, text=True, timeout=10).stdout.strip()
    result = dict(started, status='timed-out' if timed_out else 'exited',
        target_exit=exit_code, output_bytes=len(raw), output_sha256=sha256(raw_path),
        output_utf8=raw.decode('utf-8', 'replace')[-4096:], error=output_error,
        process_group_absent=group_absent, workspace_exists=repo.exists(), repo_head=head)
    immutable_json(root / 'finished.json', result)
    print(json.dumps(result, ensure_ascii=True), flush=True)
    if output_error or not group_absent:
        raise RuntimeError('controlling-terminal probe exceeded its output cap or left a process group')


if __name__ == '__main__':
    main()
